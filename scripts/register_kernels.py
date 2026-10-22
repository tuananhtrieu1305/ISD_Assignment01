"""Register project-local kernels with the backend selected before any import."""

import argparse
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--runtime", type=Path, required=True)
parser.add_argument("--keras-backend", choices=["tensorflow", "keras-torch"], required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
for name in ("torch", "keras"):
    python = args.runtime / f".venv-{name}/bin/python"
    subprocess.run(
        [
            str(python),
            "-m",
            "ipykernel",
            "install",
            "--prefix",
            str(args.runtime),
            "--name",
            f"ai-v3-{name}",
            "--display-name",
            f"AI V3 ({name}, WSL GPU)",
        ],
        check=True,
    )
    spec_path = args.runtime / f"share/jupyter/kernels/ai-v3-{name}/kernel.json"
    spec = json.loads(spec_path.read_text())
    spec["env"] = {
        "KERAS_BACKEND": "tensorflow" if name == "keras" and args.keras_backend == "tensorflow" else "torch",
        "PYTHONPATH": str(root),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if name == "keras" and args.keras_backend == "tensorflow":
        site = args.runtime / ".venv-keras/lib/python3.11/site-packages/nvidia"
        spec["env"]["LD_LIBRARY_PATH"] = ":".join(str(path) for path in sorted(site.glob("*/lib")))
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
