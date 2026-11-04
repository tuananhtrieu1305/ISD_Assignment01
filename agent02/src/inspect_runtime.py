"""Non-mutating runtime and reusable-input inventory for the Agent02 plan."""

import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

import torch

BASE = Path(__file__).resolve().parent
REPO = BASE.parent


def main():
    packages = {}
    for name in ('numpy', 'matplotlib', 'pandas', 'scikit-learn', 'torch',
                 'nbformat', 'nbclient', 'python-docx', 'pypdf', 'pytest', 'ruff'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    paths = ['data/raw/ch2/cdc_diabetes/data.csv', 'data/raw/ch2/ames/AmesHousing.txt',
             'data/raw/ch4/gold/CMO-Historical-Data-Monthly.xlsx',
             'data/raw/ch5/medquad/readme.txt', 'docs/phase31_report.md',
             'discovering_ai_agent/notebooks/Discovering_AI_Agent.ipynb', 'uv.lock']
    assets = []
    for relative in paths:
        path = REPO / relative
        assets.append({'path': relative, 'exists': path.is_file(),
                       'bytes': path.stat().st_size if path.is_file() else None,
                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest()
                       if path.is_file() else None})
    result = {'python': platform.python_version(), 'executable': sys.executable,
              'packages': packages, 'cuda_available': torch.cuda.is_available(),
              'gpu_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
              'gpu_total_bytes': torch.cuda.get_device_properties(0).total_memory
              if torch.cuda.is_available() else None,
              'scope': 'Import/device inventory only; no model training or old TEST execution',
              'assets': assets}
    destination = BASE / 'evidence'
    destination.mkdir(exist_ok=True)
    (destination / 'planning_runtime.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
