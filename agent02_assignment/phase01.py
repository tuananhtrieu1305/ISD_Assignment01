"""Phase 1 preparation and read-only preflight; no training command is exposed."""

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path

from .workspace import inside, inspect_python, prepare_sources, sha256_file, validate_runtime, write_receipt

BASE = Path(__file__).resolve().parent
REPO = BASE.parent
SOURCE = Path('/mnt/c/Users/anhca/Documents/Intel_sys_dev/ASIGNMENT-AGENT_02')
EXPECTED_PYTHON = '/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python'
FOLDERS = ('docs', 'code/agents', 'code/environments', 'code/evaluation', 'configs',
           'notebooks', 'data/derived', 'artifacts/runs', 'artifacts/metrics',
           'artifacts/figures', 'artifacts/manifests', 'report/sections', 'report/build',
           'report/qa', 'output', 'scripts')


def runtime_inventory():
    expected = json.loads((BASE / 'evidence/planning_runtime.json').read_text())
    versions = {name: importlib.metadata.version(name) for name in expected['packages']}
    actual = {'python': platform.python_version(), 'packages': versions,
              'executable': sys.executable, 'user': os.environ.get('USER'),
              'platform': platform.system()}
    validate_runtime(actual, expected)
    if sys.executable != EXPECTED_PYTHON or actual['user'] != 'tuananh' or actual['platform'] != 'Linux':
        raise ValueError('Use the existing Ubuntu/tuananh pinned runtime via run_experiment.ps1')
    return actual


def preserved_inputs():
    inventory = json.loads((BASE / 'evidence/planning_runtime.json').read_text())
    checks = []
    for record in inventory['assets']:
        actual = sha256_file(inside(REPO, record['path']))
        if actual != record['sha256']:
            raise ValueError('Existing project input changed: ' + record['path'])
        checks.append({'path': record['path'], 'sha256': actual, 'unchanged': True})
    return checks


def notebook_probe():
    import matplotlib
    import nbformat
    import numpy as np
    from jupyter_client import KernelManager
    from nbclient import NotebookClient

    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell(
            '# Agent02 Phase 1 runtime probe\n\nEnvironment check only. No teacher code, '
            'Q-learning, training, data fitting or final evaluation is executed.'),
        nbformat.v4.new_code_cell(
            'import platform, sys\n'
            'print("Python:", platform.python_version())\nprint("Executable:", sys.executable)'),
        nbformat.v4.new_code_cell(
            'import numpy as np\nimport matplotlib\nmatplotlib.use("Agg")\n'
            'import matplotlib.pyplot as plt\n'
            'print("NumPy:", np.__version__, "| Matplotlib:", matplotlib.__version__)\n'
            'print("Array sum:", int(np.arange(4).sum()))\n'
            'print("Charts generated: 0 | Training steps: 0")'),
    ])
    notebook.metadata.kernelspec = {'display_name': 'Agent02 pinned WSL Python',
                                     'language': 'python', 'name': 'python3'}
    # DrvFS cannot enforce mode 0600. A private Linux temp directory keeps Jupyter's
    # secure_write protection enabled; never set JUPYTER_ALLOW_INSECURE_WRITES.
    with tempfile.TemporaryDirectory(prefix='ag02-phase01-') as temporary:
        cache = Path(temporary)
        manager = KernelManager(kernel_name='python3', connection_file=str(cache / 'connection.json'))
        manager.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
        client = NotebookClient(notebook, km=manager, timeout=60, allow_errors=False,
                                resources={'metadata': {'path': str(BASE)}})
        try:
            client.execute(env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'CUDA_VISIBLE_DEVICES': '',
                                'MPLBACKEND': 'Agg', 'IPYTHONDIR': str(cache / 'ipython'),
                                'JUPYTER_RUNTIME_DIR': str(cache / 'jupyter'),
                                'MPLCONFIGDIR': str(cache / 'matplotlib')})
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
    target = inside(BASE, 'evidence/phase01/runtime_probe.ipynb')
    if target.exists():
        raise FileExistsError('Keep previous notebook probe; use a new phase attempt')
    nbformat.write(notebook, target)
    outputs = [''.join(output.get('text', '') for output in cell.outputs
                        if output.output_type == 'stream')
               for cell in notebook.cells if cell.cell_type == 'code']
    if len(outputs) != 2 or EXPECTED_PYTHON not in outputs[0] or 'Array sum: 6' not in outputs[1]:
        raise ValueError('Runtime notebook did not use the expected interpreter/outputs')
    return {'path': str(target.relative_to(BASE)), 'sha256': sha256_file(target),
            'executed_code_cells': 2, 'outputs': outputs,
            'numpy': np.__version__, 'matplotlib': matplotlib.__version__,
            'charts_generated': 0, 'training_steps': 0}


