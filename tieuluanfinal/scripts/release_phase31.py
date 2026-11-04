"""Release-only closure over report/bibliography; frozen evaluator/auditor remain untouched."""

import argparse
from datetime import UTC, datetime

from scripts.phase31_benchmark import BASE, SOURCE_FILES
from scripts.verify_phase31 import audit_release, verify_lock, xml_count
from src.ch05_knowledge_rag.preservation import checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json


def merge_references(first, second):
    members = {}
    for record in first + second:
        key, digest = record["path"], record["sha256"]
        if key in members and members[key] != digest:
            raise ValueError("Conflicting release member hash")
        members[key] = digest
    if not members:
        raise ValueError("Empty release")
    return [{"path": key, "sha256": value} for key, value in sorted(members.items())]


def release():
    if (BASE / "experiment_lock.json").exists():
        raise ValueError("Release already exists; use --verify-only")
    result = audit_release()
    active = read_json(BASE / "active_report_r2.json")
    generation = read_json(checked(active["generation"]))
    if generation["manuscript"] != active["manuscript"] or generation["benchmark_modified"]:
        raise ValueError("Presentation overlay identity/scope mismatch")
    reviewed = read_json(BASE / "revisions/presentation_r2/visual_qa.json")
    expected_pngs = {r["path"] for r in generation["figures"] if r["path"].endswith(".png")}
    if (
        reviewed["status"] != "PASS"
        or set(reviewed["reviewed_pngs"]) != expected_pngs
        or len(expected_pngs) != 5
    ):
        raise ValueError("Active presentation overlay not fully reviewed")
    for reference in generation["files"]:
        checked(reference)
    result["tests"] = xml_count(
        [
            BASE / "pretest-tests.xml",
            BASE / "regression-tests.xml",
            BASE / "report-tests.xml",
            BASE / "packaging-tests-final.xml",
        ]
    )
    result["packaging"] = (
        "phase31.release.1; closes report references and bibliography beyond frozen benchmark source"
    )
    write_once(BASE / "verification.json", result)
    files = set()
    for folder in (
        BASE,
        ROOT / "data/processed/v3/phase31",
        ROOT / "artifacts/figures/phase31",
        ROOT / "artifacts/metrics/phase31",
        ROOT / "report/references/dataset_cards/v3_agent",
        ROOT / "experiments/notebooks/v3/ch06_multi_agent",
        ROOT / "tests/agents31_report",
    ):
        files.update(
            p
            for p in folder.rglob("*")
            if p.is_file()
            and not p.name.startswith(".")
            and "__pycache__" not in p.parts
            and p.name not in {"experiment_lock.json", "checkpoint.json"}
        )
    files.update(ROOT / p for p in SOURCE_FILES)
    files.update(
        ROOT / p
        for p in (
            "scripts/demo_phase31.py",
            "scripts/build_phase31.py",
            "scripts/check_phase31.ps1",
            "scripts/release_phase31.py",
            "docs/phase31_report.md",
            "docs/phase31_operations.md",
            "report/references/ch06_sources_v3.bib",
        )
    )
    exported = read_json(BASE / "report_generation.json")["files"] + generation["files"]
    members = merge_references([ref(p) for p in sorted(files)], exported)
    for record in members:
        checked(record)
    write_once(
        BASE / "experiment_lock.json",
        {
            "phase": 31,
            "version": "phase31.release.1",
            "files": members,
            "acceptance": ref(BASE / "verification.json"),
            "created_at": datetime.now(UTC).isoformat(),
        },
    )
    verify_lock()
    write_once(
        BASE / "checkpoint.json",
        {
            "phase": 31,
            "status": "COMPLETE",
            "controller_pid": None,
            "experiment_lock": ref(BASE / "experiment_lock.json"),
            "acceptance": ref(BASE / "verification.json"),
        },
    )
    print(result, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify_lock()
    else:
        release()


if __name__ == "__main__":
    main()
