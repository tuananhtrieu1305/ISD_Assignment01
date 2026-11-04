"""Sequential isolated RNN validation jobs; deliberately no TEST command."""

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from src.ch02_ml.test_gate import atomic_json
from src.ch04_rnn_lstm.protocol import BASE, check_sources
from src.common.contracts import ROOT, read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("train", "status"), required=True)
    args = parser.parse_args()
    release = check_sources()
    active_path = BASE / "active_controller.json"
    completed = sum((BASE / "runs" / row["run_id"] / "selection.json").exists() for row in release["runs"])
    if args.stage == "status":
        print(
            json.dumps(
                {
                    "completed": completed,
                    "expected": len(release["runs"]),
                    "test_executed": False,
                    "active": read_json(active_path) if active_path.exists() else None,
                },
                indent=2,
            )
        )
        return
    if (BASE / "experiment_lock.json").exists():
        raise ValueError("Phase28 released; do not train again")
    if active_path.exists():
        old = read_json(active_path).get("pid")
        if old and old != os.getpid() and Path(f"/proc/{old}").exists():
            raise ValueError("Another live recurrent controller owns the queue")
    atomic_json(active_path, {"pid": os.getpid(), "status": "running", "stage": "validation_train"})
    try:
        for entry in release["runs"]:
            if (BASE / "runs" / entry["run_id"] / "selection.json").exists():
                continue
            atomic_json(
                BASE / "checkpoint.json",
                {
                    "phase": 28,
                    "status": "IN_PROGRESS",
                    "stage": "validation_train",
                    "controller_pid": os.getpid(),
                    "completed_runs": completed,
                    "expected_runs": len(release["runs"]),
                    "current_run": entry["run_id"],
                    "test_evaluation_executed": False,
                },
            )
            framework = {"keras": "keras", "pytorch": "torch"}.get(entry["method"], "scratch")
            path = BASE / "logs" / f"{entry['run_id']}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}.log"
            path.parent.mkdir(parents=True, exist_ok=True)
            command = [
                "bash",
                str(ROOT / "scripts/run_experiment.sh"),
                framework,
                "coverage",
                "run",
                "--append",
                "--rcfile=experiments/configs/v3/phase28_coverage.ini",
                "-m",
                "scripts.phase28_worker",
                "--run-id",
                entry["run_id"],
            ]
            print(f"RUN {entry['run_id']}", flush=True)
            with path.open("x", encoding="utf-8") as output:
                process = subprocess.Popen(
                    command,
                    cwd=ROOT,
                    env={**os.environ, "PYTHONUNBUFFERED": "1"},
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
                    raise RuntimeError(f"RNN validation worker failed: {entry['run_id']}; see {path.name}")
            completed += 1
        atomic_json(
            BASE / "checkpoint.json",
            {
                "phase": 28,
                "status": "IN_PROGRESS",
                "stage": "validation_complete_pending_acceptance",
                "completed_runs": completed,
                "expected_runs": len(release["runs"]),
                "test_evaluation_executed": False,
            },
        )
    finally:
        atomic_json(
            active_path,
            {
                "pid": None,
                "status": "finished",
                "stage": "validation_train",
                "at": datetime.now(UTC).isoformat(),
            },
        )


if __name__ == "__main__":
    main()
