"""Build the two deterministic, offline Phase 13 knowledge graphs."""

from __future__ import annotations

import csv
import gc
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping
from xml.sax.saxutils import escape

from term_paper.tools.phase13_graph import (
    build_adjacency,
    extract_financial_concepts,
    graph_stats,
    link_wikidata,
    make_edge,
    make_node,
    make_provenance,
    normalize_label,
    shortest_path,
    validate_graph,
    write_graphml,
    write_jsonl,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


class GraphCollector:
    def __init__(self, domain: str) -> None:
        self.domain = domain
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, Any]] = {}

    def add_node(self, node: dict[str, Any]) -> dict[str, Any]:
        old = self.nodes.get(node["node_id"])
        if old is not None and old != node:
            raise ValueError(f"Conflicting node definition: {node['node_id']}")
        self.nodes[node["node_id"]] = node
        return node

    def add_edge(self, edge: dict[str, Any]) -> dict[str, Any]:
        old = self.edges.get(edge["edge_id"])
        if old is not None and old != edge:
            raise ValueError(f"Conflicting edge definition: {edge['edge_id']}")
        self.edges[edge["edge_id"]] = edge
        return edge

    def sorted_rows(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        return (
            sorted(self.nodes.values(), key=lambda row: row["node_id"]),
            sorted(self.edges.values(), key=lambda row: row["edge_id"]),
        )


def _raw_hashes(workspace: Path) -> dict[str, str]:
    path = workspace / "term_paper/knowledge_rag/artifacts/manifests/raw_manifest.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["relative_path"]: row["sha256"] for row in csv.DictReader(handle)}


def _row_provenance(
    row: Mapping[str, Any],
    record_id: str,
    raw_hashes: Mapping[str, str],
    extractor: str,
    fallback: Mapping[str, Any] | None = None,
    confidence: float = 1.0,
) -> dict[str, Any]:
    source_path = str(row.get("raw_source_path") or (fallback or {}).get("raw_source_path") or "")
    source_hash = str(row.get("raw_source_sha256") or raw_hashes.get(source_path) or (fallback or {}).get("raw_source_sha256") or "")
    return make_provenance(record_id, source_path, source_hash, extractor, confidence)


def _config_provenance(
    source_record_id: str, config_relative: str, config_hash: str, extractor: str, confidence: float = 1.0
) -> dict[str, Any]:
    return make_provenance(source_record_id, config_relative, config_hash, extractor, confidence)


def _load_wikidata_nodes(
    collector: GraphCollector,
    workspace: Path,
    domain: str,
    extractor: str,
) -> dict[str, dict[str, Any]]:
    raw_root = workspace / "term_paper/knowledge_rag/data/raw"
    snapshot_path = raw_root / "wikidata/snapshot_index.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    result: dict[str, dict[str, Any]] = {}
    for item in sorted(snapshot["entities"], key=lambda row: row["qid"]):
        if item["domain"] != domain:
            continue
        qid = item["qid"]
        source_path = (raw_root / item["entity_relative_path"]).relative_to(workspace).as_posix()
        provenance = make_provenance(qid, source_path, item["entity_sha256"], extractor, 1.0)
        node = make_node(
            domain,
            "WikidataEntity",
            f"wikidata:{qid}",
            item["label_en"],
            provenance,
            qid=qid,
            revision_id=item["revision_id"],
            modified=item["modified"],
            description=item["description_en"],
        )
        result[qid] = collector.add_node(node)
    return result


def _audit_and_link(
    collector: GraphCollector,
    local_nodes: Iterable[dict[str, Any]],
    wiki_nodes: Mapping[str, dict[str, Any]],
    rules: list[dict[str, Any]],
    config_relative: str,
    config_hash: str,
    extractor: str,
) -> list[dict[str, Any]]:
    audit: list[dict[str, Any]] = []
    for node in sorted(local_nodes, key=lambda row: row["node_id"]):
        decision = link_wikidata(node["label"], rules)
        linked_qid = decision["linked_qid"]
        if linked_qid and linked_qid in wiki_nodes:
            provenance = _config_provenance(
                f"{node['node_id']}:{linked_qid}", config_relative, config_hash, extractor, decision["confidence"]
            )
            collector.add_edge(
                make_edge(
                    collector.domain,
                    "SAME_AS",
                    node["node_id"],
                    wiki_nodes[linked_qid]["node_id"],
                    f"{node['stable_key']}:{linked_qid}",
                    provenance,
                    link_method=decision["method"],
                )
            )
        audit.append(
            {
                "domain": collector.domain,
                "local_node_id": node["node_id"],
                "local_label": node["label"],
                "candidate_qids": "|".join(decision["candidate_qids"]),
                "decision": decision["decision"],
                "linked_qid": linked_qid or "",
                "method": decision["method"],
                "confidence": f"{decision['confidence']:.3f}",
                "rationale": decision["rationale"],
                "source_record_id": node["provenance"]["source_record_id"],
            }
        )
    return audit


def build_medical(
    workspace: Path, config: dict[str, Any], raw_hashes: dict[str, str], config_hash: str
) -> tuple[GraphCollector, list[dict[str, Any]], list[str]]:
    base = workspace / "term_paper/knowledge_rag"
    phase12 = base / "data/processed/phase12"
    extractor = config["extractor_version"]
    collector = GraphCollector("medical")
    documents = [row for row in read_jsonl(phase12 / "documents.jsonl") if row["domain"] == "medical"]
    doc_by_id = {row["document_id"]: row for row in documents}
    doc_nodes: dict[str, dict[str, Any]] = {}
    entity_nodes: dict[str, dict[str, Any]] = {}
    question_type_nodes: dict[str, dict[str, Any]] = {}

    for document in sorted(documents, key=lambda row: row["document_id"]):
        provenance = _row_provenance(document, document["document_id"], raw_hashes, extractor)
        doc_node = collector.add_node(
            make_node(
                "medical", "Document", document["document_id"], document["title"], provenance,
                source_id=document["document_id"], split=document["split"], group_id=document["group_id"], dataset="medquad",
            )
        )
        doc_nodes[document["document_id"]] = doc_node
        entity_key = document["group_id"]
        if entity_key not in entity_nodes:
            entity_nodes[entity_key] = collector.add_node(
                make_node(
                    "medical", "MedicalEntity", entity_key, document["title"], provenance,
                    source_group_id=entity_key, extraction="medquad_focus_metadata",
                )
            )
        entity = entity_nodes[entity_key]
        collector.add_edge(
            make_edge("medical", "DESCRIBES", doc_node["node_id"], entity["node_id"], document["document_id"], provenance)
        )
        question_type = str(document.get("metadata", {}).get("question_type") or "unknown")
        qt_key = normalize_label(question_type)
        if qt_key not in question_type_nodes:
            question_type_nodes[qt_key] = collector.add_node(
                make_node("medical", "QuestionType", qt_key, question_type, provenance, extraction="medquad_question_type_metadata")
            )
        qt_node = question_type_nodes[qt_key]
        collector.add_edge(
            make_edge(
                "medical", "HAS_QUESTION_TYPE", doc_node["node_id"], qt_node["node_id"],
                f"{document['document_id']}:{qt_key}", provenance,
            )
        )

    for chunk in read_jsonl(phase12 / "chunks.jsonl"):
        if chunk["domain"] != "medical":
            continue
        document = doc_by_id[chunk["document_id"]]
        provenance = _row_provenance(document, chunk["chunk_id"], raw_hashes, extractor)
        node = collector.add_node(
            make_node(
                "medical", "Chunk", chunk["chunk_id"], f"{document['title']} — chunk {chunk['chunk_index']}", provenance,
                source_id=chunk["chunk_id"], document_id=chunk["document_id"], split=chunk["split"],
                chunk_index=chunk["chunk_index"], word_count=chunk["word_count"],
            )
        )
        collector.add_edge(
            make_edge("medical", "HAS_CHUNK", doc_nodes[chunk["document_id"]]["node_id"], node["node_id"], chunk["chunk_id"], provenance)
        )

    for query in read_jsonl(phase12 / "queries.jsonl"):
        if query["domain"] != "medical":
            continue
        fallback = doc_by_id.get(query.get("gold_document_ids", [None])[0], {}) if query.get("gold_document_ids") else {}
        provenance = _row_provenance(query, query["query_id"], raw_hashes, extractor, fallback)
        qnode = collector.add_node(
            make_node(
                "medical", "Question", query["query_id"], query["question"], provenance,
                source_id=query["query_id"], split=query["split"], group_id=query["group_id"], answer_available=query["answer_available"],
            )
        )
        question_text = f" {normalize_label(query['question'])} "
        matches = [
            (len(normalize_label(entity["label"])), entity)
            for entity in entity_nodes.values()
            if normalize_label(entity["label"]) and f" {normalize_label(entity['label'])} " in question_text
        ]
        if matches:
            longest = max(length for length, _ in matches)
            for _, entity in sorted((item for item in matches if item[0] == longest), key=lambda item: item[1]["node_id"]):
                collector.add_edge(
                    make_edge(
                        "medical", "ASKS_ABOUT", qnode["node_id"], entity["node_id"],
                        f"{query['query_id']}:{entity['stable_key']}", provenance,
                        extraction="longest_exact_normalized_phrase_from_question",
                    )
                )

    wiki_nodes = _load_wikidata_nodes(collector, workspace, "medical", extractor)
    audit = _audit_and_link(
        collector, entity_nodes.values(), wiki_nodes, config["medical"]["wikidata_rules"],
        "term_paper/knowledge_rag/config/phase13.json", config_hash, extractor,
    )
    nodes, edges = collector.sorted_rows()
    linked_entities = {edge["source_id"] for edge in edges if edge["edge_type"] == "SAME_AS"}
    sample_doc = next(
        (edge["source_id"] for edge in edges if edge["edge_type"] == "DESCRIBES" and edge["target_id"] in linked_entities),
        next(edge["source_id"] for edge in edges if edge["edge_type"] == "DESCRIBES"),
    )
    same_as_targets = {edge["source_id"]: edge["target_id"] for edge in edges if edge["edge_type"] == "SAME_AS"}
    describes_target = next(edge["target_id"] for edge in edges if edge["edge_type"] == "DESCRIBES" and edge["source_id"] == sample_doc)
    sample_goal = same_as_targets.get(describes_target, describes_target)
    path = shortest_path(build_adjacency(nodes, edges), sample_doc, sample_goal, 3)
    return collector, audit, path


def build_finance(
    workspace: Path, config: dict[str, Any], raw_hashes: dict[str, str], config_hash: str
) -> tuple[GraphCollector, list[dict[str, Any]], list[str]]:
    base = workspace / "term_paper/knowledge_rag"
    phase12 = base / "data/processed/phase12"
    extractor = config["extractor_version"]
    collector = GraphCollector("finance")
    documents = [row for row in read_jsonl(phase12 / "documents.jsonl") if row["domain"] == "finance"]
    doc_by_id = {row["document_id"]: row for row in documents}
    doc_nodes: dict[str, dict[str, Any]] = {}
    company_nodes: dict[str, dict[str, Any]] = {}
    report_nodes: dict[str, dict[str, Any]] = {}
    company_aliases = config["finance"]["validated_company_aliases"]

    for document in sorted(documents, key=lambda row: row["document_id"]):
        provenance = _row_provenance(document, document["document_id"], raw_hashes, extractor)
        report_id = document["metadata"]["report_id"]
        ticker, year = report_id.split("/", 1)
        company = company_nodes.get(ticker)
        if company is None:
            company = collector.add_node(
                make_node(
                    "finance", "Company", ticker, company_aliases.get(ticker, ticker), provenance,
                    ticker=ticker, extraction="finqa_report_id",
                )
            )
            company_nodes[ticker] = company
        report = report_nodes.get(report_id)
        if report is None:
            report = collector.add_node(
                make_node(
                    "finance", "AnnualReport", report_id, f"{ticker} annual report {year}", provenance,
                    report_id=report_id, ticker=ticker, year=year, extraction="finqa_report_id",
                )
            )
            report_nodes[report_id] = report
            collector.add_edge(
                make_edge("finance", "HAS_REPORT", company["node_id"], report["node_id"], report_id, provenance)
            )
        doc_node = collector.add_node(
            make_node(
                "finance", "ReportPage", document["document_id"], document["title"], provenance,
                source_id=document["document_id"], page_id=document["metadata"]["page_id"], report_id=report_id,
                split=document["split"], dataset="finqa",
            )
        )
        doc_nodes[document["document_id"]] = doc_node
        collector.add_edge(
            make_edge("finance", "HAS_PAGE", report["node_id"], doc_node["node_id"], document["document_id"], provenance)
        )

    config_prov = _config_provenance(
        "finance-concept-lexicon", "term_paper/knowledge_rag/config/phase13.json", config_hash, extractor
    )
    concept_nodes: dict[str, dict[str, Any]] = {}
    for concept_id, label in sorted(config["finance"]["concept_labels"].items()):
        concept_nodes[concept_id] = collector.add_node(
            make_node(
                "finance", "FinancialConcept", concept_id, label, config_prov,
                concept_id=concept_id, extraction="fixed_validated_lexicon",
            )
        )
    lexicon = config["finance"]["concept_lexicon"]
    for chunk in read_jsonl(phase12 / "chunks.jsonl"):
        if chunk["domain"] != "finance":
            continue
        document = doc_by_id[chunk["document_id"]]
        provenance = _row_provenance(document, chunk["chunk_id"], raw_hashes, extractor)
        node = collector.add_node(
            make_node(
                "finance", "Chunk", chunk["chunk_id"], f"{document['title']} — {chunk['source_locator']}", provenance,
                source_id=chunk["chunk_id"], document_id=chunk["document_id"], split=chunk["split"],
                source_locator=chunk["source_locator"], segment_type=chunk.get("segment_type"), word_count=chunk["word_count"],
            )
        )
        collector.add_edge(
            make_edge("finance", "HAS_CHUNK", doc_nodes[chunk["document_id"]]["node_id"], node["node_id"], chunk["chunk_id"], provenance)
        )
        for concept_id in extract_financial_concepts(chunk["text"], lexicon):
            collector.add_edge(
                make_edge(
                    "finance", "MENTIONS", node["node_id"], concept_nodes[concept_id]["node_id"],
                    f"{chunk['chunk_id']}:{concept_id}", provenance, extraction="exact_lexicon_boundary",
                )
            )

    for query in read_jsonl(phase12 / "queries.jsonl"):
        if query["domain"] != "finance":
            continue
        fallback = doc_by_id.get(query.get("gold_document_ids", [None])[0], {}) if query.get("gold_document_ids") else {}
        provenance = _row_provenance(query, query["query_id"], raw_hashes, extractor, fallback)
        qnode = collector.add_node(
            make_node(
                "finance", "Question", query["query_id"], query["question"], provenance,
                source_id=query["query_id"], split=query["split"], group_id=query["group_id"], answer_available=query["answer_available"],
            )
        )
        for concept_id in extract_financial_concepts(query["question"], lexicon):
            collector.add_edge(
                make_edge(
                    "finance", "MENTIONS", qnode["node_id"], concept_nodes[concept_id]["node_id"],
                    f"{query['query_id']}:{concept_id}", provenance, extraction="exact_lexicon_boundary",
                )
            )

    wiki_nodes = _load_wikidata_nodes(collector, workspace, "finance", extractor)
    linkable = list(concept_nodes.values()) + list(company_nodes.values())
    audit = _audit_and_link(
        collector, linkable, wiki_nodes, config["finance"]["wikidata_rules"],
        "term_paper/knowledge_rag/config/phase13.json", config_hash, extractor,
    )
    nodes, edges = collector.sorted_rows()
    aapl = company_nodes.get("AAPL", next(iter(company_nodes.values())))
    report_edge = next(edge for edge in edges if edge["edge_type"] == "HAS_REPORT" and edge["source_id"] == aapl["node_id"])
    page_edge = next(edge for edge in edges if edge["edge_type"] == "HAS_PAGE" and edge["source_id"] == report_edge["target_id"])
    chunk_edge = next(edge for edge in edges if edge["edge_type"] == "HAS_CHUNK" and edge["source_id"] == page_edge["target_id"])
    path = shortest_path(build_adjacency(nodes, edges), aapl["node_id"], chunk_edge["target_id"], 4)
    return collector, audit, path


def _write_schema_svg(path: Path) -> None:
    columns = [
        ("Medical", ["Question", "Document", "Chunk", "MedicalEntity", "QuestionType", "WikidataEntity"]),
        ("Finance", ["Company", "AnnualReport", "ReportPage", "Chunk", "Question", "FinancialConcept", "WikidataEntity"]),
    ]
    width, height = 1200, 540
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<style>text{font-family:Arial,sans-serif}.title{font-size:24px;font-weight:700;fill:#0f172a}.label{font-size:15px;font-weight:600;fill:#0f172a}.note{font-size:13px;fill:#475569}.box{fill:#dbeafe;stroke:#2563eb;stroke-width:2;rx:10}</style>',
        '<text x="40" y="42" class="title">Phase 13 — Knowledge Graph schema</text>',
    ]
    for column_index, (title, labels) in enumerate(columns):
        x0 = 60 + column_index * 590
        parts.append(f'<text x="{x0}" y="86" class="title">{title}</text>')
        for index, label in enumerate(labels):
            row, col = divmod(index, 2)
            x, y = x0 + col * 260, 115 + row * 92
            parts.append(f'<rect class="box" x="{x}" y="{y}" width="220" height="54"/>')
            parts.append(f'<text class="label" x="{x + 110}" y="{y + 33}" text-anchor="middle">{escape(label)}</text>')
        parts.append(f'<text class="note" x="{x0}" y="500">Edges: provenance + stable ID; SAME_AS requires one exact validated alias.</text>')
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def _write_path_svg(path: Path, title: str, node_path: list[str], collector: GraphCollector) -> None:
    node_map = collector.nodes
    edge_map = {(edge["source_id"], edge["target_id"]): edge for edge in collector.edges.values()}
    width = max(900, 70 + len(node_path) * 250)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="260" viewBox="0 0 {width} 260">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<style>text{font-family:Arial,sans-serif}.title{font-size:22px;font-weight:700;fill:#0f172a}.type{font-size:13px;font-weight:700;fill:#1d4ed8}.label{font-size:12px;fill:#334155}.edge{font-size:11px;fill:#7c3aed}.box{fill:#fff;stroke:#2563eb;stroke-width:2;rx:10}</style>',
        f'<text x="35" y="38" class="title">{escape(title)}</text>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#7c3aed"/></marker></defs>',
    ]
    for index, node_id in enumerate(node_path):
        x, y = 35 + index * 245, 92
        node = node_map[node_id]
        label = str(node["label"])
        if len(label) > 28:
            label = label[:25] + "..."
        parts.append(f'<rect class="box" x="{x}" y="{y}" width="190" height="78"/>')
        parts.append(f'<text class="type" x="{x + 95}" y="{y + 28}" text-anchor="middle">{escape(node["node_type"])}</text>')
        parts.append(f'<text class="label" x="{x + 95}" y="{y + 53}" text-anchor="middle">{escape(label)}</text>')
        if index < len(node_path) - 1:
            next_x = x + 245
            edge = edge_map[(node_id, node_path[index + 1])]
            parts.append(f'<line x1="{x + 190}" y1="{y + 39}" x2="{next_x - 10}" y2="{y + 39}" stroke="#7c3aed" stroke-width="2" marker-end="url(#arrow)"/>')
            parts.append(f'<text class="edge" x="{x + 217}" y="{y + 27}" text-anchor="middle">{escape(edge["edge_type"])}</text>')
    parts.append('<text class="label" x="35" y="220">Đường đi được truy vấn trực tiếp từ adjacency.json; không cần Neo4j.</text>')
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def _export_domain(
    workspace: Path, collector: GraphCollector, linkable_types: set[str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    base = workspace / "term_paper/knowledge_rag"
    target = base / f"data/processed/phase13/{collector.domain}"
    nodes, edges = collector.sorted_rows()
    failures = validate_graph(nodes, edges)
    if failures:
        raise ValueError(f"{collector.domain} graph validation failed: {failures[:10]}")
    write_jsonl(target / "nodes.jsonl", nodes)
    write_jsonl(target / "edges.jsonl", edges)
    write_graphml(target / "graph.graphml", nodes, edges)
    adjacency = build_adjacency(nodes, edges)
    (target / "adjacency.json").write_text(
        json.dumps(adjacency, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8"
    )
    stats = graph_stats(nodes, edges, linkable_types)
    stats["schema_validation"] = "PASS"
    stats["provenance_coverage"] = {
        "nodes": round(sum(bool(row.get("provenance")) for row in nodes) / len(nodes), 6),
        "edges": round(sum(bool(row.get("provenance")) for row in edges) / len(edges), 6),
    }
    return stats, adjacency


def _artifact_row(workspace: Path, path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(workspace).as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def build_phase13(workspace: Path) -> dict[str, Any]:
    base = workspace / "term_paper/knowledge_rag"
    config_path = base / "config/phase13.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config_hash = sha256_file(config_path)
    raw_hashes = _raw_hashes(workspace)
    metrics_dir = base / "artifacts/metrics"
    figures_dir = base / "artifacts/figures/phase13"
    manifests_dir = base / "artifacts/manifests"
    for directory in (metrics_dir, figures_dir, manifests_dir):
        directory.mkdir(parents=True, exist_ok=True)

    medical, medical_audit, medical_path = build_medical(workspace, config, raw_hashes, config_hash)
    medical_stats, _ = _export_domain(workspace, medical, set(config["medical"]["linkable_node_types"]))
    _write_path_svg(figures_dir / "medical_sample_subgraph.svg", "Medical KG — sample path", medical_path, medical)

    finance, finance_audit, finance_path = build_finance(workspace, config, raw_hashes, config_hash)
    finance_stats, _ = _export_domain(workspace, finance, set(config["finance"]["linkable_node_types"]))
    _write_path_svg(figures_dir / "finance_sample_subgraph.svg", "Finance KG — sample path", finance_path, finance)
    _write_schema_svg(figures_dir / "graph_schema.svg")

    audit = sorted(medical_audit + finance_audit, key=lambda row: (row["domain"], row["local_node_id"]))
    audit_path = metrics_dir / "phase13_entity_link_audit.csv"
    audit_fields = (
        "domain", "local_node_id", "local_label", "candidate_qids", "decision", "linked_qid",
        "method", "confidence", "rationale", "source_record_id",
    )
    with audit_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=audit_fields)
        writer.writeheader()
        writer.writerows(audit)

    stats = {
        "schema_version": 1,
        "generated_at": config["generated_at"],
        "extractor_version": config["extractor_version"],
        "config_sha256": config_hash,
        "input_preprocessing_manifest_sha256": sha256_file(base / "artifacts/manifests/preprocessing_manifest.json"),
        "test_split_status": "SEALED_NOT_USED_FOR_TUNING",
        "medical": medical_stats,
        "finance": finance_stats,
        "entity_link_audit": {
            "rows": len(audit),
            "linked": sum(row["decision"] == "linked" for row in audit),
            "unresolved": sum(row["decision"] == "unresolved" for row in audit),
            "forced_ambiguous_links": 0,
        },
    }
    stats_path = metrics_dir / "phase13_graph_statistics.json"
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    stats_csv = metrics_dir / "phase13_graph_statistics.csv"
    with stats_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "domain", "node_count", "edge_count", "component_count", "isolated_node_count", "mean_degree",
                "maximum_degree", "entity_link_coverage", "duplicate_node_rate", "duplicate_edge_rate",
                "node_type_counts", "edge_type_counts",
            ),
        )
        writer.writeheader()
        for domain, domain_stats in (("medical", medical_stats), ("finance", finance_stats)):
            writer.writerow(
                {
                    "domain": domain,
                    "node_count": domain_stats["node_count"],
                    "edge_count": domain_stats["edge_count"],
                    "component_count": domain_stats["component_count"],
                    "isolated_node_count": domain_stats["isolated_node_count"],
                    "mean_degree": domain_stats["degree"]["mean"],
                    "maximum_degree": domain_stats["degree"]["maximum"],
                    "entity_link_coverage": domain_stats["entity_link_coverage"],
                    "duplicate_node_rate": domain_stats["duplicate_node_rate"],
                    "duplicate_edge_rate": domain_stats["duplicate_edge_rate"],
                    "node_type_counts": json.dumps(domain_stats["node_type_counts"], sort_keys=True),
                    "edge_type_counts": json.dumps(domain_stats["edge_type_counts"], sort_keys=True),
                }
            )
    sample_paths_path = metrics_dir / "phase13_sample_paths.json"
    sample_paths_path.write_text(
        json.dumps(
            {
                "medical": {"node_ids": medical_path, "hop_count": max(0, len(medical_path) - 1)},
                "finance": {"node_ids": finance_path, "hop_count": max(0, len(finance_path) - 1)},
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    report_path = base / "phase13_build_report.md"
    report_path.write_text(
        "# Phase 13 build report\n\n"
        f"- Extractor: `{config['extractor_version']}`\n"
        "- TEST policy: `SEALED_NOT_USED_FOR_TUNING`\n"
        f"- Medical: {medical_stats['node_count']:,} nodes, {medical_stats['edge_count']:,} edges, "
        f"link coverage {medical_stats['entity_link_coverage']:.3f}.\n"
        f"- Finance: {finance_stats['node_count']:,} nodes, {finance_stats['edge_count']:,} edges, "
        f"link coverage {finance_stats['entity_link_coverage']:.3f}.\n"
        f"- Entity-link audit: {len(audit):,} rows; {stats['entity_link_audit']['linked']:,} linked; "
        f"{stats['entity_link_audit']['unresolved']:,} unresolved; 0 forced ambiguous links.\n"
        "- Both graph schemas: PASS; provenance coverage: 100% nodes and edges; duplicate rates: 0.\n"
        "- Offline exports: JSONL + GraphML + bidirectional adjacency JSON.\n",
        encoding="utf-8",
    )

    generated = [
        config_path,
        base / "graph_schema.md",
        report_path,
        metrics_dir / "phase13_graph_statistics.json",
        metrics_dir / "phase13_graph_statistics.csv",
        metrics_dir / "phase13_entity_link_audit.csv",
        metrics_dir / "phase13_sample_paths.json",
        figures_dir / "graph_schema.svg",
        figures_dir / "medical_sample_subgraph.svg",
        figures_dir / "finance_sample_subgraph.svg",
    ]
    for domain in ("medical", "finance"):
        graph_dir = base / f"data/processed/phase13/{domain}"
        generated.extend(graph_dir / name for name in ("nodes.jsonl", "edges.jsonl", "graph.graphml", "adjacency.json"))
    manifest = {
        "schema_version": 1,
        "generated_at": config["generated_at"],
        "status": "PASS",
        "domains": ["medical", "finance"],
        "test_split_status": "SEALED_NOT_USED_FOR_TUNING",
        "artifacts": [_artifact_row(workspace, path) for path in sorted(generated)],
    }
    manifest_path = manifests_dir / "phase13_graph_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "PASS", "statistics": stats, "manifest": manifest_path.relative_to(workspace).as_posix()}


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    result = build_phase13(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
