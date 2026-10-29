"""Verify the single Markdown navigation repair without scientific execution."""

import argparse
import hashlib
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / 'evidence/phase08_presentation_r2'
PARENT_SHA = '5399801278e64aaed9b6535ac4d9684e31434311a4623e33c5bd153445f8bbc6'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    parent = BASE / 'evidence/phase08/experiment_lock.json'
    if digest(parent) != PARENT_SHA:
        raise ValueError('Original content release changed')
    entries = json.loads(parent.read_text(encoding='utf-8'))['files']
    for item in entries:
        if digest(BASE / item['path']) != item['sha256']:
            raise ValueError('Original Phase8 file changed: ' + item['path'])
    original = (BASE / 'report/question_evidence_matrix.md').read_bytes()
    wrong = b'](phase 08/manuscript.md)'
    if original.count(wrong) != 1:
        raise ValueError('Expected one navigation typo')
    repaired = BASE / 'report/question_evidence_matrix_r2.md'
    if repaired.read_bytes() != original.replace(wrong, b'](phase08/manuscript.md)'):
        raise ValueError('Repair must change exactly one link and no claims')
    links = []
    for doc in (repaired, BASE / 'report/phase08/manuscript.md'):
        for label, target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            resolved = (doc.parent / target).resolve()
            if not resolved.is_relative_to(BASE) or not resolved.is_file():
                raise ValueError('Broken or out-of-scope link: ' + target)
            links.append({'document': doc.relative_to(BASE).as_posix(), 'label': label,
                          'target': resolved.relative_to(BASE).as_posix(), 'sha256': digest(resolved)})
    if len(links) != 21:
        raise ValueError('Expected one manuscript link and twenty figure links')
    return {'status': 'PASS', 'phase': 8, 'revision': 'presentation_r2',
            'original_release_sha256': PARENT_SHA, 'original_locked_files_preserved': len(entries),
            'exact_link_replacements': 1, 'resolved_local_links': links,
            'manuscript_changed': False, 'scientific_forward_added': 0, 'train_runs_added': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    receipt = verify()
    files = [BASE / 'verify_phase08_presentation_r2.py', BASE / 'report/question_evidence_matrix_r2.md',
             BASE / 'docs/phase08_presentation_r2.md', BASE / 'evidence/phase08/experiment_lock.json']
    lock = {'schema': 'ag02.phase08.presentation_r2.1', 'files': [
        {'path': p.relative_to(BASE).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)}
        for p in files]}
    OUT.mkdir(parents=True, exist_ok=True)
    lock_path = OUT / 'experiment_lock.json'
    receipt_path = OUT / 'verification.json'
    if args.seal:
        if lock_path.exists() or receipt_path.exists():
            raise ValueError('Existing revision must be verified, never overwritten')
        lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    elif json.loads(lock_path.read_text(encoding='utf-8')) != lock:
        raise ValueError('Presentation revision changed')
    receipt['revision_lock_sha256'] = digest(lock_path)
    if args.seal:
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    elif json.loads(receipt_path.read_text(encoding='utf-8')) != receipt:
        raise ValueError('Presentation receipt changed')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'resolved_local_links'}, indent=2))


if __name__ == '__main__':
    main()
