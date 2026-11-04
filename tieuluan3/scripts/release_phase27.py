"""Final immutable CNN release after visual QA; read-only once locked."""

import argparse
import json
from datetime import UTC, datetime

from scripts.verify_phase27 import test_count, verify
from src.ch02_ml.test_gate import atomic_json
from src.ch03_cnn.protocol import BASE, METRICS, MODELS, PREDICTIONS, SOURCE_FILES, ref
from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json


def verify_lock():
    lock = read_json(BASE / "experiment_lock.json")
    for record in lock["files"]:
        if sha256_file(ROOT / record["path"]) != record["sha256"]:
            raise ValueError(f"Immutable Phase27 file changed: {record['path']}")
    return {
        "status": "PASS",
        "locked_files": len(lock["files"]),
        "lock": ref(BASE / "experiment_lock.json"),
        "test_forward_executed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if (BASE / "experiment_lock.json").exists():
        print(json.dumps(verify_lock(), indent=2))
        return
    if args.verify_only or not args.lock:
        raise ValueError("No CNN release lock; visual QA/acceptance must precede --lock")
    active = read_json(BASE / "active_controller.json")
    if active.get("pid") is not None or active.get("status") != "finished":
        raise ValueError("CNN controller is not finished")
    result = verify("full")
    if result["auditor"] != read_json(BASE / "pretest_verification.json")["auditor"]:
        raise ValueError("CNN auditor differs from pre-TEST frozen version")
    result["pretest"] = ref(BASE / "pretest_verification.json")
    result["postreport_tests"] = test_count(BASE / "revisions/r2/report-tests.xml")
    qa = read_json(BASE / "visual_qa.json")
    active_report = read_json(BASE / "active_report.json")
    if ref(ROOT / active_report["generation"]["path"]) != active_report["generation"]:
        raise ValueError("Active report revision hash mismatch")
    generation = read_json(ROOT / active_report["generation"]["path"])
    if ref(ROOT / generation["manuscript"]["path"]) != generation["manuscript"]:
        raise ValueError("Active manuscript changed")
    result["active_report"] = ref(BASE / "active_report.json")
    if qa["status"] != "PASS" or {row["path"] for row in qa["figures"]} != {
        row["path"] for row in generation["figures"] if row["path"].endswith(".png")
    }:
        raise ValueError("Missing/incomplete visual inspection")
    for record in qa["figures"]:
        if ref(ROOT / record["path"]) != {key: record[key] for key in ("path", "sha256")}:
            raise ValueError("Figure changed since visual QA")
    if read_json(BASE / "final_coverage.json")["totals"]["percent_covered"] < 80:
        raise ValueError("CNN final coverage below 80%")
    for name in ("cpu_smoke.json", "demo/export.json"):
        if read_json(BASE / name)["status"] != "PASS":
            raise ValueError("CPU demo export incomplete")
    result.update(
        {
            "status": "PASS",
            "phase": 27,
            "visual_qa": ref(BASE / "visual_qa.json"),
            "coverage": ref(BASE / "final_coverage.json"),
            "test_policy": "3 evaluated seals, evaluation_count=1; audit reads saved predictions only",
        }
    )
    for required in (
        "docs/phase27_report.md",
        generation["manuscript"]["path"],
        "artifacts/manifests/phase27/trained_contract_registry.json",
    ):
        if not (ROOT / required).is_file():
            raise ValueError(f"Missing CNN handoff artifact: {required}")
    acceptance_path = BASE / "acceptance_verification.json"
    if acceptance_path.exists():
        result["at"] = read_json(acceptance_path)["at"]
    write_once(acceptance_path, result)
    candidates = {ROOT / p for p in SOURCE_FILES}
    for folder in (
        BASE,
        METRICS,
        MODELS,
        PREDICTIONS,
        ROOT / "artifacts/figures/phase27",
        ROOT / "experiments/notebooks/v3/ch03_cnn",
        ROOT / "tests/cnn",
    ):
        for path in folder.rglob("*"):
            if not path.is_file() or any(
                part.startswith(".") or part == "__pycache__" for part in path.relative_to(folder).parts
            ):
                continue
            if path.name in {
                "checkpoint.json",
                "active_controller.json",
                "verification.json",
                "experiment_lock.json",
            }:
                continue
            if path.suffix == ".tmp":
                raise ValueError("Unresolved temporary artifact before CNN release")
            candidates.add(path)
    candidates.update(ROOT.glob("scripts/*phase27*"))
    candidates.update(ROOT.glob("docs/phase27*.md"))
    candidates.update(ROOT.glob("report/sections/v3/ch03_cnn*.md"))
    candidates.add(ROOT / "tests/test_phase27_report_acceptance.py")
    files = [ref(path) for path in sorted(candidates) if path.is_file()]
    write_once(
        BASE / "experiment_lock.json",
        {
            "phase": 27,
            "status": "COMPLETE",
            "created_at": datetime.now(UTC).isoformat(),
            "source_fingerprint": result["code_sha256"],
            "files": files,
            "neural_runs": 27,
            "majority_runs": 9,
            "test_evaluation_count_per_dataset": 1,
            "acceptance": ref(BASE / "acceptance_verification.json"),
            "policy": "Immutable measured evidence; future edits require a versioned revision; no repeated TEST forward",
        },
    )
    audit = verify_lock()
    atomic_json(
        BASE / "checkpoint.json",
        {
            "phase": 27,
            "status": "COMPLETE",
            "stage": "released",
            "active_runner": None,
            "completed_runs": 36,
            "neural_runs": 27,
            "majority_runs": 9,
            "test_evaluation_executed": True,
            "test_evaluation_count_per_dataset": 1,
            "experiment_lock": audit["lock"],
            "next_phase": 28,
            "next_phase_note": "RNN validation only; joint RNN/LSTM TEST in Phase29",
            "docx_integration": "Phase34–35",
        },
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
