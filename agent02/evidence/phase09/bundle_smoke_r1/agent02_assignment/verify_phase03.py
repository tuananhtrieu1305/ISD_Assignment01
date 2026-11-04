"""Saved-output Phase3 audit and one-time release. Never train/evaluate a policy."""

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

from .code.baseline_analysis import analyze_rows, validate_rows
from .code.baseline_runs import summarize, verify_run
from .code.training import digest, q_digest
from .phase02 import save_json
from .phase03 import assert_declaration
from .phase03_reporting import read_rows
from .verify_phase02 import audit as audit_phase2
from .workspace import sha256_file

BASE = Path(__file__).resolve().parent


def saved_run_audit(spec):
    result = verify_run(BASE, spec['run_id'])
    folder = BASE / 'artifacts/runs' / spec['run_id']
    rows = read_rows(folder / 'episode_rewards.csv')
    validate_rows(rows, episodes=5000, steps=20)
    saved = json.loads((folder / 'checkpoint_e005000.json').read_text())
    payload = {key: value for key, value in saved.items() if key != 'sha256'}
    if digest(payload) != saved['sha256'] or digest(saved['rows']) != digest(rows):
        raise ValueError('Checkpoint hash or CSV/rows parity failed')
    q = json.loads((folder / 'q_table.json').read_text())
    if q_digest(q) != q_digest(saved['q']) or q_digest(q) != result['q_sha256']:
        raise ValueError('Q artifact parity failed')
    visits = json.loads((folder / 'visits.json').read_text())
    if visits != saved['visits'] or np.asarray(visits).sum() != 100000:
        raise ValueError('Visitation count mismatch')
    if summarize(rows, 20) != result['summary']:
        raise ValueError('Recomputed summary differs')
    from .code.controlled import LearningConfig
    learning = LearningConfig(**saved['learning'])
    if any(row['epsilon'] != learning.epsilon_at(index) for index, row in enumerate(rows)):
        raise ValueError('Exploration schedule mismatch')
    policy = json.loads((folder / 'policy.json').read_text())
    for item in policy:
        values = np.array(q)[tuple(item['state'])]
        if (item['greedy_action_set'] != np.flatnonzero(np.isclose(values, values.max())).tolist()
                or item['q_no_discount'] != values[0] or item['q_discount'] != values[1]):
            raise ValueError('Q/policy mismatch')
    if saved['completed'] != 5000 or len(list(folder.glob('checkpoint_e*.json'))) != 51:
        raise ValueError('Completed/checkpoint budget mismatch')
    return {'run_id': spec['run_id'], 'track': spec['track'], 'seed': spec['seed'], 'status': 'TRAINED',
            'episodes': 5000, 'market_steps': 100000, 'q_sha256': result['q_sha256'],
            'q_path': (folder/'q_table.json').relative_to(BASE).as_posix(),
            'checkpoint': (folder/'checkpoint_e005000.json').relative_to(BASE).as_posix(),
            'training_source_declaration_sha256': sha256_file(BASE/'evidence/phase03/declaration.json'),
            'final_evaluation_count': 0, 'default_inference_ready': True}


