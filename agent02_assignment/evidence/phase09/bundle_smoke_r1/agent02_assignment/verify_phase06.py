"""Read-only scientific audit from saved outputs; --seal writes a new Phase6 release."""

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

from .code.evaluation.aggregate_v1 import validate_result
from .code.evaluation.phase06_journal import PREFIX, key_for, read_claim
from .code.gold_regime import estimate_regimes
from .code.phase06_analysis import aggregate
from .code.training import digest, q_digest
from .phase01 import preflight
from .phase02 import save_json
from .phase03 import writer_lock
from .phase06 import assert_proof
from .workspace import sha256_file

BASE = Path(__file__).resolve().parent


def csv_values(path):
    with path.open() as stream:
        return [{k: json.loads(v) if v[:1] in '[{' else v for k, v in row.items()} for row in csv.DictReader(stream)]


def check_table(path, expected):
    with path.open() as stream:
        actual = list(csv.DictReader(stream))
    if len(actual) != len(expected):
        raise ValueError('CSV row count differs: '+str(path))
    for saved, row in zip(actual, expected, strict=True):
        if set(saved) != set(row):
            raise ValueError('CSV columns differ')
        for key, value in row.items():
            if isinstance(value, (float, int)) and not isinstance(value, bool):
                matches = float(saved[key]) == value
            elif isinstance(value, (list, dict)):
                matches = json.loads(saved[key]) == value
            else:
                matches = saved[key] == str(value)
            if not matches:
                raise ValueError(f'CSV value differs:{path.name}/{key}')


