"""Seal a tested, rendered candidate handoff; no model or experiment execution."""

import argparse
import ast
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from .code.publication_v1 import digest

BASE = Path(__file__).resolve().parent
EVIDENCE = BASE / 'evidence/phase09'


def load(path):
    return json.loads((BASE / path).read_text(encoding='utf-8'))


def verify():
    for name in ('phase08', 'phase08_presentation_r2'):
        for row in load(f'evidence/{name}/experiment_lock.json')['files']:
            if digest(BASE / row['path']) != row['sha256']:
                raise ValueError('Frozen content changed:' + row['path'])
    for row in load('report/phase08/input_index.json'):
        if digest(BASE / row['path']) != row['sha256']:
            raise ValueError('Report input changed:' + row['path'])
    import nbformat
    notebook = nbformat.read(BASE / 'notebooks/AG02_Code_and_Results.ipynb', as_version=4)
    codes = [c for c in notebook.cells if c.cell_type == 'code']
    if len(codes) != 44 or [c.execution_count for c in codes] != list(range(1, 45)):
        raise ValueError('Notebook incomplete')
    pngs = 0
    for cell in codes:
        tree = ast.parse(cell.source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [node.module] if isinstance(node, ast.ImportFrom) else [a.name for a in node.names]
                if any(name.split('.')[0] not in {'hashlib', 'json', 'platform', 'pathlib', 'IPython', 'decimal'} for name in names):
                    raise ValueError('Notebook must not import experiment/model modules')
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ''
                if name in {'exec', 'eval', 'train', 'learn', 'evaluate', 'evaluate_tapes', 'act', 'step'}:
                    raise ValueError('Scientific execution forbidden in notebook')
        for output in cell.outputs:
            if output.output_type == 'error':
                raise ValueError('Notebook output error')
            pngs += 'image/png' in output.get('data', {})
    if pngs != 20:
        raise ValueError('Notebook image output coverage incomplete')
    visual = load('evidence/phase09/visual_review_r3.json')
    structure = load('report/qa/phase09/r3/structure.json')
    if visual['status'] != 'PASS' or visual['pdf_sha256'] != structure['pdf_sha256'] or len(visual['pages']) != 28:
        raise ValueError('Visual review of final candidate missing')
    for row, checked in zip(structure['pages'], visual['pages']):
        if row['page'] != checked['page'] or row['png_sha256'] != checked['png_sha256'] or checked['status'] != 'PASS':
            raise ValueError('Page changed after visual review')
    for key in ('pdf', 'docx'):
        if digest(BASE / structure[key]) != structure[key + '_sha256']:
            raise ValueError('Candidate changed after inspection')
    if structure['figure_occurrences'] != 20 or structure['questions_in_pdf'] != 10:
        raise ValueError('Rendered coverage incomplete')
    bundle = load('evidence/phase09/bundle_r1.json')
    if digest(BASE / bundle['archive']) != bundle['sha256']:
        raise ValueError('Source ZIP changed')
    with zipfile.ZipFile(BASE / bundle['archive']) as archive:
        for row in bundle['manifest']['files']:
            if hashlib.sha256(archive.read('agent02_assignment/' + row['path'])).hexdigest() != row['sha256']:
                raise ValueError('Bundle payload changed')
    smoke = load('evidence/phase09/bundle_smoke_r1.json')
    if smoke['status'] != 'PASS' or smoke['executed_code_cells'] != 44:
        raise ValueError('Portable Run All failed')
    tests = ET.parse(EVIDENCE / 'final_tests_r3.xml').getroot()
    count = len(tests.findall('.//testcase'))
    if count != 245 or any(tests.findall('.//' + tag) for tag in ('failure', 'error', 'skipped')):
        raise ValueError('Final tests failed')
    coverage = load('evidence/phase09/final_coverage_r3.json')['totals']['percent_covered']
    if coverage < 80 or load('evidence/phase09/quality_checks.json')['status'] != 'PASS':
        raise ValueError('Helper coverage or lint failed')
    metadata = load('evidence/phase09/submission_metadata.json')
    if metadata['submission_mode'] != 'individual' or metadata['final_pdf_filename'] != Path(structure['pdf']).name:
        raise ValueError('User-approved identity/filename mismatch')
    # This is the fresh, read-only dependency audit stdout captured after production.
    dependency = (EVIDENCE / 'dependency_audit.json').read_text(encoding='utf-8')
    parent = json.loads(dependency)
    if parent['status'] != 'PASS' or parent['prior_protected_files_preserved'] != 7501:
        raise ValueError('Dependency preservation failed')
    return {'status': 'PASS', 'phase': 9, 'handoff': 'CANDIDATE_READY_FOR_PHASE10',
            'candidate_revision': 'r3', 'page_count': 28, 'native_tables': 14, 'artifact_bound_tables': 12,
            'figures': 20, 'code_excerpts': 8, 'questions': 10, 'notebook_code_cells': 44,
            'tests_passed': count, 'skipped': 0, 'coverage_combined_percent': coverage,
            'coverage_scope': 'publication_v1 parser/path helpers only; excludes prose,Word renderer,notebook driver and scientific code',
            'prior_protected_files_preserved': 7501, 'notebook': 'notebooks/AG02_Code_and_Results.ipynb',
            'docx': structure['docx'], 'pdf': structure['pdf'], 'source_bundle': bundle['archive'],
            'metadata_confirmed': True, 'all_candidate_pages_reviewed': True, 'final_submission_released': False,
            'scientific_forward_added': 0, 'train_runs_added': 0, 'next_phase': 10}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    receipt = verify()
    paths = [BASE / p for p in ('code/publication_v1.py', 'build_phase09.py', 'make_phase09_notebook.py',
             'inspect_phase09.py', 'bundle_phase09.py', 'check_phase09_bundle.py', 'verify_phase09.py',
             'tests/test_phase09.py', 'tests/coverage_phase09.ini', 'docs/phase09_reproduction.md',
             'docs/phase09_report.md', 'docs/phase09_operations.md', 'notebooks/AG02_Code_and_Results.ipynb',
             receipt['source_bundle'], 'evidence/phase08/experiment_lock.json',
             'evidence/phase08_presentation_r2/experiment_lock.json')]
    for folder in ('report/build/candidate-r3', 'report/qa/phase09/r3', 'evidence/phase09'):
        paths += [p for p in (BASE / folder).rglob('*') if p.is_file() and
                  not any(re.fullmatch(r'bundle_smoke_r\d+', part) for part in p.relative_to(BASE).parts) and
                  p.name not in {'.coverage', 'experiment_lock.json', 'verification.json'}]
    lock = {'schema': 'ag02.phase09.candidate_release.1', 'files': [
        {'path': p.relative_to(BASE).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(set(paths))]}
    lock_path = EVIDENCE / 'experiment_lock.json'
    receipt_path = EVIDENCE / 'verification.json'
    if args.seal:
        if lock_path.exists() or receipt_path.exists():
            raise ValueError('Do not overwrite candidate release')
        lock_path.write_text(json.dumps(lock, indent=2) + '\n', encoding='utf-8')
    elif json.loads(lock_path.read_text()) != lock:
        raise ValueError('Released candidate source/artifacts changed')
    receipt.update({'locked_files': len(lock['files']), 'experiment_lock_sha256': digest(lock_path)})
    if args.seal:
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    elif json.loads(receipt_path.read_text()) != receipt:
        raise ValueError('Candidate receipt changed')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
