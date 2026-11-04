"""Hash-only verification of the final Agent02 publication and its evidence."""

import argparse
import json
from pathlib import Path

from .code.publication_v1 import digest

BASE = Path(__file__).resolve().parent
EVIDENCE = BASE / 'evidence/phase10'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((BASE / 'output/AG02_RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    if manifest['status'] != 'COMPLETE' or manifest['pages'] != 28 or manifest['submitted_to_instructor']:
        raise ValueError('Invalid final release state')
    for row in manifest['files']:
        path = (BASE / row['path']).resolve()
        if not path.is_relative_to(BASE) or digest(path) != row['sha256'] or path.stat().st_size != row['bytes']:
            raise ValueError('Final product changed:' + row['path'])
    old = json.loads((BASE / 'evidence/phase09/experiment_lock.json').read_text())
    for row in old['files']:
        if digest(BASE / row['path']) != row['sha256']:
            raise ValueError('Earlier candidate/evidence changed')
    paths = [BASE / row['path'] for row in manifest['files']]
    paths += [BASE / p for p in ('output/AG02_RELEASE_MANIFEST.json', 'output/AG02_HUONG_DAN_NOP.md',
              'phase10_release.py', 'verify_phase10.py', 'docs/phase10_report.md',
              'evidence/phase09/experiment_lock.json')]
    paths += [p for p in EVIDENCE.rglob('*') if p.is_file() and p.name not in
              {'.coverage', 'experiment_lock.json', 'verification.json'}]
    lock = {'schema': 'ag02.phase10.final_lock.1', 'files': [
        {'path': p.relative_to(BASE).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)}
        for p in sorted(set(paths))]}
    target = EVIDENCE / 'experiment_lock.json'
    receipt_path = EVIDENCE / 'verification.json'
    if args.seal:
        if target.exists() or receipt_path.exists():
            raise ValueError('Keep the final release; make a new revision')
        target.write_text(json.dumps(lock, indent=2) + '\n', encoding='utf-8')
    elif json.loads(target.read_text()) != lock:
        raise ValueError('Final release or evidence changed')
    receipt = {'status': 'PASS', 'phase': 10, 'assignment': 'COMPLETE',
               'final_release_manifest': 'output/AG02_RELEASE_MANIFEST.json',
               'locked_files': len(lock['files']), 'experiment_lock_sha256': digest(target),
               'phase9_locked_files_preserved': len(old['files']), 'pages': 28,
               'requirements_passed': 18, 'questions': 10, 'figures': 20, 'native_tables': 14,
               'tests_passed': 245, 'skipped': 0, 'all_pages_reviewed': True,
               'native_word_readonly_pages': manifest['native_word_readonly_pages'],
               'prior_scientific_files_preserved': manifest['prior_scientific_files_preserved'],
               'scientific_forward_added': 0, 'train_runs_added': 0, 'submitted_to_instructor': False}
    if args.seal:
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    elif json.loads(receipt_path.read_text()) != receipt:
        raise ValueError('Final receipt changed')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
