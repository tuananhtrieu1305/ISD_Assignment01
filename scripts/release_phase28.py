"""Immutable validation-only RNN handoff; does not own or open TEST."""

import argparse
import json
from datetime import UTC, datetime

from scripts.verify_phase27 import test_count
from scripts.verify_phase28 import verify
from src.ch02_ml.test_gate import atomic_json
from src.ch04_rnn_lstm.protocol import BASE, METRICS, MODELS, PREDICTIONS, ROOT, SOURCE_FILES, checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import read_json


def verify_lock():
    lock = read_json(BASE / "experiment_lock.json")
    for row in lock["files"]:
        checked(row)
    return {
        "status": "PASS",
        "locked_files": len(lock["files"]),
        "lock": ref(BASE / "experiment_lock.json"),
        "test_evaluation_executed": False,
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
        raise ValueError("No validation release lock yet; use --lock only after acceptance/visual QA")
    result = verify()
    test_files = (
        "rnn-tests.xml",
        "keras-final-tests.xml",
        "regression-tests.xml",
        "preservation-tests.xml",
        "report-tests.xml",
        "powershell-entrypoint-green-tests.xml",
    )
    result["tests"] = {name: test_count(BASE / name) for name in test_files}
    result["test_evidence"] = [ref(BASE / name) for name in test_files]
    coverage = read_json(BASE / "final_coverage.json")
    if coverage["totals"]["percent_covered"] < 80:
        raise ValueError("Recurrent coverage below 80%")
    result["coverage_percent"] = coverage["totals"]["percent_covered"]
    result["coverage"] = ref(BASE / "final_coverage.json")
    generation = read_json(BASE / "report_generation.json")
    qa = read_json(BASE / "visual_qa.json")
    if generation["status"] != "PASS" or qa["status"] != "PASS" or generation["test_evaluation_executed"]:
        raise ValueError("Report/visual QA incomplete")
    for record in [generation["manuscript"], *generation["figures"], *generation["tables"]]:
        checked(record)
    expected_png = {r["path"] for r in generation["figures"] if r["path"].endswith(".png")}
    if expected_png != {r["path"] for r in qa["figures"]}:
        raise ValueError("Visual QA set incomplete")
    for record in qa["figures"]:
        checked({key: record[key] for key in ("path", "sha256")})
    if (
        read_json(BASE / "cpu_smoke.json")["status"] != "PASS"
        or read_json(BASE / "demo/export.json")["status"] != "PASS"
    ):
        raise ValueError("CPU export incomplete")
    for required in (
        "docs/phase28_report.md",
        "docs/phase28_operations.md",
        "artifacts/manifests/phase28/trained_validation_registry.json",
        "artifacts/manifests/phase28/holdout_handoff.json",
    ):
        if not (ROOT / required).is_file():
            raise ValueError("Missing RNN handoff artifact: " + required)
    result["at"] = datetime.now(UTC).isoformat()
    acceptance = BASE / "acceptance_verification.json"
    if acceptance.exists():
        result["at"] = read_json(acceptance)["at"]
    write_once(acceptance, result)
    candidates = {ROOT / name for name in SOURCE_FILES}
    for folder in (
        BASE,
        METRICS,
        MODELS,
        PREDICTIONS,
        ROOT / "artifacts/figures/phase28",
        ROOT / "experiments/notebooks/v3/ch04_rnn",
        ROOT / "tests/recurrent",
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
                raise ValueError("Unresolved temporary file in validation release")
            candidates.add(path)
    candidates.update(ROOT.glob("scripts/*phase28*"))
    candidates.add(ROOT / "scripts/phase28_r2.py")
    candidates.add(ROOT / "src/ch04_rnn_lstm/export_r2.py")
    candidates.update(ROOT.glob("docs/phase28*.md"))
    candidates.update(ROOT.glob("report/sections/v3/ch04_rnn*.md"))
    candidates.add(ROOT / "tests/test_phase28_report_acceptance.py")
    candidates.add(ROOT / "tests/powershell/test_phase28_entrypoints.ps1")
    files = [ref(path) for path in sorted(candidates) if path.is_file()]
    write_once(
        BASE / "experiment_lock.json",
        {
            "phase": 28,
            "status": "COMPLETE",
            "scope": "RNN validation only",
            "created_at": datetime.now(UTC).isoformat(),
            "source_fingerprint": result["code_sha256"],
            "files": files,
            "neural_runs": 108,
            "main_neural_runs": 27,
            "rolling_neural_runs": 81,
            "baseline_runs": 24,
            "test_evaluation_count": 0,
            "test_owner_phase": 29,
            "acceptance": ref(acceptance),
            "policy": "Immutable validation evidence; any edit needs a versioned revision; joint RNN/LSTM TEST deferred to Phase29",
        },
    )
    audit = verify_lock()
    atomic_json(
        BASE / "checkpoint.json",
        {
            "phase": 28,
            "status": "COMPLETE",
            "stage": "released_validation_only",
            "active_runner": None,
            "completed_runs": 132,
            "main_neural_runs": 27,
            "rolling_neural_runs": 81,
            "baseline_runs": 24,
            "test_evaluation_executed": False,
            "experiment_lock": audit["lock"],
            "next_phase": 29,
            "next_phase_note": "Implement LSTM on identical data/budget, lock both families before joint one-shot TEST",
            "docx_integration": "Phase34–35",
        },
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
