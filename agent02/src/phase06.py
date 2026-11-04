"""AG02 phase6: preregistered pair learning and two demand variants; separate final gate."""

import argparse
import json
import os
import xml.etree.ElementTree as ET
from dataclasses import asdict, replace
from pathlib import Path

import openpyxl

from .code.baseline_runs import execute_run, verify_run
from .code.controlled import LearningConfig, MarketConfig
from .code.evaluation.final_v1 import evaluate_tapes, policy_hash
from .code.evaluation.phase06_journal import PREFIX, claim_once, key_for
from .code.gold_regime import estimate_regimes, prefix_records
from .code.pair_training import execute_pair
from .code.training import digest, q_digest
from .phase01 import preflight
from .phase02 import disk_guard, save_csv, save_json
from .phase03 import TRAIN_FILES, writer_lock
from .phase04 import verify_lock
from .workspace import inside, sha256_file

BASE = Path(__file__).resolve().parent
NEW_FILES = ['phase06.py', 'code/gold_regime.py', 'code/pair_training.py',
    'code/evaluation/phase06_journal.py', 'tests/test_phase06.py', 'tests/coverage_phase06.ini',
    'scripts/run_agent02_phase06.ps1', 'docs/phase06_design.md']
FILES = sorted(set(TRAIN_FILES+NEW_FILES+['code/evaluation/final_v1.py']))


def protocol():
    return json.loads((BASE/'docs/protocol_v1.json').read_text())


def specs():
    result = [r for r in protocol()['training_runs'] if r['phase'] == 6]
    if len(result) != 15 or sum(r['learners'] for r in result) != 20:
        raise ValueError('Require 15 market runs / 20 learners')
    return result


def markets():
    data = protocol()
    baseline = MarketConfig(**data['market'])
    return {'iid': baseline, 'persistent': replace(baseline, kernel=data['future_variants']['persistent']['kernel']),
        'gold': replace(baseline, kernel=json.loads((BASE/'data/derived/gold_regime_kernel_v1.json').read_text())['kernel'])}


def prepare():
    preflight()
    gold = protocol()['future_variants']['gold']
    source, split = BASE.parent/gold['source_path'], BASE.parent/gold['parent_split_path']
    if sha256_file(source) != gold['source_sha256'] or sha256_file(split) != gold['parent_split_sha256']:
        raise ValueError('Gold source/split changed')
    train = next(r for r in json.loads(split.read_text())['partitions'] if r['name']=='train')
    if train['target_end'][:7] != gold['last_allowed_month']:
        raise ValueError('TRAIN cutoff differs')
    ids = BASE.parent/train['ids']['path']
    if sha256_file(ids) != train['ids']['sha256']:
        raise ValueError('TRAIN IDs changed')
    book = openpyxl.load_workbook(source, read_only=True, data_only=True)
    try:
        rows = iter(book['Monthly Prices'].values)
        header = next(row for row in rows if 'Gold' in row)
        column = header.index('Gold')
        records = prefix_records(rows, column, gold['last_allowed_month'])
    finally:
        book.close()
    result = {**estimate_regimes(records), 'cutoff': gold['last_allowed_month'],
        'source': gold, 'parent_train_ids': train['ids'], 'parent_train_target_start': train['target_start'],
        'unit': 'USD per troy ounce, monthly, revised vintage', 'data_column': 'Gold',
        'prefix_includes_pre_target_training_history': True}
    save_json(BASE, 'data/derived/gold_regime_kernel_v1.json', result)
    save_csv(BASE, 'data/derived/gold_train_prefix_v1.csv', result['records'])
    return {k: result[k] for k in ('first_month', 'last_month', 'valid_prices', 'transition_counts', 'kernel', 'regime_counts')}


def assert_proof(relative):
    value = json.loads((BASE/relative).read_text())
    for item in value['files']:
        if sha256_file(inside(BASE, item['path'])) != item['sha256']:
            raise ValueError('Phase6 protected input changed: '+item['path'])
    return value


def file_rows(paths):
    return [{'path': p, 'sha256': sha256_file(inside(BASE, p))} for p in sorted(set(paths))]


def test_proof():
    xml = ET.parse(BASE/'evidence/phase06/pretrain_tests.xml').getroot()
    if len(xml.findall('.//testcase')) < 181 or any(xml.findall('.//'+tag) for tag in ('failure', 'error', 'skipped')):
        raise ValueError('Pretrain test gate failed')
    if json.loads((BASE/'evidence/phase06/pretrain_coverage.json').read_text())['totals']['percent_covered'] < 80:
        raise ValueError('Phase6 coverage below80')