def prepare():
    if (BASE / 'evidence/phase01/preparation.json').exists():
        raise FileExistsError('Phase 1 already prepared; use read-only preflight')
    free_bytes = shutil.disk_usage(BASE).free
    if free_bytes < 5 * 1024 ** 3:
        raise RuntimeError('Host workspace volume has less than 5 GiB free; do not install or delete data')
    runtime = runtime_inventory()
    before = preserved_inputs()
    manifest = json.loads((BASE / 'sources/manifest.json').read_text())
    source_receipt = prepare_sources(SOURCE, BASE, manifest)
    for relative in FOLDERS:
        inside(BASE, relative).mkdir(parents=True, exist_ok=True)
    existing_receipt = BASE / 'evidence/phase01/source_receipt.json'
    if existing_receipt.exists():
        original = json.loads(existing_receipt.read_text())
        original_pairs = [(row['path'], row['sha256']) for row in original['sources']]
        current_pairs = [(row['path'], row['sha256']) for row in source_receipt['sources']]
        if original['inspection'] != source_receipt['inspection'] or original_pairs != current_pairs:
            raise ValueError('Earlier source receipt differs; retain evidence and investigate')
    else:
        write_receipt(BASE, 'evidence/phase01/source_receipt.json', source_receipt)
    write_receipt(BASE, 'evidence/phase01/reference_inspection.json', source_receipt['inspection'])
    probe = notebook_probe()
    receipt = {'status': 'PASS', 'phase': 1, 'runtime': runtime, 'host_free_bytes_before': free_bytes,
               'notebook_probe': probe,
               'preservation_before': before, 'preservation_after': preserved_inputs(),
               'folders_created': list(FOLDERS), 'reference_executed': False,
               'training_started': False, 'final_evaluation_started': False}
    write_receipt(BASE, 'evidence/phase01/preparation.json', receipt)
    return receipt


def preflight():
    runtime = runtime_inventory()
    manifest = json.loads((BASE / 'sources/manifest.json').read_text())
    for record in manifest:
        for folder in (SOURCE, BASE / 'sources/provided'):
            target = inside(folder, record['name'])
            if target.stat().st_size != record['bytes'] or sha256_file(target) != record['sha256']:
                raise ValueError('Source changed: ' + str(target))
    reference = inspect_python(BASE / 'code/agent02_experiment.py')
    expected = next(record['sha256'] for record in manifest if record['name'] == 'agent02_code.tex')
    if reference['sha256'] != expected:
        raise ValueError('Reference Python copy changed')
    return {'status': 'PASS', 'runtime': runtime, 'source_hashes_verified': len(manifest),
            'reference': reference, 'preservation': preserved_inputs(), 'read_only': True,
            'training_started': False, 'final_evaluation_started': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', choices=('prepare', 'preflight', 'inspect-reference'))
    args = parser.parse_args()
    if args.task == 'prepare':
        receipt = prepare()
    elif args.task == 'preflight':
        receipt = preflight()
    else:
        receipt = inspect_python(BASE / 'code/agent02_experiment.py')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
