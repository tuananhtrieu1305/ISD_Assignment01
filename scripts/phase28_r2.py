"""Versioned validation-only recovery/controller and strict native-CPU receipts."""

import os

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "2"
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import argparse
import json
import subprocess
import traceback
from datetime import UTC, datetime
from pathlib import Path

from src.ch02_ml.experiment import provenance
from src.ch02_ml.protocol import array_sha256
from src.ch02_ml.test_gate import atomic_json
from src.ch04_rnn_lstm.export_r2 import (
    ORPHAN,
    REVISION,
    check_revision,
    compare_outputs,
    native_cpu,
    recovery_schema,
    run_revision,
)
from src.ch04_rnn_lstm.protocol import BASE, IMPLEMENTATIONS, MODELS, ROOT, check_sources, checked, ref
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.artifact_core import ArtifactStore, write_once
from src.common.contracts import read_json
from src.common.numpy_engine import NumpyNetwork

SOURCES = ["src/ch04_rnn_lstm/export_r2.py", "scripts/phase28_r2.py",
           "tests/recurrent/test_export_r2.py", "tests/recurrent/test_experiment.py",
           "docs/phase28_r2_authorization.md"]


def declare():
    release = check_sources()
    if read_json(BASE / "active_controller.json").get("pid") is not None:
        raise ValueError("Another controller owns the queue")
    selections = [ref(BASE / "runs" / e["run_id"] / "selection.json")
                  for e in release["runs"] if (BASE / "runs" / e["run_id"] / "selection.json").exists()]
    if len(selections) != 90:
        raise ValueError("Expected exactly 90 preserved selections at approved revision boundary")
    schema_path = REVISION.parent / "recovery_run.schema.json"
    write_once(schema_path, recovery_schema())
    write_once(REVISION, {
        "phase": 28, "revision": "r2", "status": "DECLARED",
        "authorization": ref(ROOT / "docs/phase28_r2_authorization.md"),
        "original_release": ref(BASE / "release.json"), "source_files": [ref(ROOT / p) for p in SOURCES],
        "preserved_selections": selections,
        "preserved_orphan": [ref(MODELS / ORPHAN / p)
                             for p in ("best.npz", "best.json", "progress.json", "resume/epoch_011.json")],
        "recovery_schema": ref(schema_path),
        "gate": {"reference": "native_cpu", "portable": "numpy_cpu", "rtol": 1e-4, "atol": 1e-5,
                 "all_neural_runs_require_receipt": 108, "original_gpu_cpu_results_preserved": True},
        "training_source_unchanged": True, "orphan_training_updates_allowed": 0,
        "missing_original_telemetry_policy": "null in single-run recovery schema; exclude from train/RAM/VRAM aggregates",
        "test_executed": False,
    })
    print(json.dumps({"status": "DECLARED", "revision": ref(REVISION), "preserved_selections": 90}))


def receipt(entry, data):
    run = entry["run_id"]
    path = REVISION.parent / "cpu_receipts" / f"{run}.json"
    if path.exists():
        existing = read_json(path)
        for key in ("checkpoint", "checkpoint_metadata", "revision", "selection"):
            checked(existing[key])
        if existing["status"] != "PASS":
            raise ValueError("Existing CPU receipt failed")
        return
    folder = BASE / "runs" / run
    selected = read_json(folder / "selection.json")
    config = read_json(checked(entry["config"]))
    weights = ArtifactStore(MODELS / run).load_checkpoint(
        "best", provenance(entry, config), expected_manifest_sha256=selected["checkpoint_metadata"]["sha256"]
    )
    x, _ = data.batch(data.train_ids[:4])
    portable = NumpyNetwork(config["plan"], weights).forward(x)
    demo = read_json(checked(selected["cpu_demo"]))
    # Existing demos record the original GPU/CPU error but not both GPU arrays.
    # Do not invent GPU outputs or repeat a GPU forward in the CPU-only receipt process.
    comparison = compare_outputs(portable, native_cpu(config["plan"], weights, entry["method"], x), portable)
    original = demo.get("comparisons", {}).get("original_gpu_cpu_gate", {
        "status": "PASS", "max_absolute_error": demo["max_absolute_error"],
        "source": selected["cpu_demo"], "output": None,
    })
    comparison["original_gpu_cpu_gate"] = original
    write_once(path, {
        "status": "PASS", "run_id": run, "revision": ref(REVISION),
        "selection": ref(folder / "selection.json"), "checkpoint": selected["checkpoint"],
        "checkpoint_metadata": selected["checkpoint_metadata"],
        "input_split": "train", "ids": data.train_ids[:4], "canonical_x_sha256": array_sha256(x),
        "portable_cpu_output": portable.tolist(), "comparisons": comparison,
        "native_cpu_engine": {"scratch": "numpy_manual", "pytorch": "torch", "keras": "tensorflow"}[entry["method"]],
        "native_cpu_device": "cpu", "validation_executed": False, "test_executed": False,
        "weights_updated": False,
    })


