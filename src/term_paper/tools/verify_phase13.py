"""Independent verifier for Phase 13 graph artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from term_paper.tools.phase13_graph import read_jsonl, validate_evaluation_safety, validate_graph


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_phase13(workspace: Path) -> dict[str, Any]:
    base = workspace / "term_paper/knowledge_rag"
    manifest_path = base / "artifacts/manifests/phase13_graph_manifest.json"
    failures: list[str] = []
    checks: list[str] = []
    if not manifest_path.exists():
        return {"status": "FAIL", "checks": [], "failures": ["missing phase13_graph_manifest.json"]}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "checks": [], "failures": [f"invalid phase13_graph_manifest.json: {exc}"]}

    required = [
        base / "config/phase13.json",
        base / "graph_schema.md",
        base / "artifacts/metrics/phase13_graph_statistics.json",
        base / "artifacts/metrics/phase13_entity_link_audit.csv",
        base / "artifacts/figures/phase13/graph_schema.svg",
        base / "artifacts/figures/phase13/medical_sample_subgraph.svg",
        base / "artifacts/figures/phase13/finance_sample_subgraph.svg",
    ]
    for path in required:
        if not path.exists() or path.stat().st_size == 0:
            failures.append(f"missing or empty deliverable: {path.relative_to(workspace).as_posix()}")
    if not failures:
        checks.append("core deliverables present")

    domains = manifest.get("domains", [])
    if not domains:
        failures.append("manifest has no domains")
    for domain in domains:
        graph_dir = base / f"data/processed/phase13/{domain}"
        paths = {name: graph_dir / name for name in ("nodes.jsonl", "edges.jsonl", "graph.graphml", "adjacency.json")}
        if any(not path.exists() for path in paths.values()):
            failures.append(f"{domain}: incomplete graph export")
            continue
        try:
            nodes = read_jsonl(paths["nodes.jsonl"])
            edges = read_jsonl(paths["edges.jsonl"])
            graph_failures = validate_graph(nodes, edges)
            graph_failures.extend(validate_evaluation_safety(edges))
            failures.extend(f"{domain}: {item}" for item in graph_failures)
            adjacency = json.loads(paths["adjacency.json"].read_text(encoding="utf-8"))
            if set(adjacency.get("out", {})) != {node["node_id"] for node in nodes}:
                failures.append(f"{domain}: adjacency node set mismatch")
            root = ET.parse(paths["graph.graphml"]).getroot()
            ns = {"g": "http://graphml.graphdrawing.org/xmlns"}
            if len(root.findall(".//g:node", ns)) != len(nodes) or len(root.findall(".//g:edge", ns)) != len(edges):
                failures.append(f"{domain}: GraphML row counts mismatch")
            if not graph_failures:
                checks.append(f"{domain} schema/provenance/ID/dangling-edge validation PASS")
        except (OSError, ValueError, json.JSONDecodeError, ET.ParseError) as exc:
            failures.append(f"{domain}: unreadable graph export ({exc})")

    audit_path = base / "artifacts/metrics/phase13_entity_link_audit.csv"
    if audit_path.exists():
        try:
            with audit_path.open(encoding="utf-8", newline="") as handle:
                audit = list(csv.DictReader(handle))
            forced = [row for row in audit if row.get("decision") == "unresolved" and row.get("linked_qid")]
            if forced:
                failures.append("entity-link audit contains forced links for unresolved rows")
            else:
                checks.append("ambiguous/unresolved entity links are not forced")
        except OSError as exc:
            failures.append(f"cannot read entity-link audit: {exc}")

    for artifact in manifest.get("artifacts", []):
        relative = artifact.get("path", "")
        path = workspace / relative
        if not path.exists():
            failures.append(f"manifest artifact missing: {relative}")
            continue
        if "size_bytes" in artifact and path.stat().st_size != artifact["size_bytes"]:
            failures.append(f"manifest size mismatch: {relative}")
        if "sha256" in artifact and _sha256(path) != artifact["sha256"]:
            failures.append(f"manifest hash mismatch: {relative}")
    if manifest.get("artifacts"):
        checks.append("manifest artifact inventory validated")

    return {"status": "PASS" if not failures else "FAIL", "checks": checks, "failures": failures}


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    result = verify_phase13(workspace)
    output = workspace / "term_paper/knowledge_rag/artifacts/manifests/phase13_verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
