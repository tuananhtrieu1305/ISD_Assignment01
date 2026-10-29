"""AG02 phase5 final gate: frozen Q, independent matched scenarios and claim-once journal."""

import argparse
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from .code.controlled import MarketConfig
from .code.evaluation.final_v1 import evaluate_tapes, native_reference, policy_hash
from .code.evaluation.journal_v1 import PREFIX, claim_evaluate, job_key
from .code.training import digest, q_digest
from .phase01 import preflight
from .phase02 import disk_guard, save_json
from .phase03 import writer_lock
from .workspace import inside, sha256_file

BASE = Path(__file__).resolve().parent
EVAL_FILES = ['code/controlled.py', 'code/training.py', 'code/evaluation/__init__.py',
    'code/evaluation/final_v1.py', 'code/evaluation/journal_v1.py', 'code/reference_adapter.py',
    'code/agent02_experiment.py', 'phase01.py', 'phase02.py', 'phase03.py', 'workspace.py', 'phase05.py',
    'docs/protocol_v1.json', 'artifacts/manifests/phase04/trained_registry.json',
    'artifacts/manifests/phase03/trained_registry.json', 'tests/test_phase05_evaluation.py',
    'tests/test_phase05_gate.py', 'tests/coverage_phase05.ini', 'scripts/run_agent02_phase05.ps1']


def build_jobs():
    protocol = json.loads((BASE/'docs/protocol_v1.json').read_text())
    registry = json.loads((BASE/'artifacts/manifests/phase04/trained_registry.json').read_text())['entries']
    jobs = []
    def add(*, group, kind, train_seed, config, role, scenario_seed, engine='matched_tapes_v1', record=None):
        scenario = {'market': protocol['market'], 'episodes': 500, 'steps_per_episode': 20,
                    'scenario_seed': scenario_seed, 'engine': engine,
                    'initial_history': [0, 0], 'rng_spec': protocol['rng'] if engine == 'matched_tapes_v1'
                    else 'original env RNG; cloned trained policy RNG'}
        q = json.loads(inside(BASE, record['q_path']).read_text()) if record else None
        fingerprint = policy_hash(q, kind)
        if record and fingerprint != record['q_sha256']:
            raise ValueError('Registry Q differs before final declaration')
        job = {'job_id': f'{group}/{config}/s{train_seed:04d}/role{role}', 'group': group,
               'study_id': 'ag02_core_final_v1' if engine == 'matched_tapes_v1' else 'ag02_ref_native_final_v1',
               'kind': kind, 'config_id': config, 'train_seed': train_seed, 'role': role,
               'scenario_seed': scenario_seed, 'scenario_sha256': digest(scenario), 'scenario_spec': scenario,
               'policy_sha256': fingerprint, 'episodes': 500, 'steps_per_episode': 20, 'engine': engine}
        if record:
            job.update({'run_id': record['run_id'], 'q_path': record['q_path'],
                        'q_file_sha256': sha256_file(BASE/record['q_path'])})
            if engine != 'matched_tapes_v1':
                job['checkpoint'] = record['checkpoint']
                job['checkpoint_sha256'] = sha256_file(BASE/record['checkpoint'])
        jobs.append(job)
    for record in registry:
        for role in (0, 1):
            add(group='core', kind='q', train_seed=record['seed'], config=record['config_id'], role=role,
                scenario_seed=2000000+record['seed'], record=record)
    for kind in ('rule', 'no_discount'):
        for seed in protocol['train_seeds']:
            for role in (0, 1):
                add(group='control', kind=kind, train_seed=seed, config=kind, role=role, scenario_seed=2000000+seed)
    reference = next(row for row in json.loads((BASE/'artifacts/manifests/phase03/trained_registry.json').read_text())['entries']
                     if row['track'] == 'REF')
    add(group='reference_native', kind='q', train_seed=42, config='reference_native', role=0,
        scenario_seed=protocol['evaluation']['reference_native_final_seed'], engine='teacher_native_evaluate_pair', record=reference)
    return jobs


def assert_declaration(base=BASE):
    declaration = json.loads(inside(base, 'evidence/phase05/declaration.json').read_text())
    for item in declaration['files']:
        if sha256_file(inside(base, item['path'])) != item['sha256']:
            raise ValueError('Phase5 locked source/input hash mismatch: '+item['path'])
    return declaration