def declare():
    runtime = preflight()['runtime']
    test_proof()
    verify_lock(BASE, 'evidence/phase05/experiment_lock.json')
    paths = FILES+['evidence/phase05/experiment_lock.json', 'data/derived/gold_regime_kernel_v1.json',
        'data/derived/gold_train_prefix_v1.csv', 'evidence/phase06/pretrain_tests.xml', 'evidence/phase06/pretrain_coverage.json']
    value = {'schema': 'ag02.phase06.train.1', 'matrix': specs(), 'runtime': runtime,
        'market_configs': {k: asdict(v) for k, v in markets().items()},
        'learning': protocol()['controlled_configs']['baseline'], 'checkpoint_interval': 100,
        'q8_checkpoint_episodes': [0, 1000, 2500, 5000], 'expected_final_claims': 160,
        'evaluation': protocol()['evaluation'], 'files': file_rows(paths), 'free_bytes': disk_guard(BASE)}
    save_json(BASE, 'evidence/phase06/train_declaration.json', value)
    return {'status': 'DECLARED', 'runs': 15, 'learners': 20, 'sha256': sha256_file(BASE/'evidence/phase06/train_declaration.json')}


def update_state(state):
    path = BASE/'evidence/phase06/active_controller.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2)+'\n')
    temporary.replace(path)


def train(resume=False):
    declaration = assert_proof('evidence/phase06/train_declaration.json')
    proof = sha256_file(BASE/'evidence/phase06/train_declaration.json')
    state = {'stage': 'train', 'status': 'RUNNING', 'pid': os.getpid(), 'completed': 0, 'current': None}
    records = []
    try:
        for spec in declaration['matrix']:
            state['current'] = spec['run_id']
            update_state(state)
            runner = execute_pair if spec['learners']==2 else execute_run
            result = runner(BASE, spec, MarketConfig(**declaration['market_configs'][spec['kernel_id']]),
                            LearningConfig(**declaration['learning']), proof, resume=resume, interval=100)
            records.append({**spec, 'complete_path': 'artifacts/runs/'+spec['run_id']+'/complete.json',
                'q_sha256': result['q_sha256'], 'train_wall_seconds': result['train_wall_seconds'],
                'train_cpu_seconds': result['train_cpu_seconds'], 'resumed': result['resumed']})
            state['completed'] = len(records)
            print(f'{len(records)}/15 TRAIN COMPLETE {spec["run_id"]}', flush=True)
        save_json(BASE, 'artifacts/manifests/phase06/train_completion.json', {'status': 'COMPLETE', 'entries': records,
                  'declaration_sha256': proof, 'market_runs': 15, 'learner_instances': 20})
        state.update({'status': 'COMPLETE', 'current': None})
    except BaseException as error:
        state.update({'status': 'FAILED_RETAIN_CHECKPOINT', 'error': str(error)})
        raise
    finally:
        state['pid'] = None
        update_state(state)
    return {'status': 'COMPLETE', 'train_runs': 15}


def build_jobs():
    declaration = assert_proof('evidence/phase06/train_declaration.json')
    jobs = []
    def add(group, policy_id, seed, kernel, role, path=None, learner=None, checkpoint=None, kind='q'):
        q = json.loads((BASE/path).read_text()) if path else None
        if checkpoint is not None:
            q = q['q'][learner]
        scenario = {'market': declaration['market_configs'][kernel], 'episodes': 500, 'scenario_seed': 2000000+seed,
                    'rng': protocol()['rng'], 'initial_history': [0, 0], 'engine': 'matched_tapes_v1'}
        study = 'ag02_phase06_robustness_v1' if group=='variant' else f'ag02_phase06_q8_{policy_id}_v1'
        job = {'job_id': f'{group}/{kernel}/{policy_id}/s{seed:04d}/role{role}', 'study_id': study,
            'group': group, 'policy_id': policy_id, 'seed': seed, 'kernel_id': kernel, 'role': role,
            'kind': kind, 'learner': learner, 'checkpoint_episode': checkpoint,
            'policy_sha256': policy_hash(q, kind), 'scenario_sha256': digest(scenario), 'scenario_spec': scenario}
        if path:
            job.update({'q_path': path, 'q_file_sha256': sha256_file(BASE/path)})
        jobs.append(job)
    for spec in declaration['matrix']:
        verify_run(BASE, spec['run_id'])
        if spec['learners']==2:
            for checkpoint in declaration['q8_checkpoint_episodes']:
                for learner in (0, 1):
                    for role in (0, 1):
                        add('q8', f'learner{learner}_e{checkpoint:06d}', spec['seed'], 'iid', role,
                            f'artifacts/runs/{spec["run_id"]}/checkpoint_e{checkpoint:06d}.json', learner, checkpoint)
        else:
            for role in (0, 1):
                add('variant', 'retrained', spec['seed'], spec['kernel_id'], role,
                    f'artifacts/runs/{spec["run_id"]}/q_table.json')
                add('variant', 'baseline_iid', spec['seed'], spec['kernel_id'], role,
                    f'artifacts/runs/controlled/iid/baseline/s{spec["seed"]:04d}/q_table.json')
                for kind in ('rule', 'no_discount'):
                    add('variant', kind, spec['seed'], spec['kernel_id'], role, kind=kind)
    if len(jobs)!=160 or len({key_for(j) for j in jobs})!=160:
        raise ValueError('Require160 unique evaluation claims')
    return jobs


