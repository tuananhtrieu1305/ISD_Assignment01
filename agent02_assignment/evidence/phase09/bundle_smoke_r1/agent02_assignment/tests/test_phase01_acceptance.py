"""Integration contracts for Phase 1, not tests of the teacher's RL model."""

import json
import subprocess
import sys
from pathlib import Path

from agent02_assignment.workspace import sha256_file

BASE = Path(__file__).resolve().parents[1]


def test_six_portable_source_copies_match_original_hashes():
    manifest = json.loads((BASE / 'sources/manifest.json').read_text())
    assert len(manifest) == 6
    assert all(sha256_file(BASE / 'sources/provided' / item['name']) == item['sha256']
               for item in manifest)


def test_reference_is_exact_bytes_and_was_only_compiled():
    source = BASE / 'sources/provided/agent02_code.tex'
    reference = BASE / 'code/agent02_experiment.py'
    assert reference.read_bytes() == source.read_bytes()
    receipt = json.loads((BASE / 'evidence/phase01/reference_inspection.json').read_text())
    assert receipt['syntax_valid'] is True
    assert receipt['execution_performed'] is False
    assert len(receipt['classes']) == 4 and len(receipt['functions']) == 12
    assert receipt['config_defaults']['output_dir'] == 'agent02_results'


def test_runtime_notebook_used_pinned_interpreter_and_no_training():
    notebook = json.loads((BASE / 'evidence/phase01/runtime_probe.ipynb').read_text())
    cells = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
    assert len(cells) == 2
    assert [cell['execution_count'] for cell in cells] == [1, 2]
    assert all(cell['outputs'] for cell in cells)
    assert all(output['output_type'] != 'error' for cell in cells for output in cell['outputs'])
    combined = json.dumps(cells)
    assert 'Array sum: 6' in combined and 'Training steps: 0' in combined
    assert '.venv-torch/bin/python' in combined


def test_old_selected_inputs_preserved_before_and_after():
    receipt = json.loads((BASE / 'evidence/phase01/preparation.json').read_text())
    assert receipt['preservation_before'] == receipt['preservation_after']
    assert len(receipt['preservation_after']) == 7
    assert all(item['unchanged'] for item in receipt['preservation_after'])


def test_preflight_cli_works_from_repo_without_running_reference():
    result = subprocess.run([sys.executable, '-B', '-m', 'agent02_assignment.phase01', 'preflight'],
                            cwd=BASE.parent, capture_output=True, text=True, check=True, timeout=30)
    receipt = json.loads(result.stdout)
    assert receipt['status'] == 'PASS' and receipt['read_only'] is True
    assert receipt['training_started'] is False
    assert receipt['source_hashes_verified'] == 6


def test_cli_has_no_training_action_in_phase_one():
    result = subprocess.run([sys.executable, '-B', '-m', 'agent02_assignment.phase01', 'train'],
                            cwd=BASE.parent, capture_output=True, text=True, timeout=15, check=False)
    assert result.returncode == 2
    assert 'invalid choice' in result.stderr


def test_prepare_refuses_to_rerun_finished_probe():
    result = subprocess.run([sys.executable, '-B', '-m', 'agent02_assignment.phase01', 'prepare'],
                            cwd=BASE.parent, capture_output=True, text=True, timeout=15, check=False)
    assert result.returncode != 0
    assert 'already prepared' in result.stderr
