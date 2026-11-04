"""Chapter5 immutable acceptance; all checks read saved artifacts, never a TEST evaluator."""

import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from src.ch05_knowledge_rag.catalog import validate_pipeline
from src.ch05_knowledge_rag.presentation_r2 import error_scope
from src.ch05_knowledge_rag.preservation import BASE, ROOT, SEAL, SEAL_SHA, checked, ref, verify_records
from src.ch05_knowledge_rag.reporting import historical_metrics
from src.common.artifact_core import write_once
from src.common.contracts import read_json, validate_document

SNAPSHOT_SHA = "481071f65b2c01b8d132532bdaccaa08ff760b153b908bbf1906e72d2f1c310a"


def validate_gate(export, totals, qa, figures):
    if (
        export["status"] != "PASS"
        or export["notebooks_executed"] != 3
        or export["qa_slots_executed"] != 10
        or export["wikidata_entities_inspected"] != 10
        or export["new_test_evaluation_executed"]
    ):
        raise ValueError("Real CPU export incomplete or TEST was rerun")
    if (
        not math.isfinite(totals["percent_covered"])
        or totals["percent_covered"] < 80
        or totals["num_statements"] < 100
    ):
        raise ValueError("Require nonempty actual coverage >=80%, never rounded display")
    expected = {r["path"] for r in figures if r["path"].endswith(".png")}
    actual = qa["reviewed_pngs"]
    if (
        len(expected) != 7
        or qa["status"] != "PASS"
        or set(actual) != expected
        or len(actual) != len(set(actual))
    ):
        raise ValueError("Visual QA must cover exact seven current PNGs")


def xml_tests(paths):
    keys = set()
    for path in paths:
        document = ET.parse(path).getroot()
        if any(
            int(row.get(key, 0))
            for row in document.iter("testsuite")
            for key in ("errors", "failures", "skipped")
        ):
            raise ValueError("Failed or skipped acceptance XML")
        cases = list(document.iter("testcase"))
        if not cases:
            raise ValueError("Empty test evidence")
        for case in cases:
            key = (case.get("classname"), case.get("name"))
            if key in keys or any(case.find(name) is not None for name in ("failure", "error", "skipped")):
                raise ValueError("Duplicate/failed/skipped test evidence")
            keys.add(key)
    return len(keys)


def audit():
    snapshot_path = checked(
        {"path": "artifacts/manifests/phase30/preserved_snapshot.json", "sha256": SNAPSHOT_SHA}
    )
    snapshot = read_json(snapshot_path)
    print("Phase30 audit: verifying11490 preserved assets (no inference)", flush=True)
    preserved = verify_records(snapshot["files"])
    if preserved != 11490 or snapshot["baseline"] != {
        "raw": 11345,
        "config": 7,
        "metric": 23,
        "sealed_predictions": 10,
        "test_run_count": 1,
    }:
        raise ValueError("Preservation snapshot identity/count mismatch")
    dependencies = []
    for record in snapshot["dependencies"]:
        lock = read_json(checked(record))
        count = verify_records(lock["files"])
        if count != record["verified_files"]:
            raise ValueError("Dependency lock member count changed")
        dependencies.append({"path": record["path"], "verified_files": count})
    checked({"path": SEAL, "sha256": SEAL_SHA})
    metrics = historical_metrics()
    scope = error_scope()
    if metrics != read_json(BASE / "historical_consistency.json") or scope != read_json(
        BASE / "revisions/presentation_r2/error_scope.json"
    ):
        raise ValueError("Saved evidence consistency changed")
    active = read_json(BASE / "active_report.json")
    generation = read_json(checked(active["generation"]))
    if active["revision"] != "presentation_r2" or active["manuscript"] != generation["manuscript"]:
        raise ValueError("Current report pointer mismatch")
    export = read_json(BASE / "export.json")
    verify_records(export["artifacts"])
    for record in generation["figures"] + [generation["manuscript"]]:
        checked(record)
    legacy_docs = read_json(checked(generation["preserved_docs"]))
    verify_records(legacy_docs["files"])
    qa = read_json(BASE / "visual_qa.json")
    checked(qa["generation"])
    if qa["generation"] != active["generation"]:
        raise ValueError("Visual QA belongs to another report")
    coverage_path = BASE / "final_coverage_r2.json"
    totals = read_json(coverage_path)["totals"]
    validate_gate(export, totals, qa, generation["figures"])
    registry = read_json(BASE / "reused_registry.json")
    if (
        len(registry["models"]) != 15
        or sum(r["available"] for r in registry["models"]) != 10
        or registry["initialized_registry_replaced"]
    ):
        raise ValueError("Reused/structural registry mismatch")
    for row in registry["models"]:
        validate_pipeline(read_json(checked(row["contract"])))
    tabs = read_json(BASE / "catalog.json")
    validate_document("api#chapter", tabs["chapter"])
    old = (ROOT / "report/sections/05_knowledge_rag.md").read_text(encoding="utf-8")
    current = checked(active["manuscript"]).read_text(encoding="utf-8")
    if set(re.findall(r"@([A-Za-z0-9_-]+)", old)) != set(re.findall(r"@([A-Za-z0-9_-]+)", current)):
        raise ValueError("Original literature citation keys changed")
    for name in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", current):
        image = (checked(active["manuscript"]).parent / name).resolve()
        if not image.is_relative_to(ROOT) or not image.is_file():
            raise ValueError("Broken manuscript image reference")
    for name in (
        "docs/phase30_report.md",
        "docs/phase30_operations.md",
        "docs/phase30_contract_extension.md",
        "docs/phase30_presentation_revision_r2.md",
    ):
        if not (ROOT / name).is_file():
            raise ValueError("Missing handoff document")
    tests = [BASE / "final-tests-r2.xml", BASE / "regression-tests.xml"]
    count = xml_tests(tests)
    return {
        "phase": 30,
        "status": "PASS",
        "preserved_files": preserved,
        "snapshot": ref(snapshot_path),
        "dependencies": dependencies,
        "tests": count,
        "skipped": 0,
        "test_evidence": [ref(p) for p in tests],
        "coverage_percent": totals["percent_covered"],
        "coverage": ref(coverage_path),
        "historical_predictions_audited": 6045,
        "test_run_count": 1,
        "manuscript": active["manuscript"],
        "current_generation": active["generation"],
        "visual_qa": ref(BASE / "visual_qa.json"),
        "new_test_evaluation_executed": False,
    }


