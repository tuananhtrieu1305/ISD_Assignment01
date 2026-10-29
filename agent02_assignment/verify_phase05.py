"""Read-only final journal/aggregate audit; --seal releases saved Phase5 evidence."""

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

from .code.evaluation.aggregate_v1 import aggregate_evaluations, validate_result
from .code.evaluation.journal_v1 import PREFIX, job_key, read_complete
from .code.training import digest
from .phase01 import preflight
from .phase02 import save_json
from .phase04 import verify_lock
from .phase05 import assert_declaration, build_jobs
from .verify_phase04 import check_csv
from .workspace import sha256_file

BASE = Path(__file__).resolve().parent


def audit():
    declaration = assert_declaration()
    proof = sha256_file(BASE/'evidence/phase05/declaration.json')
    preflight()
    for path in ('evidence/phase01/input_lock.json', 'evidence/phase02/protocol_lock.json',
                 'evidence/phase03/experiment_lock.json', 'evidence/phase04/experiment_lock.json'):
        verify_lock(BASE, path)
    if declaration['jobs'] != build_jobs():
        raise ValueError('Final job matrix/input specification changed')
    protocol = json.loads((BASE/'docs/protocol_v1.json').read_text())
    gold = protocol['future_variants']['gold']
    if sha256_file(BASE.parent/gold['parent_split_path']) != gold['parent_split_sha256']:
        raise ValueError('Gold split metadata changed')
    state = json.loads((BASE/'evidence/phase05/active_controller.json').read_text())
    if state['status'] != 'COMPLETE' or state['pid'] is not None or state['completed'] != 71:
        raise ValueError('Evaluation controller not finished')
    completion = json.loads((BASE/'artifacts/evaluation/phase05/completion.json').read_text())
    if completion['unique_claims'] != 71 or completion['declaration_sha256'] != proof:
        raise ValueError('Completion matrix mismatch')
    folders = [path for path in (BASE/PREFIX).iterdir() if path.is_dir()]
    if len(folders) != 71 or list((BASE/PREFIX).rglob('failure.json')):
        raise ValueError('Unexpected consumed/failure claims; retain and investigate')
    records, episode_rows, steps = [], 0, 0
    for job in declaration['jobs']:
        saved = read_complete(BASE, job, proof)
        folder = BASE/PREFIX/job_key(job)
        claim = json.loads((folder/'claim.json').read_text())
        if saved['evaluation_count'] != 1 or claim['job'] != job:
            raise ValueError('Claim identity/count mismatch')
        result = json.loads((folder/'result.json').read_text())
        if (result['partition'] != 'final' or result['episodes'] != 500 or result['steps'] != 10000
                or result['exploration'] or result['policy_sha256'] != job['policy_sha256']
                or result['role'] != job['role'] or result['scenario_seed'] != job['scenario_seed']
                or result['engine'] != job['engine'] or digest(job['scenario_spec']) != job['scenario_sha256']):
            raise ValueError('Final scope/scenario identity mismatch')
        if job['kind'] == 'q' and not (result['q_hash_before'] == result['q_hash_after'] == job['policy_sha256']):
            raise ValueError('Frozen Q mismatch')
        if [row['episode'] for row in result['rows']] != list(range(1, 501)):
            raise ValueError('Episode IDs incomplete')
        validate_result(result)
        with (folder/'episodes.csv').open() as stream:
            csv_rows = [{key: json.loads(value) for key, value in row.items()} for row in csv.DictReader(stream)]
        if csv_rows != result['rows']:
            raise ValueError('Episode CSV/JSON values differ')
        if result['engine'] == 'matched_tapes_v1':
            visits = np.array([row['state_visits'] for row in result['rows']])
            if (visits.shape != (500, 4) or not (visits.sum(axis=1) == 20).all()
                    or visits.sum(axis=0).tolist() != result['state_visits']):
                raise ValueError('Evaluation visitation mismatch')
        else:
            checkpoint = json.loads((BASE/job['checkpoint']).read_text())
            if result['policy_rng_before'] != checkpoint['rng']['agent']:
                raise ValueError('Native cloned policy RNG differs')
        records.append({'job': job, 'result': result})
        episode_rows += len(result['rows'])
        steps += result['steps']
    aggregate = aggregate_evaluations(records)
    prefix = 'artifacts/metrics/phase05/'
    for name, rows in [('multi_seed.csv', aggregate['multi_seed']), ('paired_comparison.csv', aggregate['paired_rows']),
        ('alpha_comparison.csv', [r for r in aggregate['config_summary'] if r['config_id'] in ('alpha_low', 'baseline', 'alpha_high')]),
        ('exploration_comparison.csv', [r for r in aggregate['config_summary'] if r['config_id'] in
            ('epsilon_low_fixed', 'baseline', 'epsilon_high_fixed')])]:
        check_csv(prefix+name, rows)
    for name, value in [('config_summary.json', aggregate['config_summary']), ('controls_summary.json', aggregate['controls'])]:
        if json.loads((BASE/(prefix+name)).read_text()) != value:
            raise ValueError('Recomputed final aggregate differs')
    with (BASE/(prefix+'q_policy.csv')).open() as stream:
        q_rows = list(csv.DictReader(stream))
    if len(q_rows) != 104 or len({row['run_id'] for row in q_rows}) != 26:
        raise ValueError('Require 26 Q tables / 104 state rows')
    for row in q_rows:
        job = next(j for j in declaration['jobs'] if j.get('run_id') == row['run_id'])
        q = np.array(json.loads((BASE/job['q_path']).read_text()))
        values = q[int(row['demand']), int(row['competitor_previous'])]
        if (float(row['q_no_discount']) != values[0] or float(row['q_discount']) != values[1]
                or json.loads(row['greedy_actions']) != np.flatnonzero(np.isclose(values, values.max())).tolist()):
            raise ValueError('Q/policy table mismatch')
    with (BASE/(prefix+'baseline_reward.csv')).open() as stream:
        baseline = list(csv.DictReader(stream))
    if len(baseline) != 6:
        raise ValueError('Require five baseline seeds and one separate REF row')
    for row in baseline:
        value = aggregate['reference_native'] if row['track'] == 'REF_NATIVE' else next(
            r for r in aggregate['multi_seed'] if r['config_id']=='baseline' and r['train_seed']==int(row['train_seed']))
        if float(row['target_mean']) != value['target_mean'] or float(row['opponent_mean']) != value['opponent_mean']:
            raise ValueError('Baseline table differs')
    plots = json.loads((BASE/'artifacts/figures/phase05/manifest.json').read_text())
    for item in plots['files']+plots['source_results']:
        if sha256_file(BASE/item['path']) != item['sha256']:
            raise ValueError('Figure/table/manuscript/source hash mismatch')
    if sha256_file(BASE/'phase05_reporting.py') != plots['generator_sha256']:
        raise ValueError('Report generator changed')
    qa = json.loads((BASE/'evidence/phase05/visual_qa.json').read_text())
    if qa['status'] != 'PASS' or len(qa['images']) != 4:
        raise ValueError('Four explained figures require visual QA')
    for item in qa['images']:
        if not item['inspected'] or sha256_file(BASE/item['path']) != item['sha256']:
            raise ValueError('Visual QA hash changed')
        pixels = np.asarray(Image.open(BASE/item['path']).convert('RGB'))
        if not (np.array_equal(pixels[..., 0], pixels[..., 1]) and np.array_equal(pixels[..., 1], pixels[..., 2])):
            raise ValueError('Image is not grayscale')
    xml = ET.parse(BASE/'evidence/phase05/final_tests.xml').getroot()
    if len(xml.findall('.//testcase')) != 157 or any(xml.findall('.//'+tag) for tag in ('failure', 'error', 'skipped')):
        raise ValueError('Expected 157 final tests / no skip')
    coverage = json.loads((BASE/'evidence/phase05/final_coverage.json').read_text())['totals']
    quality = json.loads((BASE/'evidence/phase05/quality_checks.json').read_text())
    if coverage['percent_covered'] < 80 or quality['status'] != 'PASS' or any(quality['exit_codes'].values()):
        raise ValueError('Coverage or lint/parser/CLI checks failed')
    receipt = {'status': 'PASS', 'phase': 5, 'evaluated_unique_claims': 71, 'evaluation_count_each': 1,
        'core_claims': 50, 'control_claims': 20, 'native_reference_claims': 1,
        'saved_episode_rows': episode_rows, 'market_steps': steps, 'train_runs_added': 0,
        'frozen_q_tables': 26, 'tables_csv': 6, 'figures_explained_and_viewed': 4,
        'tests_passed': 157, 'skipped': 0, 'coverage_combined_percent': coverage['percent_covered'],
        'coverage_scope': 'final_v1, journal_v1, aggregate_v1 only; excludes CLI/plots/auditor/teacher',
        'parent_locks_phase1_to4_preserved': True, 'selected_parent_assets_preserved': 7, 'next_phase': 6}
    return completion, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    completion, receipt = audit()
    registry = {'phase': 5, 'status': 'EVALUATED', 'declaration_sha256': completion['declaration_sha256'],
                'entries': [{'job_id': item['job']['job_id'], 'key': item['key'], 'complete_path': item['complete_path'],
                             'evaluation_count': 1} for item in completion['entries']]}
    if args.seal:
        save_json(BASE, 'artifacts/manifests/phase05/evaluated_registry.json', registry)
    if json.loads((BASE/'artifacts/manifests/phase05/evaluated_registry.json').read_text()) != registry:
        raise ValueError('Evaluated registry differs')
    explicit = ['phase05.py', 'phase05_reporting.py', 'verify_phase05.py', 'code/evaluation/final_v1.py',
        'code/evaluation/journal_v1.py', 'code/evaluation/aggregate_v1.py', 'tests/test_phase05_evaluation.py',
        'tests/test_phase05_gate.py', 'tests/test_phase05_aggregate.py', 'tests/coverage_phase05.ini',
        'scripts/run_agent02_phase05.ps1', 'docs/phase05_report.md', 'docs/phase05_operations.md',
        'report/sections/phase05_final_evaluation.md', 'evidence/phase04/experiment_lock.json']
    paths = [BASE/path for path in explicit]
    for relative in ('artifacts/evaluation/phase05', 'artifacts/metrics/phase05', 'artifacts/figures/phase05',
                     'artifacts/manifests/phase05', 'evidence/phase05'):
        paths += [path for path in (BASE/relative).rglob('*') if path.is_file() and path.name not in
                  ('.coverage', 'active_controller.json', 'experiment_lock.json', 'verification.json')]
    lock = {'schema': 'ag02.phase05.release.1', 'declaration_sha256': completion['declaration_sha256'],
            'files': [{'path': path.relative_to(BASE).as_posix(), 'bytes': path.stat().st_size,
                       'sha256': sha256_file(path)} for path in sorted(set(paths))]}
    if args.seal:
        save_json(BASE, 'evidence/phase05/experiment_lock.json', lock)
    if json.loads((BASE/'evidence/phase05/experiment_lock.json').read_text()) != lock:
        raise ValueError('Phase5 release lock differs')
    receipt.update({'locked_files': len(lock['files']), 'experiment_lock_sha256': sha256_file(BASE/'evidence/phase05/experiment_lock.json')})
    if args.seal:
        save_json(BASE, 'evidence/phase05/verification.json', receipt)
    elif json.loads((BASE/'evidence/phase05/verification.json').read_text()) != receipt:
        raise ValueError('Verification receipt differs')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
