"""Sequential isolated-process Phase26 jobs. TEST is a separate explicit stage."""

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime

from src.ch02_ml.protocol import BASE, DATASETS, check_sources
from src.ch02_ml.test_gate import EvaluationGate, atomic_json
from src.ch02_ml.workflow import lock_tests, pending_test_runs
from src.common.contracts import ROOT, read_json


def invoke(entry, mode):
    framework = {"keras": "keras", "pytorch": "torch"}.get(entry["method"], "scratch")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    log = BASE / "logs" / f"{entry['run_id']}_{mode}_{stamp}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    arguments = [
        "bash",
        str(ROOT / "scripts/run_experiment.sh"),
        framework,
        "coverage",
        "run",
        "--append",
        "--rcfile=experiments/configs/v3/phase26_coverage.ini",
        "-m",
        "scripts.phase26_worker",
        "--run-id",
        entry["run_id"],
        "--mode",
        mode,
    ]
    environment = {**os.environ, "PYTHONUNBUFFERED": "1"}
    with log.open("x", encoding="utf-8") as output:
        process = subprocess.Popen(
            arguments,
            cwd=ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in process.stdout:
            output.write(line)
            output.flush()
            print(line, end="", flush=True)
        if process.wait() != 0:
            raise RuntimeError(f"Phase26 {mode} worker failed: {entry['run_id']}. See {log.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["train", "lock-test", "test", "status"], required=True)
    args = parser.parse_args()
    release = check_sources()
    entries = release["runs"]
    if args.stage == "lock-test":
        print(json.dumps(lock_tests()))
        return
    if args.stage == "status":
        print(
            json.dumps(
                {
                    "selected": sum(
                        (BASE / "runs" / row["run_id"] / "selection.json").exists() for row in entries
                    ),
                    "total": len(entries),
                    "seals": {
                        dataset: read_json(BASE / "test_seals" / dataset / "seal.json")["state"]
                        for dataset in DATASETS
                        if (BASE / "test_seals" / dataset / "seal.json").exists()
                    },
                }
            )
        )
        return
    atomic_json(
        BASE / "active_controller.json",
        {"pid": os.getpid(), "stage": args.stage, "started_at": datetime.now(UTC).isoformat()},
    )
    if args.stage == "train":
        if any((BASE / "test_seals" / dataset / "evaluation.started").exists() for dataset in DATASETS):
            raise ValueError("Training prohibited after TEST authorization consumed")
        for i, entry in enumerate(entries):
            if (BASE / "runs" / entry["run_id"] / "selection.json").exists():
                continue
            print(f"JOB {i + 1}/{len(entries)} {entry['run_id']}", flush=True)
            invoke(entry, "train")
    else:
        for dataset in DATASETS:
            gate = EvaluationGate(BASE / "test_seals" / dataset)
            if gate.state()["state"] == "locked":
                gate.begin(release["code"]["dirty_tree_sha256"])
            try:
                pending = pending_test_runs(gate)
                for run in pending:
                    invoke(next(row for row in entries if row["run_id"] == run), "test")
                if gate.state()["state"] == "evaluating":
                    gate.complete()
            except Exception:
                if gate.state()["state"] == "evaluating":
                    gate.fail("TEST worker/controller failed; no automatic retry")
                raise
    atomic_json(
        BASE / "active_controller.json",
        {"pid": None, "stage": args.stage, "status": "finished", "at": datetime.now(UTC).isoformat()},
    )


if __name__ == "__main__":
    main()