def receipts(method):
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    release, cache, count = check_revision(), {}, 0
    for entry in release["runs"]:
        if entry["method"] != method:
            continue
        key = (entry["dataset_id"], entry["fold"])
        if key not in cache:
            cache[key] = WindowData(*key)
        receipt(entry, cache[key])
        count += 1
        print(json.dumps({"cpu_receipt": entry["run_id"], "status": "PASS"}), flush=True)
    if count != 36:
        raise ValueError("Expected 36 strict CPU receipts per implementation")


def worker(run):
    try:
        print(json.dumps(run_revision(run)), flush=True)
    except Exception:
        write_once(BASE / "attempts" / f"r2_{run}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}.json", {
            "run_id": run, "traceback": traceback.format_exc(), "test_executed": False,
        })
        raise


def train():
    release = check_revision()
    if (BASE / "experiment_lock.json").exists():
        raise ValueError("Released phase cannot be trained again")
    active = BASE / "active_controller.json"
    old = read_json(active).get("pid")
    if old and Path(f"/proc/{old}").exists():
        raise ValueError("Another live controller owns validation queue")
    status, current = "failed", None
    atomic_json(active, {"pid": os.getpid(), "status": "running", "stage": "r2_validation_train"})
    try:
        for entry in release["runs"]:
            if (BASE / "runs" / entry["run_id"] / "selection.json").exists():
                continue
            current = entry["run_id"]
            completed = sum((BASE / "runs" / e["run_id"] / "selection.json").exists() for e in release["runs"])
            atomic_json(BASE / "checkpoint.json", {
                "phase": 28, "status": "IN_PROGRESS", "stage": "r2_validation_train",
                "controller_pid": os.getpid(), "current_run": current,
                "completed_runs": completed, "expected_runs": 132, "test_evaluation_executed": False,
            })
            framework = {"pytorch": "torch", "keras": "keras"}.get(entry["method"], "scratch")
            log = BASE / "logs" / f"r2_{current}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}.log"
            command = ["bash", str(ROOT / "scripts/run_experiment.sh"), framework, "coverage", "run", "--append",
                       "--rcfile=experiments/configs/v3/phase28_coverage.ini", "-m", "scripts.phase28_r2",
                       "--stage", "worker", "--run-id", current]
            print(f"RUN r2 {current}", flush=True)
            with log.open("x", encoding="utf-8") as output:
                process = subprocess.Popen(command, cwd=ROOT, env={**os.environ, "PYTHONUNBUFFERED": "1"},
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                for line in process.stdout:
                    output.write(line)
                    output.flush()
                    print(line, end="", flush=True)
                if process.wait():
                    raise RuntimeError(f"r2 worker failed; inspect {log.name}, do not retrain blindly")
        status = "finished"
    finally:
        completed = sum((BASE / "runs" / e["run_id"] / "selection.json").exists() for e in release["runs"])
        atomic_json(active, {"pid": None, "status": status, "stage": "r2_validation_train",
                             "at": datetime.now(UTC).isoformat()})
        atomic_json(BASE / "checkpoint.json", {
            "phase": 28, "status": "IN_PROGRESS", "controller_pid": None,
            "stage": "validation_complete_pending_acceptance" if status == "finished" else "r2_worker_failed",
            "current_run": None if status == "finished" else current,
            "completed_runs": completed, "expected_runs": 132, "test_evaluation_executed": False,
        })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=("declare", "train", "worker", "receipts"))
    parser.add_argument("--run-id")
    parser.add_argument("--method", choices=IMPLEMENTATIONS)
    args = parser.parse_args()
    if args.stage == "declare":
        declare()
    elif args.stage == "train":
        train()
    elif args.stage == "worker":
        if not args.run_id or args.run_id not in {e["run_id"] for e in check_revision()["runs"]}:
            parser.error("Only declared validation run IDs are allowed")
        worker(args.run_id)
    else:
        if not args.method:
            parser.error("CPU receipt stage requires --method")
        receipts(args.method)


if __name__ == "__main__":
    main()
