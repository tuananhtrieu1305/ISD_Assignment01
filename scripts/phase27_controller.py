"""Sequential isolated GPU/CPU jobs; TEST is never an automatic training step."""

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime

from src.ch02_ml.test_gate import atomic_json
from src.ch03_cnn.experiment import checked
from src.ch03_cnn.protocol import BASE, DATASETS, IMPLEMENTATIONS, check_sources, ref
from src.ch03_cnn.workflow import CnnEvaluationGate
from src.common.contracts import ROOT, read_json, validate_document


def selections(release):
    if len(release["runs"]) != 36:
        raise ValueError("Incomplete CNN/majority matrix")
    artifacts = {}
    for entry in release["runs"]:
        path = BASE / "runs" / entry["run_id"] / "selection.json"
        selected = read_json(path)
        if (
            selected["status"] != "succeeded"
            or selected["selection_split"] != "validation"
            or not selected["inference_ready"]
            or selected["config"] != entry["config"]
            or selected["model_contract"] != entry["model_contract"]
        ):
            raise ValueError("Invalid CNN validation selection")
        for key in (
            "checkpoint",
            "checkpoint_metadata",
            "validation_metrics",
            "validation_predictions",
            "history",
            "details",
            "cpu_demo",
            "config",
            "model_contract",
        ):
            checked(selected[key])
            artifacts[selected[key]["path"]] = selected[key]
        if entry["method"] in IMPLEMENTATIONS:
            validate_document("model", read_json(checked(entry["model_contract"])), publish=True)
            validate_document("run", read_json(checked(selected["validation_metrics"])), publish=True)
        if read_json(checked(selected["cpu_demo"]))["status"] != "PASS":
            raise ValueError("CPU checkpoint parity missing")
        artifacts[path.relative_to(ROOT).as_posix()] = ref(path)
    return list(artifacts.values())


def lock_tests(release):
    evidence = read_json(BASE / "pretest_verification.json")
    if evidence["status"] != "PASS" or evidence["code_sha256"] != release["code"]["dirty_tree_sha256"]:
        raise ValueError("Pre-TEST verification not approved")
    artifacts = selections(release) + [ref(BASE / "release.json"), ref(BASE / "pretest_verification.json")]
    for dataset in DATASETS:
        gate = CnnEvaluationGate(BASE / "test_seals" / dataset)
        if (gate.root / "seal.json").exists():
            for record in read_json(gate.root / "manifest.json")["artifacts"]:
                checked(record)
            continue
        entries = [e for e in release["runs"] if e["dataset_id"] == dataset]
        config = read_json(checked(entries[0]["config"]))
        gate.lock(
            {
                "dataset_id": dataset,
                "split_sha256": config["provenance"]["split_sha256"],
                "runs": [e["run_id"] for e in entries],
                "code_sha256": release["code"]["dirty_tree_sha256"],
                "artifacts": artifacts,
                "policy": "12 predeclared runs per dataset (9 CNN+3 majority); full TEST once; interruption consumes claim, no retry/tuning",
            }
        )
    return {"status": "PASS", "datasets_locked": 3, "approved_runs": 36, "test_predictions_executed": False}


def pending(gate):
    if gate.state()["state"] == "evaluated":
        return []
    if gate.state()["state"] != "evaluating":
        raise ValueError("No active CNN TEST batch")
    runs = []
    for run in gate.state()["approved_run_ids"]:
        claimed = (gate.root / (run + ".claimed")).exists()
        path = gate.root / (run + ".result.json")
        if path.exists():
            result = read_json(path)
            if not claimed or result["status"] != "PASS":
                raise ValueError("Invalid TEST result journal")
            for key in ("metrics", "predictions", "details"):
                checked(result[key])
        elif claimed:
            raise ValueError("Interrupted consumed claim; TEST must remain sealed")
        else:
            runs.append(run)
    return runs


def invoke(entry, mode):
    framework = {"keras": "keras", "pytorch": "torch"}.get(entry["method"], "scratch")
    log = BASE / "logs" / f"{entry['run_id']}_{mode}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "bash",
        str(ROOT / "scripts/run_experiment.sh"),
        framework,
        "coverage",
        "run",
        "--append",
        "--rcfile=experiments/configs/v3/phase27_coverage.ini",
        "-m",
        "scripts.phase27_worker",
        "--run-id",
        entry["run_id"],
        "--mode",
        mode,
    ]
    with log.open("x", encoding="utf-8") as output:
        process = subprocess.Popen(
            args,
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
            raise RuntimeError(f"CNN {mode} worker failed: {entry['run_id']}; see {log.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("train", "lock-test", "test", "status"), required=True)
    args = parser.parse_args()
    release = check_sources()
    if args.stage == "status":
        print(
            json.dumps(
                {
                    "selected": sum(
                        (BASE / "runs" / e["run_id"] / "selection.json").exists() for e in release["runs"]
                    ),
                    "total": len(release["runs"]),
                    "seals": {
                        d: read_json(BASE / "test_seals" / d / "seal.json")["state"]
                        for d in DATASETS
                        if (BASE / "test_seals" / d / "seal.json").exists()
                    },
                }
            )
        )
        return
    if args.stage == "lock-test":
        print(json.dumps(lock_tests(release)))
        return
    active = BASE / "active_controller.json"
    if active.exists():
        pid = read_json(active).get("pid")
        if pid and pid != os.getpid() and ROOT.__class__(f"/proc/{pid}").exists():
            raise ValueError("Another CNN controller is active")
    atomic_json(
        active, {"pid": os.getpid(), "stage": args.stage, "started_at": datetime.now(UTC).isoformat()}
    )
    try:
        if args.stage == "train":
            if any((BASE / "test_seals" / d / "evaluation.started").exists() for d in DATASETS):
                raise ValueError("Training forbidden after TEST began")
            for i, entry in enumerate(release["runs"]):
                if (BASE / "runs" / entry["run_id"] / "selection.json").exists():
                    continue
                print(f"JOB {i + 1}/36 {entry['run_id']}", flush=True)
                invoke(entry, "train")
        else:
            for dataset in DATASETS:
                gate = CnnEvaluationGate(BASE / "test_seals" / dataset)
                if gate.state()["state"] == "locked":
                    gate.begin(release["code"]["dirty_tree_sha256"])
                try:
                    for run in pending(gate):
                        invoke(next(e for e in release["runs"] if e["run_id"] == run), "test")
                    if gate.state()["state"] == "evaluating":
                        gate.complete()
                except Exception:
                    if gate.state()["state"] == "evaluating":
                        gate.fail("Worker/controller failed; no automatic TEST retry")
                    raise
    except Exception as error:
        atomic_json(
            active,
            {
                "pid": None,
                "stage": args.stage,
                "status": "failed",
                "error": str(error),
                "at": datetime.now(UTC).isoformat(),
            },
        )
        raise
    atomic_json(
        active, {"pid": None, "stage": args.stage, "status": "finished", "at": datetime.now(UTC).isoformat()}
    )


if __name__ == "__main__":
    main()
