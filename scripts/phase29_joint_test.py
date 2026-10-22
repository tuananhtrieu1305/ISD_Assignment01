"""Explicit joint TEST stages; never called automatically by the training queue."""

import argparse
import fcntl
import json
import os
import subprocess
from datetime import UTC, datetime

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "2"
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

from src.ch04_rnn_lstm.phase29.holdout_cache import CachedHoldout, write_cache
from src.ch04_rnn_lstm.phase29.holdout_data import HoldoutData
from src.ch04_rnn_lstm.phase29.joint_evaluation import approved_members, evaluate_member, pending
from src.ch04_rnn_lstm.phase29.joint_gate import JointGate
from src.ch04_rnn_lstm.phase29.protocol import BASE, DATASETS, SOURCE_FILES, check_sources, checked, ref
from src.common.artifact_core import code_fingerprint, write_once
from src.common.contracts import ROOT, read_json

EVAL_SOURCE_FILES = sorted(
    set(
        SOURCE_FILES
        + [
            "src/ch04_rnn_lstm/phase29/holdout_data.py",
            "src/ch04_rnn_lstm/phase29/holdout_cache.py",
            "src/ch04_rnn_lstm/phase29/joint_evaluation.py",
            "scripts/phase29_joint_test.py",
            "scripts/phase29_receipts.py",
            "scripts/verify_phase29_validation.py",
            "tests/lstm29/test_holdout_data.py",
            "tests/lstm29/test_holdout_cache.py",
            "tests/lstm29/test_joint_evaluation.py",
            "tests/lstm29/test_joint_worker.py",
            "tests/lstm29/test_joint_controller.py",
            "tests/lstm29/test_validation_audit.py",
            "scripts/prepare_phase29_pretest.py",
            "tests/lstm29/test_pretest_proof.py",
            "scripts/finish_phase29_development.ps1",
            "scripts/verify_phase29_test.py",
            "tests/lstm29/test_joint_audit.py",
        ]
    )
)


def evaluator_code():
    return code_fingerprint(ROOT, EVAL_SOURCE_FILES)


def ensure_training_complete(release):
    active = read_json(BASE / "active_controller.json")
    if active.get("pid") is not None or active.get("status") != "finished":
        raise ValueError("Training controller must finish before joint TEST")
    if len(release["runs"]) != 108:
        raise ValueError("Exactly 108 LSTM runs required before TEST")
    if any(not (BASE / "runs" / e["run_id"] / "selection.json").exists() for e in release["runs"]):
        raise ValueError("Missing validation selection; no joint TEST authorization")


def lock_tests():
    release = check_sources()
    ensure_training_complete(release)
    proof = read_json(BASE / "pretest_verification.json")
    code = evaluator_code()
    if proof["status"] != "PASS" or proof["evaluator_sha256"] != code:
        raise ValueError("Pretest proof missing or not for this evaluator")
    for evidence in proof["evidence"]:
        checked(evidence)
    rnn = read_json(ROOT / "artifacts/manifests/phase28/release.json")
    members = approved_members(rnn, release)
    artifact_map = {}
    for member in members:
        owner = ROOT / f"artifacts/manifests/phase{member['owner_phase']}"
        path = owner / "runs" / member["run_id"] / "selection.json"
        member["selection"] = ref(path)
        selected = read_json(path)
        if (
            selected["selection_split"] != "validation"
            or selected["status"] != "succeeded"
            or not selected["inference_ready"]
        ):
            raise ValueError("TEST must use a trained validation-selected checkpoint")
        if selected["config"] != member["config"] or selected["model_contract"] != member["model_contract"]:
            raise ValueError("Selected config/model differs from declaration")
        artifact_map[member["selection"]["path"]] = member["selection"]
        for record in selected.values():
            if isinstance(record, dict) and set(record) == {"path", "sha256"}:
                checked(record)
                artifact_map[record["path"]] = record
    artifacts = list(artifact_map.values()) + [
        ref(BASE / "release.json"),
        ref(BASE / "pretest_verification.json"),
        ref(ROOT / "artifacts/manifests/phase28/experiment_lock.json"),
        ref(BASE / "runtime_recovery/r1/declaration.json"),
        ref(BASE / "runtime_recovery/r1/verification.json"),
    ]
    for dataset in DATASETS:
        gate = JointGate(BASE / "test_seals" / dataset)
        if (gate.root / "seal.json").exists():
            validate_gate(gate, code)
            continue
        subset = [m for m in members if m["dataset_id"] == dataset]
        if len(subset) != 20:
            raise ValueError("Each joint seal requires 9 RNN +9 LSTM +2 baselines")
        gate.lock(
            {
                "phase": 29,
                "dataset_id": dataset,
                "evidence_kind": "measured",
                "seal_id": dataset + "_phase29_joint_test_v1",
                "families_locked": ["rnn", "lstm"],
                "evaluator_sha256": code,
                "pretest_verification_sha256": ref(BASE / "pretest_verification.json")["sha256"],
                "approved_run_ids": [m["run_id"] for m in subset],
                "members": subset,
                "source_files": [ref(ROOT / p) for p in EVAL_SOURCE_FILES],
                "artifacts": artifacts,
                "policy": "One joint main TEST batch; all seeds kept, rolling excluded; consumed claims cannot retry; no timing repeats on TEST inputs",
            }
        )
    return {"status": "PASS", "locked_datasets": 3, "approved_main_runs": 60, "test_forward_executed": False}


