"""Approved schema-only finalization and exact17 unclaimed TEST members, no original seal writes."""

import argparse
import fcntl
import gzip
import json
import os
import subprocess
from datetime import UTC, datetime

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "2"
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

from scripts.phase29_joint_test import evaluator_code as original_code
from scripts.prepare_phase29_pretest import test_evidence, verified_coverage
from scripts.verify_phase29_test import audit_saved_rows
from src.ch02_ml.test_gate import atomic_json
from src.ch04_rnn_lstm.export_r2 import ORPHAN
from src.ch04_rnn_lstm.phase29.holdout_cache import CachedHoldout
from src.ch04_rnn_lstm.phase29.joint_evaluation import evaluate_member, pending
from src.ch04_rnn_lstm.phase29.protocol import BASE, checked, ref
from src.ch04_rnn_lstm.phase29_revision.recovery import (
    ContinuationGate,
    build_orphan_record,
    create_gate,
    test_recovery_schema,
)
from src.common.artifact_core import code_fingerprint, write_once
from src.common.contracts import ROOT, canonical_sha256, read_json

REV = BASE / "revisions/test_schema_r1"
OLD = BASE / "test_seals/ch4_household_power"
DIAG = BASE / "incidents/test_recovery_schema_v1/diagnosis.json"
AUTH = ROOT / "docs/phase29_test_revision1_authorization.md"
OLD_CODE = "d57fe9be8d8a075525a30f2d7693d77080a79cc3c7f96a50960641995c2ae32c"
FILES = [
    "src/ch04_rnn_lstm/phase29_revision/__init__.py",
    "src/ch04_rnn_lstm/phase29_revision/recovery.py",
    "scripts/phase29_test_r1.py",
    "scripts/verify_phase29_test_r1.py",
    "tests/revision29/test_recovery.py",
    "tests/revision29/test_runner.py",
    "experiments/configs/v3/phase29_revision_coverage.ini",
    "docs/phase29_test_revision1_authorization.md",
]


def code():
    if original_code() != OLD_CODE:
        raise ValueError("Frozen original TEST evaluator changed")
    return canonical_sha256({"original_evaluator": OLD_CODE, "revision": code_fingerprint(ROOT, FILES)})


def check_revision():
    document = read_json(REV / "declaration.json")
    if document["evaluator_sha256"] != code():
        raise ValueError("Pinned revision source changed")
    for record in document["source_files"] + document["preserved"] + document["pretest_evidence"]:
        checked(record)
    return document


def declare():
    if (REV / "declaration.json").exists():
        return check_revision()
    if ref(DIAG)["sha256"] != "b3b7188e48931ca161076f68425843a91fe4e048c3c9b26f7354e4da3311f3e2":
        raise ValueError("Incident snapshot changed")
    diagnosis = read_json(DIAG)
    original = read_json(OLD / "manifest.json")
    future = diagnosis["unclaimed_runs"]
    if len(future) != 17 or len(set(future)) != 17 or ORPHAN in future:
        raise ValueError("Exactly17 previously unclaimed members required")
    for run in future:
        if run not in original["approved_run_ids"] or (OLD / (run + ".claimed")).exists():
            raise ValueError("Not an original unclaimed member")
    tests = test_evidence([REV / "unit.xml"])
    coverage = verified_coverage(REV / "pretest_coverage.json")
    if tests < 19 or read_json(REV / "lint.json")["status"] != "PASS":
        raise ValueError("Revision pretest/lint incomplete")
    # Validate every original pretest artifact once, without a model/native forward.
    for row in read_json(BASE / "pretest_verification.json")["evidence"]:
        checked(row)
    protected = [*diagnosis["evidence"], *original["artifacts"], ref(DIAG), ref(AUTH)]
    protected = list({row["path"]: row for row in protected}.values())
    for row in protected:
        checked(row)
    schema_path = REV / "recovery_test_schema.json"
    write_once(schema_path, test_recovery_schema())
    document = {
        "phase": 29,
        "revision": "test_schema_r1",
        "evaluator_sha256": code(),
        "original_evaluator_sha256": OLD_CODE,
        "authorization": ref(AUTH),
        "diagnosis": ref(DIAG),
        "approved_run_ids": future,
        "members": [m for m in original["members"] if m["run_id"] in future],
        "original_manifest": ref(OLD / "manifest.json"),
        "original_seal": ref(OLD / "seal.json"),
        "cache_metadata": read_json(OLD / "cache_receipt.json")["metadata"],
        "recovery_schema": ref(schema_path),
        "original_batch_count": 1,
        "additional_test_batches": 0,
        "source_files": [ref(ROOT / p) for p in FILES],
        "preserved": protected,
        "tests": tests,
        "coverage_percent": coverage,
        "pretest_evidence": [ref(REV / n) for n in ("unit.xml", "pretest_coverage.json", "lint.json")],
        "policy": "No repeat of43 consumed claims/cache/original seal writes; schema-only orphan recovery and17 unclaimed original members",
    }
    write_once(REV / "declaration.json", document)
    create_gate(
        REV / "gate",
        {
            **original,
            "approved_run_ids": future,
            "members": document["members"],
            "evaluator_sha256": code(),
            "original_seal": document["original_seal"],
            "original_manifest": document["original_manifest"],
            "revision": "test_schema_r1",
        },
    )
    return document


