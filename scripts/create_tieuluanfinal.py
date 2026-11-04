"""Copy the approved paper baseline without mutating original scientific files."""
from pathlib import Path
import hashlib
import json
import shutil
import time
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tieuluan3'
TARGET = ROOT / 'tieuluanfinal'
SKIP = {'.git', 'node_modules', '__pycache__', '.runtime', '.venv'}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    if TARGET.exists() and '--resume' not in sys.argv:
        raise FileExistsError('Refusing to overwrite an existing final folder')
    files = [p for p in SOURCE.rglob('*') if p.is_file()
             and not SKIP.intersection(p.relative_to(SOURCE).parts)
             and not p.name.startswith('.env') and p.suffix not in {'.pyc', '.pyo'}]
    total = sum(p.stat().st_size for p in files)
    existing=sum(p.stat().st_size for p in TARGET.rglob('*') if p.is_file()) if TARGET.exists() else 0
    if shutil.disk_usage(ROOT).free < max(0,total-existing) + 4 * 2**30:
        raise RuntimeError('Need baseline size plus 4GiB for report/render headroom')
    TARGET.mkdir(exist_ok=True)
    rows = []
    tick = time.monotonic()
    def copied(source):
        relative = source.relative_to(SOURCE)
        target = TARGET / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        before=sha(source)
        if not target.exists() or target.stat().st_size!=source.stat().st_size or sha(target)!=before:
            shutil.copy2(source,target)
        after=sha(target)
        if before != after:
            raise RuntimeError('Copy integrity failure: ' + str(relative))
        return {'path': relative.as_posix(), 'bytes': target.stat().st_size, 'sha256': before}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i,row in enumerate(pool.map(copied,files)):
            rows.append(row)
            if time.monotonic()-tick>20:
                print(f'Copied and hash-checked {i+1}/{len(files)} files',flush=True)
                tick=time.monotonic()
    folder = TARGET / 'docs/final_revision'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'baseline_copy.json').write_text(json.dumps({
        'source': str(SOURCE), 'target': str(TARGET), 'files': rows,
        'excluded': sorted(SKIP) + ['secrets .env*', 'Python bytecode'],
        'total_bytes': total, 'training_steps': 0, 'scientific_TEST_forward': 0,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'copied_files': len(rows), 'bytes': total, 'hash_parity': True}), flush=True)


if __name__ == '__main__':
    main()
