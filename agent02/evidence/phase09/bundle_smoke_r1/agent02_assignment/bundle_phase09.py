"""Package source and the compact saved-result notebook view; never execute models."""

import argparse
import json
import zipfile
from pathlib import Path

from .code.publication_v1 import digest

BASE = Path(__file__).resolve().parent


def build(revision):
    archive = BASE / f'output/AG02_Source_and_Notebook_{revision}.zip'
    if archive.exists():
        raise FileExistsError('Use a fresh bundle revision')
    selected = set(BASE.glob('*.py'))
    for folder in ('code', 'tests', 'scripts', 'docs', 'data/derived', 'report/phase08'):
        selected.update(p for p in (BASE / folder).rglob('*') if p.is_file() and
                        '__pycache__' not in p.parts and p.suffix in {'.py', '.ps1', '.md', '.json', '.csv', '.ini'})
    for item in json.loads((BASE / 'report/phase08/input_index.json').read_text()):
        selected.add(BASE / item['path'])
    for folder in ('artifacts/metrics', 'artifacts/figures'):
        selected.update(p for p in (BASE / folder).rglob('*') if p.suffix in {'.json', '.csv', '.md', '.png'})
    for folder in ('phase01', 'phase02', 'phase03', 'phase04', 'phase05', 'phase06', 'phase07', 'phase08', 'phase08_presentation_r2'):
        selected.update(p for p in (BASE / 'evidence' / folder).glob('*.json') if p.name in
                        {'input_lock.json', 'protocol_lock.json', 'experiment_lock.json', 'verification.json'})
    selected.update(BASE / p for p in ('notebooks/AG02_Code_and_Results.ipynb', 'report/active_report.json',
                    'report/question_evidence_matrix.md', 'report/question_evidence_matrix_r2.md',
                    'docs/phase09_reproduction.md', 'evidence/phase09/notebook_execution.json',
                    'evidence/phase09/submission_metadata.json', 'evidence/planning_runtime.json'))
    selected.update((BASE / 'evidence/phase09/dependencies').glob('*'))
    files = sorted(selected)
    if any(not p.resolve().is_relative_to(BASE) or not p.is_file() for p in files):
        raise ValueError('Missing/out-of-scope bundle input')
    if sum(p.stat().st_size for p in files) > 120 * 1024**2:
        raise ValueError('Compact source bundle exceeds 120MiB budget')
    manifest = {'schema': 'ag02.source_and_presentation.1', 'revision': revision,
                'scope': 'Source + sealed compact presentation inputs. Full trajectory archive and external runtimes excluded.',
                'notebook_run_all': 'Read-only; no training/final evaluation',
                'files': [{'path': p.relative_to(BASE).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in files]}
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path, 'agent02_assignment/' + path.relative_to(BASE).as_posix())
        bundle.writestr('agent02_assignment/BUNDLE_MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        bundle.writestr('agent02_assignment/START_HERE.md', '# AG02 source và notebook\n\nMở notebooks/AG02_Code_and_Results.ipynb bằng kernel Python đã có.\nĐọc docs/phase09_reproduction.md về cấu trúc, lệnh và giới hạn source bundle.\nRun All chỉ đọc saved outputs; không train hoặc đánh giá cuối lại.\nKhông phải full raw trajectory archive; xem BUNDLE_MANIFEST.json.\n')
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError('Bundle CRC failed')
        for row in manifest['files']:
            import hashlib
            if hashlib.sha256(bundle.read('agent02_assignment/' + row['path'])).hexdigest() != row['sha256']:
                raise ValueError('Bundled bytes differ')
    result = {'status': 'PASS', 'archive': archive.relative_to(BASE).as_posix(), 'sha256': digest(archive),
              'files': len(files), 'bytes': archive.stat().st_size, 'expanded_bytes': sum(r['bytes'] for r in manifest['files']),
              'manifest': manifest, 'scientific_forward_added': 0, 'train_runs_added': 0}
    (BASE / f'evidence/phase09/bundle_{revision}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'manifest'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True, choices=['r1', 'r2', 'r3'])
    build(parser.parse_args().revision)