def cache_for(document):
    return CachedHoldout(
        document["cache_metadata"], read_json(checked(document["original_seal"]))["manifest_sha256"]
    )


def finalize():
    document = check_revision()
    output = REV / "orphan/result.json"
    if output.exists():
        row = read_json(output)
        for key in ("metrics", "details", "predictions", "checkpoint"):
            checked(row[key])
        return row
    old = read_json(checked(document["original_manifest"]))
    member = next(m for m in old["members"] if m["run_id"] == ORPHAN)
    selected = read_json(checked(member["selection"]))
    details_ref = ref(BASE / "test_details" / (ORPHAN + ".json"))
    predictions = ref(ROOT / "artifacts/predictions/phase29/test" / (ORPHAN + ".jsonl.gz"))
    details = read_json(checked(details_ref))
    cache = cache_for(document)
    with gzip.open(checked(predictions), "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    if audit_saved_rows(cache, rows, details["metrics"]) != 4911:
        raise ValueError("Orphan saved-output audit incomplete")
    original = read_json(checked(selected["validation_metrics"]))
    config = read_json(checked(member["config"]))
    metric, revised = build_orphan_record(
        original,
        details,
        selected,
        predictions,
        details_ref,
        code(),
        datetime.now(UTC).isoformat(),
        old["seal_id"],
        config["unit"],
    )
    detail_path, metric_path = REV / "orphan/details.json", REV / "orphan/metric.json"
    write_once(detail_path, revised)
    write_once(metric_path, metric)
    result = {
        "status": "PASS",
        "run_id": ORPHAN,
        "metrics": ref(metric_path),
        "details": ref(detail_path),
        "predictions": predictions,
        "checkpoint": selected["checkpoint"],
        "optimizer_updates": 0,
        "schema_recovery_only": True,
        "new_test_forward_executed": False,
    }
    write_once(output, result)
    return result


def worker(run):
    document = check_revision()
    if run not in document["approved_run_ids"]:
        raise ValueError("Run not in exact17 whitelist")
    gate = ContinuationGate(REV / "gate")
    return evaluate_member(gate, code(), run, cache_for(document))


def continue_batch():
    document = check_revision()
    if not (REV / "orphan/result.json").exists():
        raise ValueError("Finalize orphan from saved outputs before continuation")
    gate = ContinuationGate(REV / "gate")
    with (REV / ".controller.lock").open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another continuation controller is active") from None
        if gate.state()["state"] == "evaluated":
            if pending(gate, code()):
                raise ValueError("Terminal continuation incomplete")
            return {"status": "PASS", "mode": "saved_results_verified"}
        gate.begin(code())  # Never restarts evaluating/failed states automatically.
        atomic_json(REV / "active_controller.json", {"pid": os.getpid(), "status": "running"})
        outcome = "failed"
        try:
            for member in document["members"]:
                run = member["run_id"]
                engine = {"keras": "keras", "pytorch": "torch"}.get(member["method"], "scratch")
                path = REV / "logs" / (run + ".log")
                path.parent.mkdir(parents=True, exist_ok=True)
                command = [
                    "bash",
                    str(ROOT / "scripts/run_experiment.sh"),
                    engine,
                    "coverage",
                    "run",
                    "--append",
                    "--rcfile=experiments/configs/v3/phase29_revision_coverage.ini",
                    "-m",
                    "scripts.phase29_test_r1",
                    "--stage",
                    "worker",
                    "--run-id",
                    run,
                ]
                print("RUN " + run, flush=True)
                with path.open("x", encoding="utf-8") as log:
                    process = subprocess.run(
                        command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=False
                    )
                if process.returncode:
                    raise RuntimeError(
                        "Continuation worker failed; preserve claim/output/log, no automatic retry: " + run
                    )
                print(json.dumps({"run_id": run, "status": "PASS"}), flush=True)
            gate.complete(code())
            outcome = "finished"
        except Exception:
            gate.fail("Continuation failed; original seal retained; no automatic retry")
            raise
        finally:
            atomic_json(REV / "active_controller.json", {"pid": None, "status": outcome})
    return {"status": "PASS", "unclaimed_runs_completed": 17, "new_test_batches": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("declare", "finalize", "continue", "worker"), required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args()
    functions = {"declare": declare, "finalize": finalize, "continue": continue_batch}
    if args.stage == "worker":
        if not args.run_id:
            parser.error("Worker requires declared run ID")
        result = worker(args.run_id)
    else:
        result = functions[args.stage]()
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k
                in {
                    "status",
                    "revision",
                    "tests",
                    "coverage_percent",
                    "evaluator_sha256",
                    "run_id",
                    "new_test_forward_executed",
                    "unclaimed_runs_completed",
                }
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
