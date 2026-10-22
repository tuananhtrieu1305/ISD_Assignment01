"""Run each framework in an isolated process and record actual measured readiness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.common.environment import compare_shared_packages, validate_smoke


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--keras-backend", choices=["tensorflow", "keras-torch"], required=True)
    args = parser.parse_args()
    evidence = ROOT / "artifacts/manifests/phase21"
    evidence.mkdir(parents=True, exist_ok=True)
    errors, reports = [], []
    for framework, env_name in [("torch", "torch"), (args.keras_backend, "keras")]:
        for device in ("gpu", "cpu"):
            stem = f"{framework}-{device}"
            output = evidence / f"{stem}.json"
            # A failed process must never reuse a previous successful JSON.
            output.unlink(missing_ok=True)
            command = [
                str(args.runtime / f".venv-{env_name}/bin/python"),
                str(ROOT / "scripts/gpu_smoke.py"),
                "--framework",
                framework,
                "--device",
                device,
                "--output",
                str(output),
            ]
            print(f"Checking {stem} ...", flush=True)
            worker_env = os.environ.copy()
            if framework == "tensorflow":
                site = args.runtime / ".venv-keras/lib/python3.11/site-packages/nvidia"
                libraries = ":".join(str(path) for path in sorted(site.glob("*/lib")))
                worker_env["LD_LIBRARY_PATH"] = libraries + ":" + worker_env.get("LD_LIBRARY_PATH", "")
            try:
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=worker_env,
                    capture_output=True,
                    text=True,
                    timeout=600,
                    check=False,
                )
                (evidence / f"{stem}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
                report = json.loads(output.read_text()) if output.exists() else {"status": "FAIL"}
                report["process_returncode"] = result.returncode
                issues = validate_smoke(report)
                if result.returncode:
                    issues.append(f"process exited {result.returncode}")
            except subprocess.TimeoutExpired:
                report, issues = {"status": "FAIL"}, ["600 second timeout"]
            errors.extend(f"{stem}: {issue}" for issue in issues)
            reports.append({"name": stem, "report": report})
    if not errors:
        left, right = reports[0]["report"]["shared_packages"], reports[2]["report"]["shared_packages"]
        errors.extend(f"Shared package mismatch: {name}" for name in compare_shared_packages(left, right))
    nvidia = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,compute_cap", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        check=False,
    )
    manifest = {
        "status": "PASS" if not errors else "FAIL",
        "generated_at": datetime.now(UTC).isoformat(),
        "platform": platform.platform(),
        "python": sys.version,
        "runtime_root": str(args.runtime),
        "keras_backend": args.keras_backend,
        "nvidia_smi": nvidia.stdout.strip(),
        "host_free_bytes": shutil.disk_usage(ROOT).free,
        "uv_lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        "checks": reports,
        "errors": errors,
        "tensorflow_probe": "artifacts/manifests/phase21/tensorflow-probe.log",
        "scope": "Synthetic smoke only; no training dataset or sealed Ch5 TEST was evaluated.",
    }
    (ROOT / "artifacts/manifests/environment.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps({"status": manifest["status"], "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
