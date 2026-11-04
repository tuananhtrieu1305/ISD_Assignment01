"""Acceptance verifier for Phase 12 preprocessing artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from term_paper.tools.phase12_preprocessing import validate_no_group_leakage


REQUIRED_PROCESSED = (
    "documents.jsonl",
    "chunks.jsonl",
    "queries.jsonl",
    "evidence.jsonl",
    "challenge_queries.jsonl",
    "medquad_filter_audit.jsonl",
    "duplicate_audit.jsonl",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify_phase12(workspace: Path) -> dict[str, Any]:
    base = workspace / "term_paper/knowledge_rag"
    processed = base / "data/processed/phase12"
    manifest_path = base / "artifacts/manifests/preprocessing_manifest.json"
    contract_path = base / "evaluation_contract.md"
    config_path = base / "config/phase12.json"
    manual_audit_path = base / "artifacts/metrics/phase12_diabetes_manual_audit.csv"
    audit_path = base / "artifacts/metrics/phase12_preprocessing_audit.json"
    failures: list[str] = []
    checks = 0

    checks += 1
    if not manifest_path.is_file():
        failures.append("Missing preprocessing_manifest.json")
        manifest: dict[str, Any] = {}
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    checks += len(REQUIRED_PROCESSED)
    for name in REQUIRED_PROCESSED:
        path = processed / name
        if not path.is_file():
            failures.append(f"Missing processed artifact: {name}")

    checks += 2
    if not contract_path.is_file():
        failures.append("Missing evaluation_contract.md")
    if not config_path.is_file():
        failures.append("Missing config/phase12.json")

    checks += 1
    if manifest:
        for record in manifest.get("artifacts", []):
            path = workspace / record["path"]
            if not path.is_file():
                failures.append(f"Manifest artifact missing: {record['path']}")
            elif path.stat().st_size != record["size_bytes"] or _sha256(path) != record["sha256"]:
                failures.append(f"Manifest mismatch: {record['path']}")
        if manifest.get("test_split_status") != "SEALED_NOT_USED_FOR_TUNING":
            failures.append("TEST split is not sealed against tuning")

    queries_path = processed / "queries.jsonl"
    checks += 1
    if queries_path.is_file():
        queries = _read_jsonl(queries_path)
        required = {"query_id", "domain", "dataset", "split", "question", "gold_document_ids", "gold_evidence_ids"}
        for row in queries:
            if not required.issubset(row):
                failures.append(f"Incomplete query schema: {row.get('query_id', 'UNKNOWN')}")
                break
        leaks = validate_no_group_leakage(queries)
        if leaks:
            failures.append(f"Cross-split group leakage: {leaks[:5]}")

    checks += 1
    documents_path = processed / "documents.jsonl"
    chunks_path = processed / "chunks.jsonl"
    evidence_path = processed / "evidence.jsonl"
    if documents_path.is_file() and chunks_path.is_file() and queries_path.is_file() and evidence_path.is_file():
        documents = _read_jsonl(documents_path)
        chunks = _read_jsonl(chunks_path)
        evidence = _read_jsonl(evidence_path)
        document_ids = [str(row.get("document_id")) for row in documents]
        chunk_ids = [str(row.get("chunk_id")) for row in chunks]
        query_ids = [str(row.get("query_id")) for row in queries]
        evidence_ids = [str(row.get("evidence_id")) for row in evidence]
        for label, values in (("document", document_ids), ("chunk", chunk_ids), ("query", query_ids), ("evidence", evidence_ids)):
            if len(values) != len(set(values)):
                failures.append(f"Duplicate {label} IDs")
        document_set, chunk_set, query_set, evidence_set = set(document_ids), set(chunk_ids), set(query_ids), set(evidence_ids)
        dangling_chunk_docs = [row.get("chunk_id") for row in chunks if row.get("document_id") not in document_set]
        if dangling_chunk_docs:
            failures.append(f"Chunks reference missing documents: {dangling_chunk_docs[:5]}")
        for row in queries:
            if row.get("answer_available"):
                if not row.get("gold_document_ids") or not row.get("gold_chunk_ids") or not row.get("gold_evidence_ids"):
                    failures.append(f"Answerable query lacks gold mapping: {row.get('query_id')}")
                    break
            missing_docs = set(row.get("gold_document_ids") or []) - document_set
            missing_chunks = set(row.get("gold_chunk_ids") or []) - chunk_set
            missing_evidence = set(row.get("gold_evidence_ids") or []) - evidence_set
            if missing_docs:
                failures.append(f"Query has dangling gold document: {row.get('query_id')}")
            if missing_chunks:
                failures.append(f"Query has dangling gold chunk: {row.get('query_id')}")
            if missing_evidence:
                failures.append(f"Query has dangling gold evidence: {row.get('query_id')}")
        for row in evidence:
            if row.get("query_id") not in query_set or row.get("document_id") not in document_set or row.get("chunk_id") not in chunk_set:
                failures.append(f"Dangling evidence relation: {row.get('evidence_id')}")
                break
        raw_hash_cache: dict[Path, str] = {}
        for row in documents:
            raw_path = workspace / str(row.get("raw_source_path", ""))
            if not raw_path.is_file():
                failures.append(f"Document raw source missing: {row.get('document_id')}")
                continue
            if raw_path not in raw_hash_cache:
                raw_hash_cache[raw_path] = _sha256(raw_path)
            if raw_hash_cache[raw_path] != row.get("raw_source_sha256"):
                failures.append(f"Document raw hash mismatch: {row.get('document_id')}")
                break

    checks += 1
    if not manual_audit_path.is_file():
        failures.append("Missing diabetes manual audit CSV")
    else:
        with manual_audit_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        reviewed = [row for row in rows if row.get("review_label") in {"TP", "FP", "TN", "FN"}]
        if len(reviewed) < 40:
            failures.append("Diabetes manual audit must contain at least 40 reviewed rows")
        positives = [row for row in reviewed if row["review_label"] in {"TP", "FP"}]
        precision = sum(row["review_label"] == "TP" for row in positives) / len(positives) if positives else 0.0
        minimum = 0.9
        if config_path.is_file():
            config = json.loads(config_path.read_text(encoding="utf-8"))
            minimum = float(config.get("manual_audit", {}).get("minimum_inclusion_precision", minimum))
        if precision < minimum:
            failures.append(f"Diabetes inclusion precision {precision:.3f} is below {minimum:.3f}")

    checks += 1
    if not audit_path.is_file():
        failures.append("Missing phase12_preprocessing_audit.json")
    else:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if audit.get("cross_split_group_leakage"):
            failures.append("Preprocessing audit reports cross-split leakage")
        if audit.get("test_tuning_performed") is not False:
            failures.append("Preprocessing audit does not prove TEST remained sealed")
        finqa = audit.get("finqa") or {}
        if finqa.get("gold_locator_missing"):
            failures.append("FinQA gold locator mapping is incomplete")
        if finqa.get("gold_text_token_mismatch_count") != 0:
            failures.append("FinQA gold evidence differs at token level")

    checks += 1
    challenge_path = processed / "challenge_queries.jsonl"
    if challenge_path.is_file():
        challenge = _read_jsonl(challenge_path)
        if len(challenge) < 16 or any(row.get("expected_behavior") != "abstain" for row in challenge):
            failures.append("Challenge set must contain at least 16 abstention queries")

    return {
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "failed_checks": len(failures),
        "failures": failures,
    }


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    result = verify_phase12(workspace)
    output = workspace / "term_paper/knowledge_rag/artifacts/manifests/phase12_verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
