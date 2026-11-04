"""Record restored runtime probes in Phase29, without rewriting frozen Phase21.

Only synthetic GPU/CPU probes. No training, real dataset or TEST evaluation.
"""

import argparse
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json
from src.common.environment import compare_shared_packages, validate_smoke

BASE = ROOT / "artifacts/manifests/phase29/runtime_recovery/r1"
LOCK_SHA = "b0c71fd20e221ed3456278e1916079c46ac206831a98dcf40d3b8f7a83477862"


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}


def recover(runtime):
    if sys.version_info[:3] != (3, 11, 17) or sha256_file(ROOT / "uv.lock") != LOCK_SHA:
        raise ValueError("Restored Python/dependency lock differs from declared runtime")
    existing = BASE / "verification.json"
    if existing.exists():
        receipt = read_json(existing)
        for row in receipt["reports"]:
            for name in ("report", "log"):
                path = ROOT / row[name]["path"]
                if sha256_file(path) != row[name]["sha256"]:
                    raise ValueError("Immutable runtime probe changed")
        return receipt
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    attempt = BASE / "attempts" / stamp
    attempt.mkdir(parents=True, exist_ok=False)
    reports = []
    errors = []
    old = read_json(ROOT / "artifacts/manifests/environment.json")
    old_shared = old["checks"][0]["report"]["shared_packages"]
    for framework, environment in (("torch", "torch"), ("tensorflow", "keras")):
        for device in ("gpu", "cpu"):
            stem = f"{framework}-{device}"
            output = attempt / (stem + ".json")
            log = attempt / (stem + ".log")
            worker_env = {**os.environ, "OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2",
                          "MKL_NUM_THREADS": "2", "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
                          "KERAS_BACKEND": "tensorflow", "PYTHONDONTWRITEBYTECODE": "1"}
            if device == "cpu":
                worker_env["CUDA_VISIBLE_DEVICES"] = "-1"
            if framework == "tensorflow":
                site = runtime / ".venv-keras/lib/python3.11/site-packages/nvidia"
                libraries = ":".join(str(p) for p in sorted(site.glob("*/lib")))
                worker_env["LD_LIBRARY_PATH"] = libraries + ":" + worker_env.get("LD_LIBRARY_PATH", "")
            command = [str(runtime / f".venv-{environment}/bin/python"), str(ROOT / "scripts/gpu_smoke.py"),
                       "--framework", framework, "--device", device, "--output", str(output)]
            print(f"Recovery probe {stem}", flush=True)
            with log.open("x", encoding="utf-8") as stream:
                try:
                    process = subprocess.run(command, cwd=ROOT, env=worker_env, stdout=stream,
                                             stderr=subprocess.STDOUT, timeout=600, check=False)
                    issues = [f"exit={process.returncode}"] if process.returncode else []
                except subprocess.TimeoutExpired:
                    issues = ["600-second probe timeout; TensorFlow backend not substituted"]
            report = read_json(output) if output.exists() else {"status": "FAIL"}
            if output.exists():
                issues.extend(validate_smoke(report))
                if report.get("shared_packages"):
                    issues.extend("Pinned shared package mismatch: " + name
                                  for name in compare_shared_packages(old_shared, report["shared_packages"]))
            else:
                issues.append("Probe report missing")
            errors.extend(stem + ": " + issue for issue in issues)
            reports.append({"name": stem, "status": "FAIL" if issues else "PASS",
                            "report": ref(output) if output.exists() else None, "log": ref(log)})
    document = {"phase": 29, "revision": "runtime_recovery_r1", "status": "FAIL" if errors else "PASS",
                "platform": platform.platform(), "python": sys.version, "distribution": "Ubuntu",
                "runtime_root": str(runtime), "keras_backend": "tensorflow", "uv_lock_sha256": LOCK_SHA,
                "original_environment": ref(ROOT / "artifacts/manifests/environment.json"),
                "reports": reports, "errors": errors, "scope": "Synthetic only; no dataset/TEST/train",
                "training_source_changed": False, "test_evaluation_executed": False}
    write_once(attempt / "result.json", document)
    if errors:
        raise RuntimeError("Runtime recovery probe failed; preserve attempt, no fallback: " + "; ".join(errors))
    write_once(existing, document)
    write_once(runtime / "ready.json", {"status": "PASS", "keras_backend": "tensorflow",
                                       "runtime_recovery": ref(existing)})
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    result = recover(args.runtime.resolve())
    print({"status": result["status"], "reports": len(result["reports"]), "test_executed": False})


if __name__ == "__main__":
    main()