def verify_lock():
    path = BASE / "experiment_lock.json"
    document = read_json(path)
    if (
        document["phase"] != 30
        or document["status"] != "COMPLETE"
        or document["new_test_evaluation_executed"]
    ):
        raise ValueError("Invalid Phase30 release")
    count = verify_records(document["files"])
    return {
        "phase": 30,
        "status": "PASS",
        "locked_files": count,
        "lock": ref(path),
        "new_test_evaluation_executed": False,
    }


def release():
    result = audit()
    write_once(BASE / "verification.json", result)
    print("Phase30 audit PASS; creating immutable release lock", flush=True)
    snapshot = read_json(BASE / "preserved_snapshot.json")
    candidates = {ROOT / r["path"] for r in snapshot["files"]}
    for folder in (
        "artifacts/manifests/phase30",
        "artifacts/figures/phase30",
        "src/ch05_knowledge_rag",
        "tests/kg30",
        "experiments/notebooks/v3/ch05_knowledge_rag",
    ):
        directory = ROOT / folder
        for path in directory.rglob("*"):
            if not path.is_file() or any(
                part.startswith(".") or part == "__pycache__" for part in path.relative_to(directory).parts
            ):
                continue
            if path.name in {"checkpoint.json", "experiment_lock.json"}:
                continue
            candidates.add(path)
    for pattern in (
        "scripts/*phase30*",
        "docs/phase30*.md",
        "report/sections/v3/ch05_knowledge_rag*.md",
        "docs/ch5/*.md",
        "experiments/configs/v3/phase30*.ini",
    ):
        candidates.update(p for p in ROOT.glob(pattern) if p.is_file())
    # Lock the dependency content, not only their manifest file identity.
    for row in snapshot["dependencies"]:
        candidates.update(ROOT / r["path"] for r in read_json(checked(row))["files"])
    records = [ref(p) for p in sorted(candidates)]
    lock = {
        "phase": 30,
        "status": "COMPLETE",
        "created_at": datetime.now(UTC).isoformat(),
        "scope": "Chapter5 V3 integration and saved-output regression; historical TEST run_count stays1",
        "acceptance": ref(BASE / "verification.json"),
        "files": records,
        "new_test_evaluation_executed": False,
        "historical_test_run_count": 1,
        "policy": "Immutable source/evidence/report; changes require versioned revision. No public TEST rerun/tuning, legacy reserialization or raw overwrite",
    }
    write_once(BASE / "experiment_lock.json", lock)
    verified = verify_lock()
    from src.ch02_ml.test_gate import atomic_json

    atomic_json(
        BASE / "checkpoint.json",
        {
            "phase": 30,
            "status": "COMPLETE",
            "stage": "released",
            "experiment_lock": verified["lock"],
            "test_run_count": 1,
            "new_test_evaluation_executed": False,
            "next_phase": 31,
            "http_ui_integration": "Phase32–33",
            "docx_integration": "Phase34–35",
        },
    )
    return verified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if (BASE / "experiment_lock.json").exists():
        result = verify_lock()
    elif args.verify_only or not args.lock:
        raise ValueError("No final release; --lock only after all acceptance gates")
    else:
        result = release()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