def declare_eval():
    assert_proof('evidence/phase06/train_declaration.json')
    test_proof()
    jobs = build_jobs()
    paths = FILES+['evidence/phase06/train_declaration.json', 'artifacts/manifests/phase06/train_completion.json']
    paths += [j['q_path'] for j in jobs if 'q_path' in j]
    value = {'schema': 'ag02.phase06.final.1', 'jobs': jobs, 'expected_claims': 160,
        'expected_episode_rows': 80000, 'expected_market_steps': 1600000,
        'files': file_rows(paths), 'free_bytes': disk_guard(BASE)}
    save_json(BASE, 'evidence/phase06/eval_declaration.json', value)
    return {'status': 'DECLARED', 'claims': 160, 'sha256': sha256_file(BASE/'evidence/phase06/eval_declaration.json')}


def forward(job):
    q = None
    if 'q_path' in job:
        path = BASE/job['q_path']
        if sha256_file(path) != job['q_file_sha256']:
            raise ValueError('Q file changed')
        q = json.loads(path.read_text())
        if job['checkpoint_episode'] is not None:
            q = q['q'][job['learner']]
        if q_digest(q) != job['policy_sha256']:
            raise ValueError('Q payload changed')
    scenario = job['scenario_spec']
    result = evaluate_tapes(q, MarketConfig(**scenario['market']), episodes=500,
        scenario_seed=scenario['scenario_seed'], role=job['role'], kind=job['kind'], guard=lambda: disk_guard(BASE))
    if 'q_path' in job and sha256_file(BASE/job['q_path']) != job['q_file_sha256']:
        raise RuntimeError('Source Q changed during eval')
    return {**result, 'partition': 'phase06_frozen_final', 'job_id': job['job_id']}


def evaluate():
    declaration = assert_proof('evidence/phase06/eval_declaration.json')
    proof = sha256_file(BASE/'evidence/phase06/eval_declaration.json')
    state = {'stage': 'evaluate', 'status': 'RUNNING', 'pid': os.getpid(), 'completed': 0, 'current': None}
    records = []
    try:
        for job in declaration['jobs']:
            state['current'] = job['job_id']
            update_state(state)
            disk_guard(BASE)
            saved = claim_once(BASE, job, proof, lambda job=job: forward(job))
            records.append({'job': job, 'key': saved['key'], 'complete_path': PREFIX+'/'+saved['key']+'/complete.json'})
            state['completed'] = len(records)
            print(f'{len(records)}/160 EVALUATED {job["job_id"]}', flush=True)
        save_json(BASE, 'artifacts/evaluation/phase06/completion.json', {'status': 'EVALUATED', 'entries': records,
            'declaration_sha256': proof, 'unique_claims': len(records)})
        state.update({'status': 'COMPLETE', 'current': None})
    except BaseException as error:
        state.update({'status': 'FAILED_RETAIN_CLAIMS', 'error': str(error)})
        raise
    finally:
        state['pid'] = None
        update_state(state)
    return {'status': 'COMPLETE', 'claims': len(records)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', choices=('status', 'prepare', 'declare', 'train', 'declare-eval', 'evaluate'))
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.task == 'status':
        path = BASE/'evidence/phase06/active_controller.json'
        result = {'phase': 6, 'controller': json.loads(path.read_text()) if path.exists() else None,
                  'completed_train_runs': sum((BASE/'artifacts/runs'/s['run_id']/'complete.json').exists() for s in specs())}
    else:
        with writer_lock(BASE):
            result = {'prepare': prepare, 'declare': declare, 'train': lambda: train(args.resume),
                      'declare-eval': declare_eval, 'evaluate': evaluate}[args.task]()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