def audit():
    declaration = assert_declaration()
    old_lock, _ = audit_phase2()
    if old_lock != json.loads((BASE/'evidence/phase02/protocol_lock.json').read_text()):
        raise ValueError('Phase2 lock changed')
    registry = [saved_run_audit(spec) for spec in declaration['runs']]
    analyses = json.loads((BASE/'artifacts/metrics/phase03_curve_analysis.json').read_text())
    for spec, saved_analysis in zip(declaration['runs'], analyses, strict=True):
        rows = read_rows(BASE/'artifacts/runs'/spec['run_id']/'episode_rewards.csv')
        calculated = {**analyze_rows(rows), 'run_id': spec['run_id'], 'track': spec['track']}
        if calculated != saved_analysis:
            raise ValueError('Curve analysis differs from saved CSV')
    dev_complete = json.loads((BASE/'artifacts/metrics/phase03_dev/complete.json').read_text())
    if dev_complete['market_steps'] != 8000 or dev_complete['final_evaluation']:
        raise ValueError('Unexpected DEV budget')
    for item in dev_complete['files']:
        path = BASE/item['path']
        if sha256_file(path) != item['sha256']:
            raise ValueError('DEV artifact hash mismatch')
        dev = json.loads(path.read_text())
        trained = next(record for record in registry if record['run_id'] == dev['run_id'])
        if (dev['partition'] != 'development' or dev['episodes'] != 100 or dev['exploration']
                or dev['q_hash_before'] != dev['q_hash_after'] or dev['q_hash_before'] != trained['q_sha256']):
            raise ValueError('DEV frozen-Q contract failed')
        total = sum(row['learner_reward'] for row in dev['rows'])
        if len(dev['rows']) != 100 or total != dev['total_reward'] or total/2000 != dev['mean_reward']:
            raise ValueError('DEV summary mismatch')
    plots = json.loads((BASE/'artifacts/figures/phase03/manifest.json').read_text())
    for item in plots['files'] + plots['source_csvs']:
        if sha256_file(BASE/item['path']) != item['sha256']:
            raise ValueError('Figure/report/source hash mismatch')
    if sha256_file(BASE/'phase03_reporting.py') != plots['generator_sha256']:
        raise ValueError('Presentation generator changed')
    notes = json.loads((BASE/'artifacts/figures/phase03/figure_notes.json').read_text())
    qa = json.loads((BASE/'evidence/phase03/visual_qa.json').read_text())
    if len(notes) != 4 or qa['status'] != 'PASS' or len(qa['images']) != 4:
        raise ValueError('Expected four explained and visually inspected figures')
    for item in qa['images']:
        if sha256_file(BASE/item['path']) != item['sha256']:
            raise ValueError('Visual QA image changed')
        rgb = np.asarray(Image.open(BASE/item['path']).convert('RGB'))
        if not (np.array_equal(rgb[..., 0], rgb[..., 1]) and np.array_equal(rgb[..., 1], rgb[..., 2])):
            raise ValueError('Figure is not grayscale')
    xml = ET.parse(BASE/'evidence/phase03/final_tests.xml').getroot()
    if len(xml.findall('.//testcase')) != 122 or any(xml.findall('.//'+tag) for tag in ('failure', 'error', 'skipped')):
        raise ValueError('Expected 122 tests / zero skip')
    coverage = json.loads((BASE/'evidence/phase03/final_coverage.json').read_text())['totals']
    if coverage['percent_covered'] < 80:
        raise ValueError('Coverage below minimum')
    checks = json.loads((BASE/'evidence/phase03/quality_checks.json').read_text())
    if checks['status'] != 'PASS' or any(value != 0 for value in checks['exit_codes'].values()):
        raise ValueError('Lint/parser/CLI checks failed')
    receipt = {'status': 'PASS', 'phase': 3, 'trained_runs': 2, 'train_episode_rows': 10000,
               'train_market_steps': 200000, 'dev_market_steps': 8000, 'final_evaluation_count': 0,
               'tests_passed': 122, 'skipped': 0, 'coverage_combined_percent': coverage['percent_covered'],
               'coverage_scope': 'reference_training, baseline_runs, baseline_analysis only; excludes CLI/plots/auditor/teacher',
               'figures_explained_and_visually_checked': 4, 'phase2_lock_preserved': True,
               'selected_parent_assets_preserved': 7, 'minimum_disk_reserve_bytes': 5*1024**3,
               'next_phase': 4}
    return registry, receipt


def lock_paths():
    explicit = ['code/reference_training.py', 'code/baseline_runs.py', 'code/baseline_analysis.py',
        'phase03.py', 'phase03_reporting.py', 'verify_phase03.py', 'scripts/run_agent02_phase03.ps1',
        'tests/test_phase03_training.py', 'tests/test_phase03_gate.py', 'tests/test_phase03_reporting.py',
        'tests/coverage_phase03.ini', 'docs/phase03_report.md', 'docs/phase03_operations.md',
        'report/sections/phase03_baseline.md', 'evidence/phase02/protocol_lock.json']
    paths = [BASE/path for path in explicit]
    for relative in ('artifacts/runs/ref/baseline/s0042', 'artifacts/runs/controlled/iid/baseline/s0011',
                     'artifacts/figures/phase03', 'artifacts/metrics/phase03_dev', 'evidence/phase03'):
        paths.extend(path for path in (BASE/relative).rglob('*') if path.is_file()
                     and path.name not in ('.coverage', '.writer.lock', 'experiment_lock.json', 'verification.json'))
    paths += list((BASE/'artifacts/metrics').glob('phase03_*.*'))
    paths += [BASE/'artifacts/manifests/phase03/trained_registry.json']
    return sorted(set(paths))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    registry, receipt = audit()
    if args.seal:
        if shutil.disk_usage(BASE).free < 5*1024**3:
            raise RuntimeError('Disk below reserve')
        save_json(BASE, 'artifacts/manifests/phase03/trained_registry.json', {'phase': 3, 'entries': registry})
    saved_registry = json.loads((BASE/'artifacts/manifests/phase03/trained_registry.json').read_text())
    if saved_registry != {'phase': 3, 'entries': registry}:
        raise ValueError('Trained registry changed')
    lock = {'schema': 'ag02.phase03.release.1', 'declaration_sha256':
            sha256_file(BASE/'evidence/phase03/declaration.json'), 'files': [
            {'path': path.relative_to(BASE).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha256_file(path)}
            for path in lock_paths()]}
    if args.seal:
        save_json(BASE, 'evidence/phase03/experiment_lock.json', lock)
    if json.loads((BASE/'evidence/phase03/experiment_lock.json').read_text()) != lock:
        raise ValueError('Phase3 experiment lock mismatch')
    receipt.update({'locked_files': len(lock['files']), 'experiment_lock_sha256':
                    sha256_file(BASE/'evidence/phase03/experiment_lock.json')})
    if args.seal:
        save_json(BASE, 'evidence/phase03/verification.json', receipt)
    elif json.loads((BASE/'evidence/phase03/verification.json').read_text()) != receipt:
        raise ValueError('Saved verification differs')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
