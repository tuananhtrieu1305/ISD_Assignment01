"""Phase4 saved-output audit and one-time seal; no train, policy forward or eval."""

import argparse
import csv
import io
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

from .code.sweep_runs import BASELINE_ID, select_specs
from .code.sweep_summary import summarize_matrix
from .code.training import digest
from .phase01 import preflight
from .phase02 import save_json
from .phase03_reporting import read_rows
from .phase04 import assert_declaration, verify_lock
from .verify_phase03 import saved_run_audit
from .workspace import sha256_file

BASE = Path(__file__).resolve().parent


def check_csv(relative, rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows({key: json.dumps(value) if isinstance(value, (dict, list)) else value
                     for key, value in row.items()} for row in rows)
    if (BASE/relative).read_text() != stream.getvalue():
        raise ValueError('Derived CSV differs from recomputed rows: '+relative)


def audit():
    declaration = assert_declaration()
    preflight()
    for relative in ('evidence/phase01/input_lock.json', 'evidence/phase02/protocol_lock.json',
                     'evidence/phase03/experiment_lock.json'):
        verify_lock(BASE, relative)
    controller = json.loads((BASE/'evidence/phase04/active_controller.json').read_text())
    if controller['status'] != 'COMPLETE' or controller['pid'] is not None or controller['completed_cells'] != 25:
        raise ValueError('Train controller is not finished; do not release concurrently')
    protocol = json.loads((BASE/'docs/protocol_v1.json').read_text())
    gold = protocol['future_variants']['gold']
    if sha256_file(BASE.parent/gold['parent_split_path']) != gold['parent_split_sha256']:
        raise ValueError('Gold parent TRAIN-boundary metadata changed')
    specs = select_specs(protocol)
    if specs != declaration['matrix'] or declaration['final_evaluation_authorized']:
        raise ValueError('Declared matrix/scope changed')
    baseline_complete = BASE/'artifacts/runs'/BASELINE_ID/'complete.json'
    if sha256_file(baseline_complete) != declaration['baseline_completion_sha256']:
        raise ValueError('Phase3 baseline completion changed')
    completion = json.loads((BASE/'artifacts/manifests/phase04/train_completion.json').read_text())
    indexed = {item['run_id']: item for item in completion['entries']}
    if len(indexed) != 25 or completion['final_evaluation_count'] != 0:
        raise ValueError('Incomplete train index or final gate opened')
    records, registry = [], []
    for spec in specs:
        entry = saved_run_audit(spec)
        folder = BASE/'artifacts/runs'/spec['run_id']
        manifest = json.loads((folder/'manifest.json').read_text())
        result = json.loads((folder/'complete.json').read_text())
        source = declaration['baseline_declaration_sha256'] if spec['run_id'] == BASELINE_ID else sha256_file(
                 BASE/'evidence/phase04/declaration.json')
        registration = {'spec': spec, 'market': protocol['market'],
                        'learning': protocol['controlled_configs'][spec['config_id']], 'declaration_sha256': source}
        if digest(registration) != result['registration_sha256'] or manifest['declaration_sha256'] != source:
            raise ValueError('Config/source registration mismatch')
        if indexed[spec['run_id']]['q_sha256'] != result['q_sha256']:
            raise ValueError('Completion index Q mismatch')
        rows = read_rows(folder/'episode_rewards.csv')
        records.append({'spec': spec, 'rows': rows, 'result': result})
        registry.append({**entry, 'config_id': spec['config_id'], 'status': 'TRAINED_AWAITING_FINAL',
            'training_source_declaration_sha256': source, 'reused_from_phase3': spec['run_id'] == BASELINE_ID})
    calculated = summarize_matrix(records)
    metric = 'artifacts/metrics/phase04/'
    for name, key in [('seed_train_summary.csv', 'seed_summary'), ('config_train_summary.csv', 'config_summary'),
                      ('curves_mean_std.csv', 'curve_rows')]:
        check_csv(metric+name, calculated[key])
    if json.loads((BASE/(metric+'paired_train_deltas.json')).read_text()) != calculated['paired']:
        raise ValueError('Paired train summary differs')
    from .code.controlled import LearningConfig
    schedules = []
    for config in ('baseline', 'epsilon_low_fixed', 'epsilon_high_fixed'):
        learning = LearningConfig(**protocol['controlled_configs'][config])
        schedules.extend({'config_id': config, 'episode': episode+1, 'epsilon': learning.epsilon_at(episode)}
                         for episode in range(5000))
    check_csv(metric+'epsilon_schedules.csv', schedules)
    plots = json.loads((BASE/'artifacts/figures/phase04/manifest.json').read_text())
    for item in plots['files']+plots['source_index']:
        if sha256_file(BASE/item['path']) != item['sha256']:
            raise ValueError('Presentation/source hash mismatch')
    if sha256_file(BASE/'phase04_reporting.py') != plots['generator_sha256']:
        raise ValueError('Presentation generator changed')
    notes = json.loads((BASE/'artifacts/figures/phase04/figure_notes.json').read_text())
    qa = json.loads((BASE/'evidence/phase04/visual_qa.json').read_text())
    if len(notes) != 4 or qa['status'] != 'PASS' or len(qa['images']) != 4:
        raise ValueError('Four explained and inspected figures required')
    for item in qa['images']:
        if sha256_file(BASE/item['path']) != item['sha256'] or not item['inspected']:
            raise ValueError('Visual QA hash changed')
        pixels = np.asarray(Image.open(BASE/item['path']).convert('RGB'))
        if not (np.array_equal(pixels[..., 0], pixels[..., 1]) and np.array_equal(pixels[..., 1], pixels[..., 2])):
            raise ValueError('Figure is not grayscale')
    tests = ET.parse(BASE/'evidence/phase04/final_tests.xml').getroot()
    if len(tests.findall('.//testcase')) != 137 or any(tests.findall('.//'+tag) for tag in ('failure', 'error', 'skipped')):
        raise ValueError('Require 137 final tests PASS / zero skip')
    coverage = json.loads((BASE/'evidence/phase04/final_coverage.json').read_text())['totals']
    if coverage['percent_covered'] < 80:
        raise ValueError('Coverage below acceptance')
    quality = json.loads((BASE/'evidence/phase04/quality_checks.json').read_text())
    if quality['status'] != 'PASS' or any(quality['exit_codes'].values()):
        raise ValueError('Lint/parser/CLI checks failed')
    receipt = {'status': 'PASS', 'phase': 4, 'matrix_cells': 25, 'new_trained_runs': 24,
        'reused_baseline_runs': 1, 'total_scientific_runs_including_REF': 26,
        'core_train_episode_rows': 125000, 'core_train_market_steps': 2500000,
        'new_train_market_steps': 2400000, 'derived_curve_rows': len(calculated['curve_rows']),
        'final_evaluation_count': 0, 'development_forward_in_phase4': 0, 'tests_passed': 137, 'skipped': 0,
        'coverage_combined_percent': coverage['percent_covered'],
        'coverage_scope': 'sweep_runs, sweep_analysis, sweep_summary only; not teacher, CLI, plots or auditor',
        'figures_explained_and_visually_checked': 4, 'phase1_2_3_locks_preserved': True,
        'selected_parent_assets_preserved': 7, 'next_phase': 5}
    return registry, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    registry, receipt = audit()
    relative_registry = 'artifacts/manifests/phase04/trained_registry.json'
    expected_registry = {'phase': 4, 'entries': registry, 'final_evaluation_count': 0}
    if args.seal:
        if shutil.disk_usage(BASE).free < 5*1024**3:
            raise RuntimeError('Disk reserve below 5GiB')
        save_json(BASE, relative_registry, expected_registry)
    if json.loads((BASE/relative_registry).read_text()) != expected_registry:
        raise ValueError('Registry changed')
    paths = [BASE/path for path in ('phase04.py', 'phase04_reporting.py', 'verify_phase04.py',
        'code/sweep_runs.py', 'code/sweep_analysis.py', 'code/sweep_summary.py', 'tests/test_phase04.py',
        'tests/test_phase04_summary.py', 'tests/coverage_phase04.ini', 'scripts/run_agent02_phase04.ps1',
        'docs/phase04_report.md', 'docs/phase04_operations.md', 'report/sections/phase04_sweeps.md',
        'evidence/phase03/experiment_lock.json', relative_registry)]
    for spec in assert_declaration()['matrix']:
        paths.extend(path for path in (BASE/'artifacts/runs'/spec['run_id']).rglob('*') if path.is_file())
    for folder in ('artifacts/metrics/phase04', 'artifacts/figures/phase04', 'evidence/phase04',
                   'artifacts/manifests/phase04'):
        paths.extend(path for path in (BASE/folder).rglob('*') if path.is_file() and path.name not in
                     ('.coverage', 'active_controller.json', 'experiment_lock.json', 'verification.json'))
    lock = {'schema': 'ag02.phase04.release.1', 'declaration_sha256': sha256_file(BASE/'evidence/phase04/declaration.json'),
            'files': [{'path': path.relative_to(BASE).as_posix(), 'sha256': sha256_file(path),
                       'bytes': path.stat().st_size} for path in sorted(set(paths))]}
    if args.seal:
        save_json(BASE, 'evidence/phase04/experiment_lock.json', lock)
    if json.loads((BASE/'evidence/phase04/experiment_lock.json').read_text()) != lock:
        raise ValueError('Phase4 release hash mismatch')
    receipt.update({'locked_files': len(lock['files']), 'experiment_lock_sha256':
                    sha256_file(BASE/'evidence/phase04/experiment_lock.json')})
    if args.seal:
        save_json(BASE, 'evidence/phase04/verification.json', receipt)
    elif json.loads((BASE/'evidence/phase04/verification.json').read_text()) != receipt:
        raise ValueError('Verification receipt changed')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
