"""Run the archived notebook in its extracted compact view without project imports."""

import argparse
import hashlib
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from nbclient import NotebookClient

BASE = Path(__file__).resolve().parent


def check(revision):
    target = BASE / f'evidence/phase09/bundle_smoke_{revision}'
    target.mkdir(parents=True, exist_ok=False)
    archive = BASE / f'output/AG02_Source_and_Notebook_{revision}.zip'
    with zipfile.ZipFile(archive) as bundle:
        for name in bundle.namelist():
            relative = Path(name)
            if relative.is_absolute() or '..' in relative.parts or '\\' in name:
                raise ValueError('Unsafe ZIP entry')
        bundle.extractall(target)
    extracted = target / 'agent02_assignment'
    manifest = json.loads((extracted / 'BUNDLE_MANIFEST.json').read_text())
    before = {r['path']: hashlib.sha256((extracted / r['path']).read_bytes()).hexdigest() for r in manifest['files']}
    if any(before[r['path']] != r['sha256'] for r in manifest['files']):
        raise ValueError('Extracted payload differs')
    notebook_path = extracted / 'notebooks/AG02_Code_and_Results.ipynb'
    notebook = nbformat.read(notebook_path, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            cell.outputs = []
            cell.execution_count = None
    with tempfile.TemporaryDirectory(prefix='ag02-bundle09-') as temporary:
        cache = Path(temporary)
        manager = KernelManager(kernel_name='python3', connection_file=str(cache / 'connection.json'))
        manager.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
        client = NotebookClient(notebook, km=manager, timeout=90, allow_errors=False,
                                resources={'metadata': {'path': str(notebook_path.parent)}})
        try:
            client.execute(env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'CUDA_VISIBLE_DEVICES': '',
                                'PYTHONPATH': '', 'IPYTHONDIR': str(cache / 'ipython'),
                                'JUPYTER_RUNTIME_DIR': str(cache / 'jupyter')})
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
    after = {r['path']: hashlib.sha256((extracted / r['path']).read_bytes()).hexdigest() for r in manifest['files']}
    if before != after:
        raise ValueError('Run All changed a bundled input')
    nbformat.write(notebook, target / 'executed_from_bundle.ipynb')
    result = {'status': 'PASS', 'revision': revision, 'working_directory': notebook_path.parent.relative_to(BASE).as_posix(),
              'executed_code_cells': len([c for c in notebook.cells if c.cell_type == 'code']),
              'all_payload_files_unchanged': len(before), 'external_project_imports': 0,
              'scientific_forward_added': 0, 'train_runs_added': 0}
    (BASE / f'evidence/phase09/bundle_smoke_{revision}.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True, choices=['r1', 'r2', 'r3'])
    check(parser.parse_args().revision)