def audit():
    parent = preflight()
    train = assert_proof('evidence/phase06/train_declaration.json')
    evaluation = assert_proof('evidence/phase06/eval_declaration.json')
    expected = {}
    for relative in ('phase01/input_lock.json', 'phase02/protocol_lock.json', 'phase03/experiment_lock.json',
                     'phase04/experiment_lock.json', 'phase05/experiment_lock.json'):
        for item in json.loads((BASE/'evidence'/relative).read_text())['files']:
            if item['path'] in expected and expected[item['path']] != item['sha256']:
                raise ValueError('Inconsistent old protected hash')
            expected[item['path']] = item['sha256']
    for path, fingerprint in expected.items():
        if sha256_file(BASE/path) != fingerprint:
            raise ValueError('Old protected artifact changed:'+path)
    gold = json.loads((BASE/'data/derived/gold_regime_kernel_v1.json').read_text())
    source = gold['source']
    for path, fingerprint in [(source['source_path'], source['source_sha256']),
                              (source['parent_split_path'], source['parent_split_sha256']),
                              (gold['parent_train_ids']['path'], gold['parent_train_ids']['sha256'])]:
        if sha256_file(BASE.parent/path) != fingerprint:
            raise ValueError('Gold provenance changed')
    with (BASE/'data/derived/gold_train_prefix_v1.csv').open() as stream:
        prefix = [(r['month'], float(r['gold_usd_per_troy_ounce'])) for r in csv.DictReader(stream)]
    recalculated = estimate_regimes(prefix)
    if any(recalculated[k] != gold[k] for k in recalculated) or gold['last_month']!='2006-08' or gold['valid_prices']!=560:
        raise ValueError('Gold TRAIN kernel differs')
    controller = json.loads((BASE/'evidence/phase06/active_controller.json').read_text())
    if controller['status'] != 'COMPLETE' or controller['pid'] is not None or controller['stage'] != 'evaluate':
        raise ValueError('Phase6 controller unfinished')
    completion = json.loads((BASE/'artifacts/manifests/phase06/train_completion.json').read_text())
    if len(completion['entries']) != 15 or completion['declaration_sha256'] != sha256_file(BASE/'evidence/phase06/train_declaration.json'):
        raise ValueError('Train completion mismatch')
    train_rows, learner_steps, sources = 0, 0, []
    for spec in train['matrix']:
        folder = BASE/'artifacts/runs'/spec['run_id']
        result = json.loads((folder/'complete.json').read_text())
        for item in result['files']:
            if sha256_file(BASE/item['path']) != item['sha256'] or (BASE/item['path']).stat().st_size != item['bytes']:
                raise ValueError('Train artifact changed')
        saved = json.loads((folder/'checkpoint_e005000.json').read_text())
        body = {k: v for k, v in saved.items() if k!='sha256'}
        if digest(body) != saved['sha256'] or saved['completed']!=5000 or len(saved['rows'])!=5000:
            raise ValueError('Train checkpoint count/hash differs')
        if len(list(folder.glob('checkpoint_e*.json')))!=51:
            raise ValueError('Require51 episode checkpoints')
        q = json.loads((folder/'q_table.json').read_text())
        if q != saved['q'] or np.asarray(json.loads((folder/'checkpoint_e000000.json').read_text())['q']).any():
            raise ValueError('Q source/init differs')
        if spec['learners']==2:
            for table in q:
                q_digest(table)
            if np.asarray(saved['visits']).sum(axis=(1, 2, 3)).tolist()!=[100000, 100000]:
                raise ValueError('Pair visits differ')
            if saved['rng']['agents'][0] == saved['rng']['agents'][1]:
                raise ValueError('Pair policy RNGs are identical')
        elif q_digest(q)!=result['q_sha256'] or np.asarray(saved['visits']).sum()!=100000:
            raise ValueError('Variant Q/visits differ')
        check_table(folder/'episode_rewards.csv', saved['rows'])
        if any(r['episode']!=i+1 or np.asarray(r['action_counts']).sum(axis=1).tolist()!=[20, 20]
               for i, r in enumerate(saved['rows'])):
            raise ValueError('Training episode/action counts differ')
        train_rows += len(saved['rows'])
        learner_steps += spec['learners']*100000
        sources.append({'run_id': spec['run_id'], 'q_path': (folder/'q_table.json').relative_to(BASE).as_posix(),
                        'q_file_sha256': sha256_file(folder/'q_table.json'), 'learners': spec['learners'],
                        'status': 'TRAINED_EVALUATED'})
    final = json.loads((BASE/'artifacts/evaluation/phase06/completion.json').read_text())
    proof = sha256_file(BASE/'evidence/phase06/eval_declaration.json')
    if final['declaration_sha256']!=proof or len(final['entries'])!=160 or len(evaluation['jobs'])!=160:
        raise ValueError('Final completion mismatch')
    records, rows = [], 0
    if {e['key'] for e in final['entries']} != {key_for(j) for j in evaluation['jobs']}:
        raise ValueError('Job keys differ')
    if len(list((BASE/PREFIX).iterdir()))!=160 or list((BASE/PREFIX).rglob('failure.json')):
        raise ValueError('Unexpected/missing/failed final claims')
    for entry, job in zip(final['entries'], evaluation['jobs'], strict=True):
        if entry['job']!=job or entry['key']!=key_for(job):
            raise ValueError('Job identity differs')
        read_claim(BASE, job, proof)
        folder = BASE/PREFIX/entry['key']
        claim = json.loads((folder/'claim.json').read_text())
        result = json.loads((folder/'result.json').read_text())
        if claim['job']!=job or claim['proof_sha256']!=proof:
            raise ValueError('Claim differs')
        validate_result(result)
        if (result['episodes']!=500 or result['steps']!=10000 or result['exploration'] is not False or
            result['policy_sha256']!=job['policy_sha256'] or result['role']!=job['role'] or
            result['scenario_seed']!=job['scenario_spec']['scenario_seed'] or
            digest(job['scenario_spec'])!=job['scenario_sha256'] or result['partition']!='phase06_frozen_final'):
            raise ValueError('Final policy/scenario/budget differs')
        if (result['q_hash_before']!=result['q_hash_after'] or result['job_id']!=job['job_id'] or
                (job['kind']=='q' and result['q_hash_before']!=job['policy_sha256'])):
            raise ValueError('Q changed')
        with (folder/'episodes.csv').open() as stream:
            raw = [{k: json.loads(v) for k, v in row.items()} for row in csv.DictReader(stream)]
        if raw!=result['rows'] or [r['episode'] for r in raw]!=list(range(1, 501)):
            raise ValueError('Raw evaluation rows differ')
        visits = np.array([r['state_visits'] for r in raw])
        if visits.shape!=(500, 4) or not (visits.sum(axis=1)==20).all() or visits.sum(axis=0).tolist()!=result['state_visits']:
            raise ValueError('Final visits differ')
        rows += len(raw)
        records.append({'job': job, 'result': result})
    aggregated = aggregate(records)
    for name, values in aggregated.items():
        check_table(BASE/'artifacts/metrics/phase06'/(name+'.csv'), values)
    from .phase06_reporting import train_diagnostics
    training, curves, drift = train_diagnostics(train['matrix'])
    for name, values in [('train_summary', training), ('pair_train_curves', curves), ('policy_drift', drift)]:
        check_table(BASE/'artifacts/metrics/phase06'/(name+'.csv'), values)
    manifest = json.loads((BASE/'artifacts/figures/phase06/manifest.json').read_text())
    for item in manifest['files']:
        if sha256_file(BASE/item['path'])!=item['sha256']:
            raise ValueError('Figure/notes/metric/manuscript differs')
    if sha256_file(BASE/'phase06_reporting.py')!=manifest['generator_sha256']:
        raise ValueError('Generator differs')
    qa = json.loads((BASE/'evidence/phase06/visual_qa.json').read_text())
    if qa['status']!='PASS' or len(qa['images'])!=4:
        raise ValueError('Four images require actual visual QA')
    for image in qa['images']:
        if not image['inspected'] or sha256_file(BASE/image['path'])!=image['sha256']:
            raise ValueError('Visual QA differs')
        pixels = np.array(Image.open(BASE/image['path']).convert('RGB'))
        if not np.array_equal(pixels[..., 0], pixels[..., 1]) or not np.array_equal(pixels[..., 1], pixels[..., 2]):
            raise ValueError('Figure not grayscale')
    tests = ET.parse(BASE/'evidence/phase06/final_tests.xml').getroot()
    count = len(tests.findall('.//testcase'))
    coverage = json.loads((BASE/'evidence/phase06/final_coverage.json').read_text())['totals']
    quality = json.loads((BASE/'evidence/phase06/quality_checks.json').read_text())
    if count<186 or any(tests.findall('.//'+k) for k in ('failure', 'error', 'skipped')) or coverage['percent_covered']<80:
        raise ValueError('Tests/coverage failed')
    if quality['status']!='PASS' or any(quality['exit_codes'].values()):
        raise ValueError('Lint/parser/CLI failed')
    receipt = {'status': 'PASS', 'phase': 6, 'train_market_runs': 15, 'learner_instances': 20,
        'train_episode_rows': train_rows, 'train_market_steps': train_rows*20, 'train_learner_updates': learner_steps,
        'evaluated_unique_claims': 160, 'evaluation_count_each': 1, 'saved_final_episode_rows': rows,
        'final_market_steps': rows*20, 'gold_train_months': 560, 'prior_protected_files_preserved': len(expected),
        'selected_parent_assets_preserved': len(parent['preservation']),
        'tables_csv': 9, 'figures_explained_and_viewed': 4, 'tests_passed': count, 'skipped': 0,
        'coverage_combined_percent': coverage['percent_covered'],
        'coverage_scope': 'gold_regime,pair_training,phase06_journal,phase06_analysis only; excludes frozen evaluator/CLI/plots/auditor',
        'next_phase': 7}
    return sources, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    with writer_lock(BASE):
        sources, receipt = audit()
        registry = {'phase': 6, 'status': 'TRAINED_EVALUATED', 'entries': sources,
                    'evaluation_completion': 'artifacts/evaluation/phase06/completion.json'}
        if args.seal:
            save_json(BASE, 'artifacts/manifests/phase06/trained_evaluated_registry.json', registry)
        elif json.loads((BASE/'artifacts/manifests/phase06/trained_evaluated_registry.json').read_text())!=registry:
            raise ValueError('Registry changed')
        paths = [BASE/p for p in ['phase06.py', 'phase06_reporting.py', 'verify_phase06.py', 'code/gold_regime.py',
            'code/pair_training.py', 'code/evaluation/phase06_journal.py', 'code/phase06_analysis.py',
            'tests/test_phase06.py', 'tests/test_phase06_analysis.py', 'tests/coverage_phase06.ini',
            'tests/coverage_phase06_final.ini', 'scripts/run_agent02_phase06.ps1', 'docs/phase06_design.md',
            'docs/phase06_report.md', 'docs/phase06_operations.md', 'report/sections/phase06_robustness.md',
            'evidence/phase05/experiment_lock.json', 'data/derived/gold_regime_kernel_v1.json', 'data/derived/gold_train_prefix_v1.csv']]
        for folder in ['artifacts/manifests/phase06', 'artifacts/evaluation/phase06', 'artifacts/metrics/phase06',
                       'artifacts/figures/phase06', 'evidence/phase06']:
            paths += [p for p in (BASE/folder).rglob('*') if p.is_file() and p.name not in
                ('.coverage', '.coverage_final', 'active_controller.json', 'experiment_lock.json', 'verification.json')]
        for spec in json.loads((BASE/'evidence/phase06/train_declaration.json').read_text())['matrix']:
            paths += [p for p in (BASE/'artifacts/runs'/spec['run_id']).rglob('*') if p.is_file()]
        lock = {'schema': 'ag02.phase06.release.1', 'files': [{'path': p.relative_to(BASE).as_posix(),
            'bytes': p.stat().st_size, 'sha256': sha256_file(p)} for p in sorted(set(paths))]}
        if args.seal:
            save_json(BASE, 'evidence/phase06/experiment_lock.json', lock)
        elif json.loads((BASE/'evidence/phase06/experiment_lock.json').read_text())!=lock:
            raise ValueError('Phase6 release differs')
        receipt.update({'locked_files': len(lock['files']),
                        'experiment_lock_sha256': sha256_file(BASE/'evidence/phase06/experiment_lock.json')})
        if args.seal:
            save_json(BASE, 'evidence/phase06/verification.json', receipt)
        elif json.loads((BASE/'evidence/phase06/verification.json').read_text())!=receipt:
            raise ValueError('Verification changed')
        print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
