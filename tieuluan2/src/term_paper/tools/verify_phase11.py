"""Verify Phase 11 source snapshots and provenance artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from term_paper.tools.phase11_data import aggregate_manifest_sha256, validate_raw_manifest


REQUIRED_CARDS = ("ch5_medquad.md", "ch5_finqa.md", "ch5_wikidata.md")
REQUIRED_DATASETS = {"medquad", "finqa", "wikidata"}


def verify_phase11(workspace: Path) -> dict[str, Any]:
    manifest_path = workspace / "term_paper/knowledge_rag/artifacts/manifests/raw_manifest.csv"
    snapshot_path = workspace / "term_paper/knowledge_rag/artifacts/manifests/phase11_snapshot_manifest.json"
    audit_path = workspace / "term_paper/knowledge_rag/artifacts/metrics/phase11_data_audit.json"
    registry_path = workspace / "term_paper/sources/source_registry.csv"
    references_path = workspace / "term_paper/report/references_ordered.md"
    card_root = workspace / "term_paper/sources/dataset_cards"
    failures: list[str] = []
    checks = 0

    rows: list[dict[str, str]] = []
    checks += 1
    if not manifest_path.is_file():
        failures.append("Missing raw_manifest.csv")
    else:
        with manifest_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        failures.extend(validate_raw_manifest(workspace, rows))
        if {row.get("dataset_id") for row in rows} != REQUIRED_DATASETS:
            failures.append("raw_manifest.csv must cover medquad, finqa and wikidata")

    checks += 1
    if not snapshot_path.is_file():
        failures.append("Missing phase11_snapshot_manifest.json")
    else:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if rows and snapshot.get("aggregate_manifest_sha256") != aggregate_manifest_sha256(rows):
            failures.append("Aggregate raw manifest SHA-256 mismatch")
        sources = snapshot.get("sources") or {}
        for dataset_id in REQUIRED_DATASETS:
            source = sources.get(dataset_id) or {}
            if not source.get("official_url") or not source.get("license"):
                failures.append(f"Incomplete provenance for {dataset_id}")
        if not (sources.get("medquad") or {}).get("commit_sha"):
            failures.append("MedQuAD commit SHA missing")
        if not (sources.get("finqa") or {}).get("commit_sha"):
            failures.append("FinQA commit SHA missing")
        if not (sources.get("wikidata") or {}).get("revision_ids"):
            failures.append("Wikidata revision IDs missing")

    checks += 1
    if not audit_path.is_file():
        failures.append("Missing phase11_data_audit.json")
    else:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if audit.get("medquad", {}).get("removed_answers_recovered") is not False:
            failures.append("MedQuAD removed-answer policy is not locked")
        if audit.get("wikidata", {}).get("acquisition_mode") != "narrow_entity_snapshots":
            failures.append("Wikidata must use narrow entity snapshots, not a full dump")

    checks += len(REQUIRED_CARDS)
    for name in REQUIRED_CARDS:
        if not (card_root / name).is_file():
            failures.append(f"Missing dataset card: {name}")

    checks += 1
    if not registry_path.is_file():
        failures.append("Missing source_registry.csv")
    else:
        registry = registry_path.read_text(encoding="utf-8")
        for dataset_id in ("ch5_medquad", "ch5_finqa", "ch5_wikidata"):
            if dataset_id not in registry:
                failures.append(f"Registry entry missing: {dataset_id}")

    checks += 1
    if not references_path.is_file():
        failures.append("Missing references_ordered.md")
    else:
        references = references_path.read_text(encoding="utf-8")
        for marker in ("MedQuAD", "FinQA", "Wikidata"):
            if marker not in references:
                failures.append(f"Reference missing: {marker}")

    return {
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "failed_checks": len(failures),
        "failures": failures,
    }


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    result = verify_phase11(workspace)
    output = workspace / "term_paper/knowledge_rag/artifacts/manifests/phase11_verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
