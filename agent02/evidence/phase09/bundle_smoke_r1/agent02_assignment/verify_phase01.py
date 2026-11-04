"""Seal Phase 1 input copies and verify only saved evidence; never run reference."""

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from .phase01 import preflight
from .workspace import sha256_file, write_receipt

BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    current = preflight()
    tests = ET.parse(BASE / 'evidence/phase01/final_tests_r2.xml').getroot()
    cases = tests.findall('.//testcase')
    if len(cases) != 29 or any(tests.findall('.//' + tag) for tag in ('failure', 'error', 'skipped')):
        raise ValueError('Expected 29 passing tests and zero failure/error/skip')
    coverage = json.loads((BASE / 'evidence/phase01/final_coverage_r2.json').read_text())
    if coverage['totals']['percent_covered'] < 80:
        raise ValueError('Workspace guard coverage below acceptance threshold')
    preparation = json.loads((BASE / 'evidence/phase01/preparation.json').read_text())
    probe = preparation['notebook_probe']
    if sha256_file(BASE / probe['path']) != probe['sha256'] or probe['training_steps'] != 0:
        raise ValueError('Runtime notebook evidence changed or ran training')
    manifest = json.loads((BASE / 'sources/manifest.json').read_text())
    paths = ['sources/provided/' + item['name'] for item in manifest]
    paths += ['code/agent02_experiment.py', 'sources/manifest.json',
              'evidence/phase01/reference_inspection.json']
    inputs = {'schema_version': 'ag02.phase01.inputs.1', 'files': [
        {'path': relative, 'bytes': (BASE / relative).stat().st_size,
         'sha256': sha256_file(BASE / relative)} for relative in paths]}
    lock = BASE / 'evidence/phase01/input_lock.json'
    if args.seal:
        write_receipt(BASE, 'evidence/phase01/input_lock.json', inputs)
    if json.loads(lock.read_text()) != inputs:
        raise ValueError('Phase 1 input lock mismatch')
    receipt = {'status': 'PASS', 'phase': 1, 'source_files': 6, 'locked_inputs': len(paths),
               'input_lock_sha256': sha256_file(lock), 'tests_passed': len(cases), 'skipped': 0,
               'workspace_coverage_percent': coverage['totals']['percent_covered'],
               'coverage_scope': 'agent02_assignment.workspace only',
               'runtime_notebook_code_cells': probe['executed_code_cells'],
               'reference_executed': False, 'training_started': False,
               'final_evaluation_started': False, 'selected_existing_inputs_preserved': len(current['preservation']),
               'test_receipt_sha256': sha256_file(BASE / 'evidence/phase01/final_tests_r2.xml'),
               'next_phase': 2}
    if args.seal:
        write_receipt(BASE, 'evidence/phase01/verification.json', receipt)
    elif json.loads((BASE / 'evidence/phase01/verification.json').read_text()) != receipt:
        raise ValueError('Saved verification receipt mismatch')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
