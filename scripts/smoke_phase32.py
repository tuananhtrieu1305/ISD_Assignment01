"""Live Gunicorn smoke on fixed TRAIN requests; never historical model/agent TEST."""

import argparse
import copy
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json, validate_document


def request_json(base, path, *, payload=None, headers=None):
    body = None if payload is None else json.dumps(payload, allow_nan=False).encode()
    request = urllib.request.Request(
        base + path, data=body, headers={"Content-Type": "application/json", **(headers or {})}
    )
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def probe(project, mode, evidence_name, cpu_reference=None):
    from apps.api.v3.registry import Registry

    registry = Registry()
    samples = registry.json(registry.document["samples"])
    reference = None
    if mode == "local_gpu":
        if cpu_reference is None:
            raise ValueError("GPU probe requires a saved CPU reference")
        reference = read_json(cpu_reference)
        if reference["status"] != "PASS" or reference["mode"] != "cpu":
            raise ValueError("Invalid CPU reference")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="phase32-http-") as temporary:
        database = str(Path(temporary) / "jobs.db")
        env = {
            **os.environ,
            "AI_JOB_DB": database,
            "AI_SERVING_MODE": mode,
            "PYTHONPATH": str(project),
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "AI_TRUSTED_HOSTS": "localhost,127.0.0.1",
            "AI_CORS_ORIGINS": "http://localhost:5173",
        }
        if mode == "cpu":
            env["CUDA_VISIBLE_DEVICES"] = "-1"
        else:
            env.pop("CUDA_VISIBLE_DEVICES", None)
        if (project / "bundle_manifest.json").is_file():
            checked = subprocess.run(
                [sys.executable, "-m", "apps.api.v3.check_bundle"],
                cwd=project,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            write_once(
                ROOT / f"artifacts/manifests/phase32/{evidence_name}_bundle_verification.json",
                {
                    "status": "PASS",
                    "details": json.loads(checked.stdout),
                    "package_manifest_sha256": sha256_file(project / "bundle_manifest.json"),
                },
            )
        log_path = ROOT / "artifacts/manifests/phase32" / (evidence_name + ".gunicorn.log")
        with log_path.open("xb") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "gunicorn",
                    "--chdir",
                    str(project),
                    "--bind",
                    f"127.0.0.1:{port}",
                    "--workers",
                    "1",
                    "--threads",
                    "2",
                    "--timeout",
                    "120",
                    "apps.api.v3.server:create_app()",
                ],
                cwd=project,
                env=env,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
            base = f"http://127.0.0.1:{port}"
            results, started, current_case = [], time.monotonic(), None
            try:
                while time.monotonic() - started < 30:
                    try:
                        if request_json(base, "/health")[0] == 200:
                            break
                    except (OSError, urllib.error.URLError):
                        if process.poll() is not None:
                            raise RuntimeError("Gunicorn exited")
                    time.sleep(0.2)
                else:
                    raise RuntimeError("HTTP startup deadline")
                assert request_json(base, "/ready")[0] == 200
                for path in ["chapters", "datasets", "models", "runs", "openapi.json"]:
                    assert request_json(base, "/api/v3/" + path)[0] == 200
                for item in registry.datasets.values():
                    if item["chapter"] > 1:
                        assert request_json(base, f"/api/v3/datasets/{item['dataset_id']}/results")[0] == 200
                for dataset, sample in samples.items():
                    if mode == "local_gpu" and sample["request"]["chapter"] > 4:
                        continue
                    families = (
                        ["rnn", "lstm"] if dataset.startswith("ch4_") else [sample["request"]["family"]]
                    )
                    for family in families:
                        payload = copy.deepcopy(sample["request"])
                        payload["family"] = family
                        headers = {
                            "X-Client-Token": secrets.token_hex(24),
                            "Idempotency-Key": secrets.token_hex(16),
                        }
                        tick = time.monotonic()
                        code, accepted = request_json(
                            base, "/api/v3/comparisons", payload=payload, headers=headers
                        )
                        assert code == 202, accepted
                        validate_document("api#accepted", accepted)
                        deadline = time.monotonic() + (305 if mode == "local_gpu" else 65)
                        while time.monotonic() < deadline:
                            code, job = request_json(base, accepted["poll_url"], headers=headers)
                            if job["status"] not in {"queued", "running"}:
                                break
                            time.sleep(0.5)
                        validate_document("api#job", job)
                        code, details = request_json(base, accepted["poll_url"] + "/details", headers=headers)
                        for _ in range(20):
                            if "serving_telemetry" in details["data"]:
                                break
                            time.sleep(0.1)
                            _, details = request_json(
                                base, accepted["poll_url"] + "/details", headers=headers
                            )
                        current_case = {
                            "dataset_id": dataset,
                            "family": family,
                            "job": job,
                            "details": details["data"],
                        }
                        if dataset == "ch5_wikidata_subgraphs":
                            assert all(r["status"] == "unavailable" for r in job["results"])
                            assert details["data"]["entity"]["qa_benchmark"] is False
                        else:
                            assert job["status"] == "succeeded", job
                            assert all(
                                r["actual_backend"]
                                == (
                                    "tensorflow"
                                    if mode == "local_gpu" and r["implementation"] == "keras"
                                    else "torch"
                                    if mode == "local_gpu" and r["implementation"] == "pytorch"
                                    else "numpy"
                                )
                                for r in job["results"]
                            )
                        assert not details["data"]["serving_runtime"]["native_frameworks_imported_in_driver"]
                        parity = []
                        if reference is not None:
                            import numpy as np

                            cpu = next(
                                r
                                for r in reference["results"]
                                if r["dataset_id"] == dataset and r["family"] == family
                            )
                            for actual, expected in zip(job["results"], cpu["job"]["results"], strict=True):
                                assert actual["implementation"] == expected["implementation"]
                                assert actual["artifact_sha256"] == expected["artifact_sha256"]
                                a, e = actual["prediction"], expected["prediction"]
                                if a["kind"] == "classification":
                                    assert a["label"] == e["label"]
                                    values = [r["value"] for r in a["probabilities"]]
                                    baseline = [r["value"] for r in e["probabilities"]]
                                else:
                                    assert a["unit"] == e["unit"] and a["horizons"] == e["horizons"]
                                    values, baseline = a["values"], e["values"]
                                np.testing.assert_allclose(values, baseline, rtol=1e-4, atol=1e-5)
                                parity.append(
                                    {
                                        "implementation": actual["implementation"],
                                        "max_abs_error": float(np.max(np.abs(np.asarray(values) - baseline))),
                                        "rtol": 1e-4,
                                        "atol": 1e-5,
                                    }
                                )
                        for identity in job["trace_ids"]:
                            code, trace = request_json(
                                base, "/api/v3/agent-traces/" + identity, headers=headers
                            )
                            assert code == 200
                            validate_document("agent", trace["data"])
                        results.append(
                            {
                                "dataset_id": dataset,
                                "family": family,
                                "sample_id": sample["sample_id"],
                                "input_split": sample["input_split"],
                                "job": job,
                                "details": details["data"],
                                "cpu_gpu_parity": parity,
                                "http_wall_ms": (time.monotonic() - tick) * 1000,
                            }
                        )
                        print(
                            json.dumps(
                                {"dataset": dataset, "family": family, "status": job["status"], "mode": mode}
                            ),
                            flush=True,
                        )
                write_once(
                    ROOT / f"artifacts/manifests/phase32/{evidence_name}.json",
                    {
                        "status": "PASS",
                        "mode": mode,
                        "project": project.relative_to(ROOT).as_posix()
                        if project.is_relative_to(ROOT)
                        else str(project),
                        "results": results,
                        "http_executed": True,
                        "cloud_deployed": False,
                        "models_retrained": 0,
                        "historical_test_evaluation_executed": False,
                        "cpu_reference": None
                        if cpu_reference is None
                        else {
                            "path": cpu_reference.relative_to(ROOT).as_posix(),
                            "sha256": sha256_file(cpu_reference),
                        },
                    },
                )
            except Exception as error:
                write_once(
                    ROOT / f"artifacts/manifests/phase32/{evidence_name}_failure.json",
                    {
                        "status": "FAIL",
                        "mode": mode,
                        "completed": results,
                        "current_case": current_case,
                        "exception_type": type(error).__name__,
                        "historical_test_evaluation_executed": False,
                    },
                )
                raise
            finally:
                import signal

                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--mode", choices=["cpu", "local_gpu"], required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--cpu-reference", type=Path)
    args = parser.parse_args()
    if not args.evidence.replace("_", "").isalnum():
        raise ValueError("Evidence name must be an identifier")
    probe(
        args.project.resolve(),
        args.mode,
        args.evidence,
        args.cpu_reference.resolve() if args.cpu_reference else None,
    )
