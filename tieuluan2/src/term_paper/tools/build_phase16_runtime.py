"""Build a compact, deterministic KG-RAG package for the Render backend."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from term_paper.tools.phase13_graph import normalize_label


ARTIFACT_BUDGET_BYTES = 192 * 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _gzip_text(path: Path, lines: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="\n") as text:
                for line in lines:
                    text.write(line)


def compact_graph_map(
    domain: str,
    nodes: Sequence[Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Collapse the property graph to lexical anchors and reachable chunks."""
    node_map = {str(node["node_id"]): node for node in nodes}
    chunks_by_owner: dict[str, set[str]] = defaultdict(set)
    describes: list[tuple[str, str]] = []
    mentions: list[tuple[str, str]] = []
    reports_by_company: dict[str, set[str]] = defaultdict(set)
    pages_by_report: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        source, target = str(edge["source_id"]), str(edge["target_id"])
        edge_type = edge.get("edge_type")
        if edge_type == "HAS_CHUNK":
            chunk = node_map.get(target, {})
            if chunk.get("node_type") == "Chunk" and chunk.get("source_id"):
                chunks_by_owner[source].add(str(chunk["source_id"]))
        elif edge_type == "DESCRIBES":
            describes.append((source, target))
        elif edge_type == "MENTIONS":
            mentions.append((source, target))
        elif edge_type == "HAS_REPORT":
            reports_by_company[source].add(target)
        elif edge_type == "HAS_PAGE":
            pages_by_report[source].add(target)

    anchors: dict[str, dict[str, Any]] = {}

    def add_anchor(node_id: str, chunk_ids: Iterable[str]) -> None:
        node = node_map.get(node_id, {})
        key = normalize_label(node.get("label"))
        values = sorted(set(chunk_ids))
        if not key or not values:
            return
        existing = anchors.setdefault(
            key,
            {"label": str(node.get("label", key)), "node_id": node_id, "chunk_ids": []},
        )
        existing["chunk_ids"] = sorted(set(existing["chunk_ids"]) | set(values))

    if domain == "medical":
        for document_id, entity_id in describes:
            if node_map.get(entity_id, {}).get("node_type") == "MedicalEntity":
                add_anchor(entity_id, chunks_by_owner.get(document_id, set()))
    elif domain == "finance":
        for chunk_node_id, concept_id in mentions:
            chunk = node_map.get(chunk_node_id, {})
            if chunk.get("node_type") == "Chunk" and chunk.get("source_id"):
                add_anchor(concept_id, [str(chunk["source_id"])])
        for company_id, report_ids in reports_by_company.items():
            company_chunks: set[str] = set()
            for report_id in report_ids:
                for page_id in pages_by_report.get(report_id, set()):
                    company_chunks.update(chunks_by_owner.get(page_id, set()))
            add_anchor(company_id, company_chunks)
    else:
        raise ValueError("domain must be medical or finance")
    return dict(sorted(anchors.items()))


def build_runtime(workspace: Path) -> dict[str, Any]:
    workspace = Path(workspace)
    base = workspace / "term_paper/knowledge_rag"
    output = workspace / "backend/models"
    phase14 = json.loads((base / "config/phase14.json").read_text(encoding="utf-8"))
    phase15_locked_path = base / "config/phase15_locked.json"
    phase15_locked = json.loads(phase15_locked_path.read_text(encoding="utf-8"))
    test_run_path = base / "artifacts/manifests/phase15_test_run.json"
    test_run = json.loads(test_run_path.read_text(encoding="utf-8"))
    if test_run.get("status") != "COMPLETE" or test_run.get("run_count") != 1:
        raise RuntimeError("Phase 15 public TEST must be complete exactly once before packaging")

    chunks_path = output / "kg_chunks.jsonl.gz"
    chunk_rows = read_jsonl(base / "data/processed/phase12/chunks.jsonl")
    reduced = (
        json.dumps(
            {key: row[key] for key in ("chunk_id", "document_id", "domain", "text")},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ) + "\n"
        for row in sorted(chunk_rows, key=lambda value: value["chunk_id"])
    )
    _gzip_text(chunks_path, reduced)

    graph_payload: dict[str, Any] = {}
    for domain in ("medical", "finance"):
        graph_dir = base / f"data/processed/phase13/{domain}"
        graph_payload[domain] = compact_graph_map(
            domain, read_jsonl(graph_dir / "nodes.jsonl"), read_jsonl(graph_dir / "edges.jsonl")
        )
    graph_path = output / "kg_graph_anchors.json.gz"
    graph_json = json.dumps(graph_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    _gzip_text(graph_path, [graph_json])

    indexes: dict[str, dict[str, str]] = {}
    for domain in ("medical", "finance"):
        indexes[domain] = {}
        for kind, source_name in (("sparse", "bm25.joblib"), ("dense", "dense_lsa.joblib")):
            relative = f"kg_{domain}_{source_name}"
            target = output / relative
            shutil.copyfile(base / f"data/processed/phase14/indexes/{domain}/{source_name}", target)
            indexes[domain][kind] = relative

    artifact_paths = [chunks_path, graph_path]
    artifact_paths.extend(output / relative for values in indexes.values() for relative in values.values())
    total = sum(path.stat().st_size for path in artifact_paths)
    if total > ARTIFACT_BUDGET_BYTES:
        raise RuntimeError(f"Runtime package {total} bytes exceeds {ARTIFACT_BUDGET_BYTES}-byte budget")
    locked_hash = sha256_file(phase15_locked_path)
    serialization_versions = {
        domain: json.loads(
            (base / f"data/processed/phase14/indexes/{domain}/cache_manifest.json").read_text(encoding="utf-8")
        ).get("libraries", {})
        for domain in ("medical", "finance")
    }
    manifest = {
        "schema_version": 1,
        "artifact_version": f"phase16-b4-{locked_hash[:12]}",
        "generated_at": "2026-10-13T00:00:00+07:00",
        "artifact_budget_bytes": ARTIFACT_BUDGET_BYTES,
        "phase15_locked_config_sha256": locked_hash,
        "phase15_test_run_sha256": sha256_file(test_run_path),
        "private_test_included": False,
        "external_api_required": False,
        "runtime_contract": {
            "python_builder": ".".join(str(value) for value in sys.version_info[:3]),
            "index_serialization_versions": serialization_versions,
            "deploy_scikit_learn": "1.9.1",
            "compatibility_note": "Indexes are read-only; deploy smoke is required across the pinned minor version.",
        },
        "allowed_tools": ["finance_retriever", "medical_retriever"],
        "chunks_file": chunks_path.relative_to(output).as_posix(),
        "graph_file": graph_path.relative_to(output).as_posix(),
        "indexes": indexes,
        "retrieval": {
            "model": "B4",
            "candidate_depth": 100,
            "top_k": 10,
            "rrf_k": 60,
            "max_hops": phase15_locked["selected_max_hops"],
            "weights": phase15_locked["selected_weights"],
        },
        "answer_layer": phase14["answer_layer"],
        "counts": {
            "chunks": {domain: sum(row["domain"] == domain for row in chunk_rows) for domain in ("medical", "finance")},
            "graph_anchors": {domain: len(graph_payload[domain]) for domain in ("medical", "finance")},
        },
        "files": [
            {
                "path": path.relative_to(output).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in sorted(artifact_paths)
        ],
        "package_bytes": total,
    }
    (output / "kg_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(build_runtime(root), ensure_ascii=False, indent=2))
