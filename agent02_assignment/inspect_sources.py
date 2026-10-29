"""Read teacher-provided PDFs without executing embedded or accompanying code."""

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader

SOURCE = Path('/mnt/c/Users/anhca/Documents/Intel_sys_dev/ASIGNMENT-AGENT_02')
DESTINATION = Path(__file__).resolve().parent / 'sources' / 'extracted'


def main():
    DESTINATION.mkdir(parents=True, exist_ok=True)
    manifest = []
    for source in sorted(SOURCE.iterdir()):
        if source.suffix.lower() not in {'.pdf', '.tex'}:
            continue
        record = {'name': source.name, 'bytes': source.stat().st_size,
                  'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
        if source.suffix.lower() == '.pdf':
            reader = PdfReader(source)
            pages = [page.extract_text() or '' for page in reader.pages]
            record['pages'] = len(pages)
            record['page_characters'] = [len(page) for page in pages]
            (DESTINATION / (source.stem + '.txt')).write_text(
                '\n\n'.join(f'===== PAGE {index} =====\n{text}'
                             for index, text in enumerate(pages, 1)), encoding='utf-8')
            (DESTINATION / (source.stem + '.json')).write_text(
                json.dumps(pages, ensure_ascii=False, indent=2), encoding='utf-8')
        else:
            text = source.read_text(encoding='utf-8-sig')
            (DESTINATION / source.name).write_text(text, encoding='utf-8')
            record['lines'] = len(text.splitlines())
        manifest.append(record)
    (DESTINATION.parent / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