def validate_gate(gate, code):
    state, manifest = gate._check(code, {"locked", "evaluating", "evaluated"})
    if evaluator_code() != code:
        raise ValueError("Frozen joint evaluator changed")
    for row in manifest["source_files"] + manifest["artifacts"]:
        checked(row)
    return state, manifest


def materialize(dataset, code):
    gate = JointGate(BASE / "test_seals" / dataset)
    validate_gate(gate, code)
    receipt = gate.root / "cache_receipt.json"
    if receipt.exists():
        CachedHoldout(read_json(receipt)["metadata"], gate.state()["manifest_sha256"])
        return
    if (gate.root / "inputs.materialized").exists():
        raise ValueError("Interrupted consumed TEST materialization; cannot rebuild")
    data = HoldoutData(gate, code)
    meta = write_cache(data, BASE / "test_cache" / dataset, gate.state()["manifest_sha256"])
    write_once(
        receipt,
        {
            "status": "PASS",
            "metadata": meta,
            "test_count": len(data.test_ids),
            "gate_consumed_before_materialization": True,
        },
    )


def model_worker(dataset, run, code):
    gate = JointGate(BASE / "test_seals" / dataset)
    validate_gate(gate, code)
    cache = CachedHoldout(
        read_json(gate.root / "cache_receipt.json")["metadata"], gate.state()["manifest_sha256"]
    )
    return evaluate_member(gate, code, run, cache)


def invoke(framework, dataset, stage, code, run=None):
    path = (
        BASE / "test_logs" / f"{dataset}_{run or stage}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}.log"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "bash",
        str(ROOT / "scripts/run_experiment.sh"),
        framework,
        "coverage",
        "run",
        "--append",
        "--rcfile=experiments/configs/v3/phase29_coverage.ini",
        "-m",
        "scripts.phase29_joint_test",
        "--stage",
        stage,
        "--dataset",
        dataset,
        "--code",
        code,
    ]
    if run:
        command += ["--run-id", run]
    with path.open("x", encoding="utf-8") as stream:
        process = subprocess.run(
            command,
            cwd=ROOT,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if process.returncode:
        raise RuntimeError("Joint TEST worker failed; preserve consumed claim/log: " + path.name)
    print(json.dumps({"dataset": dataset, "run": run, "stage": stage, "status": "PASS"}), flush=True)


def test_batch():
    release = check_sources()
    ensure_training_complete(release)
    code = evaluator_code()
    lock = BASE / ".joint_test_controller.lock"
    with lock.open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another joint TEST controller is active") from None
        for dataset in DATASETS:
            gate = JointGate(BASE / "test_seals" / dataset)
            validate_gate(gate, code)
            if gate.state()["state"] == "evaluated":
                pending(gate, code)
                continue
            if gate.state()["state"] == "locked":
                gate.begin(code)
            try:
                todo = pending(gate, code)
                invoke("scratch", dataset, "cache-worker", code)
                manifest = read_json(gate.root / "manifest.json")
                by_run = {m["run_id"]: m for m in manifest["members"]}
                for run in todo:
                    method = by_run[run]["method"]
                    invoke(
                        {"keras": "keras", "pytorch": "torch"}.get(method, "scratch"),
                        dataset,
                        "model-worker",
                        code,
                        run,
                    )
                gate.complete(code)
            except Exception:
                if gate.state()["state"] == "evaluating":
                    gate.fail("Joint controller/worker failed; no automatic TEST retry")
                raise
    return {"status": "PASS", "datasets": 3, "runs": 60, "test_batch_per_dataset": 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", required=True, choices=("lock-test", "test", "status", "cache-worker", "model-worker")
    )
    parser.add_argument("--dataset", choices=DATASETS)
    parser.add_argument("--run-id")
    parser.add_argument("--code")
    args = parser.parse_args()
    if args.stage == "lock-test":
        result = lock_tests()
    elif args.stage == "test":
        result = test_batch()
    elif args.stage == "status":
        result = {
            d: read_json(BASE / "test_seals" / d / "seal.json")
            if (BASE / "test_seals" / d / "seal.json").exists()
            else "not_locked"
            for d in DATASETS
        }
    else:
        if not args.dataset or not args.code or (args.stage == "model-worker" and not args.run_id):
            parser.error("Worker requires frozen dataset/code/run")
        result = (
            materialize(args.dataset, args.code)
            if args.stage == "cache-worker"
            else model_worker(args.dataset, args.run_id, args.code)
        )
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
