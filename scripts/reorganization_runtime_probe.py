"""Read installed package metadata without importing ML frameworks or changing runtime."""
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
packages = {}
for name in ["numpy", "pandas", "scikit-learn", "torch", "tensorflow", "keras", "matplotlib", "pillow", "openpyxl", "flask", "flask-cors", "gunicorn", "nbformat", "nbclient", "joblib"]:
    try:
        packages[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        packages[name] = None
record = {"python": sys.version, "executable": sys.executable, "packages": packages, "module_available": {name: importlib.util.find_spec(name) is not None for name in ["torch", "tensorflow", "keras"]}, "frameworks_imported": False, "packages_installed_or_updated": False}
name = "keras" if ".venv-keras" in sys.executable else "torch"
target = ROOT / f"docs/reorganization/runtime_{name}_metadata.json"
target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, ensure_ascii=False))
