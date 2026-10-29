"""AG02 Phase4: complete 25 CONTROLLED cells, reusing Phase3 seed11; train only."""

import argparse
import json
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from .code.sweep_runs import BASELINE_ID, select_specs, train_one
from .phase02 import disk_guard, save_json
from .phase03 import TRAIN_FILES, writer_lock
from .workspace import inside, sha256_file

BASE = Path(__file__).resolve().parent
FILES = TRAIN_FILES + ['code/sweep_runs.py', 'code/sweep_analysis.py', 'phase04.py',
         'tests/test_phase04.py', 'tests/coverage_phase04.ini', 'scripts/run_agent02_phase04.ps1']


def verify_lock(base, relative):
    lock = json.loads(inside(base, relative).read_text())
    for item in lock['files']:
        if sha256_file(inside(base, item['path'])) != item['sha256']:
            raise ValueError('Protected hash mismatch: '+item['path'])


def assert_declaration(base=BASE):
    declaration = json.loads(inside(base, 'evidence/phase04/declaration.json').read_text())
    for item in declaration['files']:
        if sha256_file(inside(base, item['path'])) != item['sha256']:
            raise ValueError('Phase4 declared source hash mismatch: '+item['path'])
    return declaration


def declare():
    from .phase01 import preflight

    runtime = preflight()['runtime']
    verify_lock(BASE, 'evidence/phase03/experiment_lock.json')
    data = json.loads((BASE/'docs/protocol_v1.json').read_text())
    specs = select_specs(data)
    xml = ET.parse(BASE/'evidence/phase04/pretrain_tests_r2.xml').getroot()
    count = len(xml.findall('.//testcase'))
    if count < 132 or any(xml.findall('.//'+tag) for tag in ('failure', 'error', 'skipped')):
        raise ValueError('Pretrain tests failed or incomplete')
    coverage = json.loads((BASE/'evidence/phase04/pretrain_coverage_r2.json').read_text())
    if coverage['totals']['percent_covered'] < 80:
        raise ValueError('Pretrain sweep coverage below minimum')
    free = disk_guard(BASE)
    paths = FILES + ['evidence/phase03/experiment_lock.json', 'evidence/phase03/declaration.json',
                    'evidence/phase04/pretrain_tests_r2.xml', 'evidence/phase04/pretrain_coverage_r2.json']
    result = {'schema': 'ag02.phase04.declaration.1', 'matrix': specs, 'new_runs': 24, 'reused_runs': [BASELINE_ID],
              'episodes_per_run': 5000, 'steps_per_episode': 20, 'checkpoint_interval': 100,
              'minimum_free_bytes': 5*1024**3, 'host_free_before_bytes': free, 'runtime': runtime,
              'baseline_declaration_sha256': sha256_file(BASE/'evidence/phase03/declaration.json'),
              'baseline_completion_sha256': sha256_file(BASE/'artifacts/runs'/BASELINE_ID/'complete.json'),
              'analysis': {'moving_average': 100, 'n_seeds': 5, 'std_ddof': 1,
                           'partition': 'training', 'bands': 'mean +/- one sample std across training seeds; not CI'},
              'development_forward_authorized': False, 'final_evaluation_authorized': False,
              'files': [{'path': path, 'sha256': sha256_file(BASE/path)} for path in sorted(set(paths))]}
    save_json(BASE, 'evidence/phase04/declaration.json', result)
    return result


def update_state(value):
    path = BASE/'evidence/phase04/active_controller.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
    temporary.replace(path)


def train(resume=False):
    declaration = assert_declaration()
    data = json.loads((BASE/'docs/protocol_v1.json').read_text())
    records = []
    state = {'status': 'RUNNING', 'pid': os.getpid(), 'completed_cells': 0, 'current_run': None,
             'final_evaluation': False, 'started_unix': time.time()}
    try:
        for spec in declaration['matrix']:
            state.update({'current_run': spec['run_id'], 'completed_cells': len(records)})
            update_state(state)
            result = train_one(BASE, spec, data, sha256_file(BASE/'evidence/phase04/declaration.json'),
                               declaration['baseline_declaration_sha256'], resume=resume)
            records.append({key: result[key] for key in ('run_id', 'q_sha256', 'summary',
                           'train_cpu_seconds', 'train_wall_seconds', 'resumed',
                           'reused_from_phase3', 'source_declaration_sha256')})
            print(f'{len(records)}/25 COMPLETE {spec["run_id"]}', flush=True)
        save_json(BASE, 'artifacts/manifests/phase04/train_completion.json',
                  {'status': 'COMPLETE', 'entries': records, 'final_evaluation_count': 0})
        state.update({'status': 'COMPLETE', 'completed_cells': len(records), 'current_run': None})
        return {'status': 'COMPLETE', 'matrix_cells': len(records), 'new_trained': 24, 'reused': 1}
    except BaseException as error:
        state.update({'status': 'FAILED_RETAIN_CHECKPOINT', 'error': type(error).__name__+': '+str(error)})
        raise
    finally:
        state.update({'pid': None, 'finished_unix': time.time()})
        update_state(state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', choices=('status', 'declare', 'train'))
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.task == 'status':
        specs = select_specs(json.loads((BASE/'docs/protocol_v1.json').read_text()))
        result = {'phase': 4, 'matrix_cells': len(specs), 'completed_cells': sum(
                  (BASE/'artifacts/runs'/spec['run_id']/'complete.json').exists() for spec in specs),
                  'controller': json.loads((BASE/'evidence/phase04/active_controller.json').read_text())
                  if (BASE/'evidence/phase04/active_controller.json').exists() else None,
                  'final_evaluation': False}
    else:
        with writer_lock(BASE):
            result = declare() if args.task == 'declare' else train(args.resume)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
