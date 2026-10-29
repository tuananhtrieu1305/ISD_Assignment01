"""Read-only saved-output audit by default; --seal creates Phase 2 lock once."""

import argparse
import json
import xml.etree.ElementTree as ET

from .code.training import TrainSession, digest
from .phase01 import preflight
from .phase02 import BASE, SMOKE, SOURCE_FILES, verify_smoke
from .protocol import build_protocol
from .workspace import inside, sha256_file, write_receipt


def record(relative):
    path = inside(BASE, relative)
    return {'path': relative, 'bytes': path.stat().st_size, 'sha256': sha256_file(path)}


def audit():
    protected = preflight()
    old_lock = json.loads((BASE / 'evidence/phase01/input_lock.json').read_text())
    for item in old_lock['files']:
        if record(item['path']) != item:
            raise ValueError('Phase 1 protected input changed: ' + item['path'])
    protocol = json.loads((BASE / 'docs/protocol_v1.json').read_text())
    if digest(protocol) != digest(build_protocol()):
        raise ValueError('Protocol no longer matches its preregistered builder')
    gold = protocol['future_variants']['gold']
    if sha256_file(BASE.parent / gold['source_path']) != gold['source_sha256']:
        raise ValueError('Gold raw source changed; no price parsing or fitting is permitted here')
    if sha256_file(BASE.parent / gold['parent_split_path']) != gold['parent_split_sha256']:
        raise ValueError('Gold TRAIN boundary metadata changed')
    smoke = verify_smoke(BASE)
    if (smoke['protocol_sha256'] != digest(protocol) or smoke['episodes_per_track'] != 100
            or smoke['training_market_steps'] != 4000 or smoke['development_market_steps'] != 120
            or smoke['full_training_started'] or smoke['final_evaluation_started']
            or smoke['reference_main_called'] or smoke['charts_generated'] != 0):
        raise ValueError('Unexpected smoke scope or budget')
    checkpoint = json.loads((BASE / SMOKE / 'controlled/checkpoint_e000100.json').read_text())
    restored = TrainSession.from_checkpoint(checkpoint)
    if digest(restored.checkpoint()) != digest(checkpoint) or int(restored.visits.sum()) != 2000:
        raise ValueError('Saved checkpoint does not roundtrip or count correctly')
    tests = ET.parse(BASE / 'evidence/phase02/final_tests.xml').getroot()
    cases = tests.findall('.//testcase')
    if len(cases) != 103 or any(tests.findall('.//' + tag) for tag in ('failure', 'error', 'skipped')):
        raise ValueError('Expected exactly 103 passing tests and zero skip/failure/error')
    coverage = json.loads((BASE / 'evidence/phase02/final_coverage.json').read_text())
    total = coverage['totals']
    core = [item['summary'] for name, item in coverage['files'].items()
            if name.replace('\\', '/') != 'agent02_assignment/phase02.py']
    line_percent = 100 * sum(c['covered_lines'] for c in core) / sum(c['num_statements'] for c in core)
    branch_percent = 100 * sum(c['covered_branches'] for c in core) / sum(c['num_branches'] for c in core)
    if total['percent_covered'] < 80 or min(line_percent, branch_percent) < 90:
        raise ValueError('Phase 2 coverage below acceptance threshold')
    checks = json.loads((BASE / 'evidence/phase02/quality_checks.json').read_text())
    if checks['status'] != 'PASS' or any(value != 0 for value in checks['exit_codes'].values()):
        raise ValueError('Lint/parser/CLI checks did not pass')
    paths = list(SOURCE_FILES) + ['verify_phase02.py', 'scripts/run_agent02_phase02.ps1',
             'tests/coverage_phase02.ini', 'tests/test_controlled_model.py', 'tests/test_controlled_runs.py',
             'tests/test_protocol_phase02.py', 'tests/test_phase02_artifacts.py', 'docs/protocol_v1.json',
             'docs/model_core_v1.md', 'docs/phase02_report.md', 'docs/phase02_operations.md',
             'docs/figure_explanation_template.md', 'evidence/phase01/input_lock.json']
    paths.extend(path.relative_to(BASE).as_posix() for path in (BASE / 'evidence/phase02').rglob('*')
                 if path.is_file() and path.suffix in ('.json', '.xml')
                 and path.name not in ('protocol_lock.json', 'verification.json'))
    lock = {'schema_version': 'ag02.phase02.lock.1', 'phase': 2,
            'protocol_canonical_sha256': digest(protocol),
            'phase1_input_lock_sha256': sha256_file(BASE / 'evidence/phase01/input_lock.json'),
            'files': [record(relative) for relative in sorted(set(paths))]}
    receipt = {'status': 'PASS', 'phase': 2, 'tests_passed': len(cases), 'skipped': 0,
               'coverage_combined_percent': total['percent_covered'],
               'coverage_line_percent': 100 * total['covered_lines'] / total['num_statements'],
               'coverage_branch_percent': 100 * total['covered_branches'] / total['num_branches'],
               'coverage_core_line_percent': line_percent, 'coverage_core_branch_percent': branch_percent,
               'coverage_scope': 'Five model/protocol modules plus phase02 smoke runner; excludes teacher and auditor',
               'input_files_phase1_preserved': len(old_lock['files']),
               'selected_parent_assets_preserved': len(protected['preservation']),
               'gold_parent_split_metadata_preserved': True, 'locked_files': len(lock['files']),
               'smoke': {'episodes_per_track': 100, 'training_market_steps': 4000,
                         'development_market_steps': 120, 'checkpoint_exact': True, 'charts': 0},
               'full_training_started': False, 'final_evaluation_started': False,
               'declared_future_runs': len(protocol['training_runs']), 'next_phase': 3}
    return lock, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    lock, receipt = audit()
    if args.seal:
        write_receipt(BASE, 'evidence/phase02/protocol_lock.json', lock)
    if json.loads((BASE / 'evidence/phase02/protocol_lock.json').read_text()) != lock:
        raise ValueError('Phase 2 lock differs; retain evidence and declare a revision')
    receipt['protocol_lock_sha256'] = sha256_file(BASE / 'evidence/phase02/protocol_lock.json')
    if args.seal:
        write_receipt(BASE, 'evidence/phase02/verification.json', receipt)
    elif json.loads((BASE / 'evidence/phase02/verification.json').read_text()) != receipt:
        raise ValueError('Phase 2 verification receipt changed')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
