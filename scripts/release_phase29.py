"""Immutable Phase29 release; audit-only after lock, never trains or forwards TEST."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from scripts.phase29_joint_test import EVAL_SOURCE_FILES
from scripts.phase29_preflight import dependencies
from scripts.phase29_test_r1 import FILES, REV, check_revision
from scripts.prepare_phase29_pretest import test_evidence
from scripts.verify_phase29_test_r1 import verify as verify_test
from src.ch02_ml.test_gate import atomic_json
from src.ch04_rnn_lstm.phase29.protocol import BASE, METRICS, MODELS, PREDICTIONS, checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json


def validate_qa(statistics, qa):
    expected = {Path(r["path"]).name for r in statistics["figures"] if r["path"].endswith(".png")}
    actual = qa["reviewed_png_names"]
    if qa["status"] != "PASS" or set(actual) != expected or len(actual) != len(set(actual)):
        raise ValueError("Visual QA must PASS exact complete PNG set, no duplicates")


def verify_lock():
    path = BASE / "experiment_lock.json"
    lock = read_json(path)
    if lock["phase"] != 29 or lock["status"] != "COMPLETE":
        raise ValueError("Invalid Phase29 release")
    for row in lock["files"]:
        checked(row)
    return {
        "status": "PASS",
        "locked_files": len(lock["files"]),
        "lock": ref(path),
        "new_test_forward_executed": False,
    }


def release():
    revision = check_revision()
    for path in (BASE / "active_controller.json", REV / "active_controller.json"):
        active = read_json(path)
        if active["pid"] is not None or active["status"] != "finished":
            raise ValueError("Controller must be finished before release")
    test_audit = verify_test()
    protected = dependencies()
    validation = read_json(BASE / "validation_verification.json")
    if (
        validation["runs"] != 108
        or validation["native_cpu_receipts"] != 108
        or validation["status"] != "PASS"
    ):
        raise ValueError("Validation/CPU audit incomplete")
    xml = [
        BASE / n
        for n in (
            "development-torch-tests.xml",
            "development-keras-tests.xml",
            "development-regression-tests.xml",
            "final-preservation-tests.xml",
            "report-tests.xml",
        )
    ]
    xml.append(REV / "unit.xml")
    count = test_evidence(xml)
    coverage = {}
    for name, path in (
        ("core", BASE / "final_coverage.json"),
        ("revision", REV / "final_coverage.json"),
        ("report", BASE / "report_coverage.json"),
    ):
        totals = read_json(path)["totals"]
        if totals["percent_covered"] < 80 or totals["num_statements"] < 100:
            raise ValueError("Nonempty >=80% coverage required: " + name)
        coverage[name] = {"percent": totals["percent_covered"], "artifact": ref(path)}
    statistics = read_json(BASE / "report_statistics.json")
    manuscript = read_json(BASE / "manuscript_generation.json")
    export = read_json(BASE / "demo/export.json")
    qa = read_json(BASE / "visual_qa.json")
    validate_qa(statistics, qa)
    if qa["statistics_sha256"] != ref(BASE / "report_statistics.json")["sha256"]:
        raise ValueError("QA must reference actual figure/statistics manifest")
    for record in (
        statistics["tables"] + statistics["figures"] + export["artifacts"] + [manuscript["manuscript"]]
    ):
        checked(record)
    if (
        statistics["status"] != "PASS"
        or manuscript["status"] != "PASS"
        or export["status"] != "PASS"
        or statistics["new_test_forward_executed"]
        or export["new_test_forward_executed"]
        or export["models_loaded"] != 18
    ):
        raise ValueError("Report/notebook/CPU export incomplete")
    for required in ("docs/phase29_report.md", "docs/phase29_operations_r1.md"):
        if not (ROOT / required).is_file():
            raise ValueError("Missing handoff document: " + required)
    acceptance = BASE / "acceptance_verification.json"
    timestamp = read_json(acceptance)["at"] if acceptance.exists() else datetime.now(UTC).isoformat()
    result = {
        "phase": 29,
        "status": "PASS",
        "at": timestamp,
        "tests": count,
        "skipped": 0,
        "test_evidence": [ref(p) for p in xml],
        "coverage": coverage,
        "test_audit": test_audit,
        "validation_audit": ref(BASE / "validation_verification.json"),
        "protected_locks": protected,
        "revision": ref(REV / "declaration.json"),
        "visual_qa": ref(BASE / "visual_qa.json"),
        "manuscript": manuscript["manuscript"],
        "new_test_forward_executed": False,
    }
    write_once(acceptance, result)
    candidates = {ROOT / p for p in EVAL_SOURCE_FILES + FILES}
    for folder in (
        BASE,
        METRICS,
        MODELS,
        PREDICTIONS,
        ROOT / "artifacts/figures/phase29",
        ROOT / "experiments/notebooks/v3/ch04_rnn_lstm",
        ROOT / "tests/report29",
        ROOT / "tests/revision29",
    ):
        for path in folder.rglob("*"):
            if not path.is_file() or any(
                p.startswith(".") or p == "__pycache__" for p in path.relative_to(folder).parts
            ):
                continue
            if path.name in {"checkpoint.json", "active_controller.json", "experiment_lock.json"}:
                continue
            if path.suffix in {".tmp", ".part"}:
                raise ValueError("Unresolved temporary artifact")
            candidates.add(path)
    for pattern in ("scripts/*phase29*", "docs/phase29*.md", "experiments/configs/v3/phase29*.ini"):
        candidates.update(p for p in ROOT.glob(pattern) if p.is_file())
    candidates.add(ROOT / "report/sections/v3/ch04_lstm_theory.md")
    candidates.add(ROOT / "report/sections/v3/ch04_rnn_lstm.md")
    write_once(
        BASE / "experiment_lock.json",
        {
            "phase": 29,
            "status": "COMPLETE",
            "created_at": timestamp,
            "scope": "108 LSTM validation selections and joint once-only RNN/LSTM main TEST with authorized schema continuation",
            "original_train_runs": 108,
            "joint_test_runs": 60,
            "test_prediction_rows": 111900,
            "original_test_batches": 3,
            "additional_test_batches": 0,
            "original_power_seal_state": "failed_sealed",
            "continuation_completed": True,
            "revision_evaluator_sha256": revision["evaluator_sha256"],
            "acceptance": ref(acceptance),
            "files": [ref(p) for p in sorted(candidates)],
            "policy": "Immutable evidence; Power original failed seal and43 claims retained; no further train/TEST forward or tuning",
        },
    )
    audit = verify_lock()
    atomic_json(
        BASE / "checkpoint.json",
        {
            "phase": 29,
            "status": "COMPLETE",
            "stage": "released",
            "completed_runs": 108,
            "joint_test_runs": 60,
            "test_prediction_rows": 111900,
            "test_evaluation_executed": True,
            "original_power_seal": "failed_sealed",
            "continuation": "test_schema_r1/evaluated",
            "active_runner": None,
            "experiment_lock": audit["lock"],
            "next_phase": 30,
            "docx_integration": "Phase34–35",
        },
    )
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if (BASE / "experiment_lock.json").exists():
        result = verify_lock()
    elif args.verify_only or not args.lock:
        raise ValueError("No final lock yet; --lock only after all acceptance and visual QA")
    else:
        result = release()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
