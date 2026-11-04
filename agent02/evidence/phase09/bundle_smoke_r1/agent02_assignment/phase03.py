"""AG02 Phase 3: registered baselines and bounded DEV; never final evaluation."""

import argparse
import fcntl
import json
import os
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from pathlib import Path

from .code.baseline_runs import execute_run, verify_run
from .code.controlled import LearningConfig, MarketConfig
from .code.evaluation.frozen import evaluate_dev
from .code.training import q_digest
from .phase02 import SOURCE_FILES, disk_guard, save_json
from .verify_phase02 import audit as audit_phase2
from .workspace import inside, sha256_file

BASE = Path(__file__).resolve().parent
TRAIN_FILES = list(SOURCE_FILES) + ['code/reference_training.py', 'code/baseline_runs.py', 'phase03.py',
              'code/agent02_experiment.py', 'docs/protocol_v1.json', 'tests/test_phase03_training.py',
              'tests/test_phase03_gate.py', 'tests/coverage_phase03.ini', 'scripts/run_agent02_phase03.ps1']


def protocol():
    return json.loads((BASE / 'docs/protocol_v1.json').read_text())


def phase3_specs():
    return [row for row in protocol()['training_runs'] if row['phase'] == 3]


@contextmanager
def writer_lock(base):
    path = inside(base, 'evidence/phase03/.writer.lock')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def assert_declaration(base=BASE):
    declaration = json.loads(inside(base, 'evidence/phase03/declaration.json').read_text())
    for item in declaration['files']:
        if sha256_file(inside(base, item['path'])) != item['sha256']:
            raise ValueError('Phase3 declaration source hash mismatch: ' + item['path'])
    return declaration


def declare():
    old_lock, _ = audit_phase2()
    if old_lock != json.loads((BASE / 'evidence/phase02/protocol_lock.json').read_text()):
        raise ValueError('Phase2 lock changed')
    xml = ET.parse(BASE / 'evidence/phase03/pretrain_tests_r2.xml').getroot()
    if len(xml.findall('.//testcase')) != 116 or any(xml.findall('.//'+tag) for tag in ('failure', 'error', 'skipped')):
        raise ValueError('Expected 116 passing pretrain tests without skip')
    coverage = json.loads((BASE / 'evidence/phase03/pretrain_coverage_r2.json').read_text())
    if coverage['totals']['percent_covered'] < 80:
        raise ValueError('Pretrain core coverage below 80%')
    paths = TRAIN_FILES + ['evidence/phase03/pretrain_tests_r2.xml', 'evidence/phase03/pretrain_coverage_r2.json']
    declaration = {'schema': 'ag02.phase03.declaration.1', 'runs': phase3_specs(),
                   'protocol_file_sha256': sha256_file(BASE / 'docs/protocol_v1.json'),
                   'phase2_lock_sha256': sha256_file(BASE / 'evidence/phase02/protocol_lock.json'),
                   'device': 'NumPy CPU float64', 'train_episodes_per_run': 5000, 'steps_per_episode': 20,
                   'checkpoint_interval_episodes': 100, 'minimum_free_bytes': 5*1024**3,
                   'dev': {'episodes_per_role': 100, 'roles': [0, 1], 'scenario_seed': 1000011,
                           'partition': 'development', 'tracks_use_same_tapes': True},
                   'reference_adapter': 'Original teacher classes, faithful instrumented loop; fixture parity proven',
                   'initialization': 'fresh zero Q; never smoke checkpoint', 'final_evaluation_authorized': False,
                   'runtime': json.loads((BASE / 'evidence/planning_runtime.json').read_text())['packages'],
                   'files': [{'path': path, 'sha256': sha256_file(BASE / path)} for path in sorted(set(paths))]}
    save_json(BASE, 'evidence/phase03/declaration.json', declaration)
    return assert_declaration()


def develop():
    declaration = assert_declaration()
    output = 'artifacts/metrics/phase03_dev'
    complete = BASE / output / 'complete.json'
    if complete.exists():
        result = json.loads(complete.read_text())
        for item in result['files']:
            if sha256_file(inside(BASE, item['path'])) != item['sha256']:
                raise ValueError('DEV saved output hash mismatch')
        return result
    if (BASE / output / 'claim.json').exists():
        raise FileExistsError('Partial DEV claim: preserve evidence and investigate, do not replay')
    save_json(BASE, output + '/claim.json', {'declaration_sha256': sha256_file(BASE / 'evidence/phase03/declaration.json'),
              'purpose': 'DEV only; not final comparison', 'pid_at_claim': os.getpid()})
    records = []
    for spec in declaration['runs']:
        trained = verify_run(BASE, spec['run_id'])
        q_path = BASE / 'artifacts/runs' / spec['run_id'] / 'q_table.json'
        q = json.loads(q_path.read_text())
        if q_digest(q) != trained['q_sha256']:
            raise ValueError('Trained Q differs')
        for role in declaration['dev']['roles']:
            disk_guard(BASE)
            result = evaluate_dev(q, MarketConfig(), episodes=100, scenario_seed=1000011, role=role)
            relative = output + f'/{spec["track"].lower()}_role{role}.json'
            save_json(BASE, relative, {'run_id': spec['run_id'], **result})
            records.append({'path': relative, 'sha256': sha256_file(BASE / relative)})
    result = {'status': 'COMPLETE', 'partition': 'development', 'final_evaluation': False,
              'market_steps': 8000, 'files': records}
    save_json(BASE, output + '/complete.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', choices=('status', 'declare', 'train', 'development'))
    parser.add_argument('--resume', action='store_true', help='explicitly resume incomplete train claims')
    args = parser.parse_args()
    if args.task == 'status':
        result = {'phase': 3, 'runs': [{'run_id': row['run_id'], 'complete':
                  (BASE / 'artifacts/runs' / row['run_id'] / 'complete.json').exists()} for row in phase3_specs()],
                  'final_evaluation': False}
    else:
        with writer_lock(BASE):
            if args.task == 'declare':
                result = declare()
            elif args.task == 'train':
                declaration = assert_declaration()
                protocol_data = protocol()
                result = [execute_run(BASE, spec, MarketConfig(**protocol_data['market']),
                          LearningConfig(**protocol_data['controlled_configs']['baseline']),
                          sha256_file(BASE / 'evidence/phase03/declaration.json'), resume=args.resume)
                          for spec in declaration['runs']]
                result = [{'run_id': run['run_id'], 'status': run['status'], 'summary': run['summary'],
                           'train_cpu_seconds': run['train_cpu_seconds']} for run in result]
            else:
                result = develop()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