def declare():
    runtime = preflight()['runtime']
    jobs = build_jobs()
    if len(jobs) != 71 or len({job_key(job) for job in jobs}) != 71:
        raise ValueError('Expected 71 unique preregistered evaluation claims')
    xml = ET.parse(BASE/'evidence/phase05/pretest_tests.xml').getroot()
    if len(xml.findall('.//testcase')) < 152 or any(xml.findall('.//'+tag) for tag in ('failure', 'error', 'skipped')):
        raise ValueError('Pretest tests incomplete or failed')
    coverage = json.loads((BASE/'evidence/phase05/pretest_coverage.json').read_text())
    if coverage['totals']['percent_covered'] < 80:
        raise ValueError('Evaluator/journal coverage below minimum')
    paths = EVAL_FILES + ['evidence/phase05/pretest_tests.xml', 'evidence/phase05/pretest_coverage.json',
                         'evidence/phase04/experiment_lock.json']
    paths += [job['q_path'] for job in jobs if 'q_path' in job]
    paths += [job['checkpoint'] for job in jobs if 'checkpoint' in job]
    old_expected = {}
    for relative in ('evidence/phase01/input_lock.json', 'evidence/phase02/protocol_lock.json',
                     'evidence/phase03/experiment_lock.json', 'evidence/phase04/experiment_lock.json'):
        old_expected.update({item['path']: item['sha256'] for item in json.loads((BASE/relative).read_text())['files']})
    for path in paths:
        if path in old_expected and sha256_file(BASE/path) != old_expected[path]:
            raise ValueError('Protected evaluation input changed: '+path)
    receipt = {'schema': 'ag02.phase05.final_declaration.1', 'jobs': jobs, 'expected_unique_claims': 71,
               'expected_market_steps': 710000, 'episodes_per_claim': 500, 'role_swap_core_and_controls': True,
               'registry25_sha256': sha256_file(BASE/'artifacts/manifests/phase04/trained_registry.json'),
               'prior_release_sha256': sha256_file(BASE/'evidence/phase04/experiment_lock.json'),
               'runtime': runtime, 'free_bytes_before': disk_guard(BASE), 'final_authorized_by_user_phase5': True,
               'aggregation': 'Average the two roles per trained seed, then mean/sample std ddof1 across five seeds; paired seed deltas',
               'controls_interpretation': 'Five scenario panels, not five trained control agents',
               'native_reference_scope': 'One faithful native role0 run, excluded from CONTROLLED n5 aggregates',
               'recovery': 'Keep failed/partial consumed claims; never replay; reuse valid completed claims',
               'files': [{'path': path, 'sha256': sha256_file(BASE/path)} for path in sorted(set(paths))]}
    save_json(BASE, 'evidence/phase05/declaration.json', receipt)
    return {'status': 'DECLARED', 'unique_claims': 71, 'market_steps': 710000,
            'sha256': sha256_file(BASE/'evidence/phase05/declaration.json')}


def forward(job):
    q = None
    if 'q_path' in job:
        path = inside(BASE, job['q_path'])
        if sha256_file(path) != job['q_file_sha256']:
            raise ValueError('Q input file changed')
        q = json.loads(path.read_text())
        if q_digest(q) != job['policy_sha256']:
            raise ValueError('Q payload changed')
    if job['engine'] == 'teacher_native_evaluate_pair':
        path = inside(BASE, job['checkpoint'])
        if sha256_file(path) != job['checkpoint_sha256']:
            raise ValueError('Native RNG checkpoint changed')
        state = json.loads(path.read_text())
        result = native_reference(q, state['rng']['agent'], episodes=500, scenario_seed=job['scenario_seed'],
                                  guard=lambda: disk_guard(BASE))
    else:
        result = evaluate_tapes(q, MarketConfig(**job['scenario_spec']['market']), episodes=500,
            scenario_seed=job['scenario_seed'], role=job['role'], kind=job['kind'], guard=lambda: disk_guard(BASE))
    if 'q_path' in job and sha256_file(BASE/job['q_path']) != job['q_file_sha256']:
        raise RuntimeError('Source Q file changed during evaluation')
    return {'partition': 'final', 'job_id': job['job_id'], **result}


def evaluate():
    declaration = assert_declaration()
    proof = sha256_file(BASE/'evidence/phase05/declaration.json')
    state = {'status': 'RUNNING', 'pid': os.getpid(), 'completed': 0, 'current_job': None}
    def update():
        path = BASE/'evidence/phase05/active_controller.json'
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(state, indent=2)+'\n')
        temporary.replace(path)
    results = []
    try:
        for job in declaration['jobs']:
            state['current_job'] = job['job_id']
            update()
            disk_guard(BASE)
            result = claim_evaluate(BASE, job, proof, lambda job=job: forward(job))
            results.append({'job': job, 'key': result['key'], 'complete_path': PREFIX+'/'+result['key']+'/complete.json'})
            state['completed'] = len(results)
            print(f'{len(results)}/71 EVALUATED {job["job_id"]}', flush=True)
        save_json(BASE, 'artifacts/evaluation/phase05/completion.json', {'status': 'EVALUATED',
            'declaration_sha256': proof, 'unique_claims': len(results), 'entries': results})
        state.update({'status': 'COMPLETE', 'current_job': None})
    except BaseException as error:
        state.update({'status': 'FAILED_RETAIN_CLAIMS', 'error': type(error).__name__+': '+str(error)})
        raise
    finally:
        state['pid'] = None
        update()
    return {'status': 'COMPLETE', 'evaluated_claims': len(results)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', choices=('status', 'declare', 'evaluate'))
    args = parser.parse_args()
    if args.task == 'status':
        path = BASE/'evidence/phase05/active_controller.json'
        result = {'phase': 5, 'declaration_exists': (BASE/'evidence/phase05/declaration.json').exists(),
                  'controller': json.loads(path.read_text()) if path.exists() else None}
    else:
        with writer_lock(BASE):
            result = declare() if args.task == 'declare' else evaluate()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
