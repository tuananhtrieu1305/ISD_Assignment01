"""Deterministic, dependency-free graph contracts for Phase 13."""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from collections import Counter, deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from xml.sax.saxutils import escape, quoteattr


PROVENANCE_FIELDS = (
    "source_record_id",
    "source_path",
    "source_sha256",
    "extractor_version",
    "confidence",
)


def normalize_label(value: Any) -> str:
    text = str(value or "").casefold().replace("_", "-")
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def stable_graph_id(kind: str, *parts: Any, length: int = 24) -> str:
    canonical = "\x1f".join(normalize_label(part) for part in (kind, *parts))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:length]
    return f"kg-{normalize_label(kind)}-{digest}"


def make_provenance(
    source_record_id: str,
    source_path: str,
    source_sha256: str,
    extractor_version: str,
    confidence: float,
) -> dict[str, Any]:
    if not all(str(value).strip() for value in (source_record_id, source_path, extractor_version)):
        raise ValueError("Provenance source record, path, and extractor version are required")
    if not re.fullmatch(r"[0-9a-f]{64}", str(source_sha256).casefold()):
        raise ValueError("Provenance source_sha256 must be a lowercase SHA-256 digest")
    score = float(confidence)
    if not 0.0 <= score <= 1.0 or not math.isfinite(score):
        raise ValueError("Provenance confidence must be finite and in [0, 1]")
    return {
        "source_record_id": str(source_record_id),
        "source_path": str(source_path).replace("\\", "/"),
        "source_sha256": str(source_sha256).casefold(),
        "extractor_version": str(extractor_version),
        "confidence": score,
    }


def make_node(
    domain: str,
    node_type: str,
    stable_key: str,
    label: str,
    provenance: Mapping[str, Any],
    **attributes: Any,
) -> dict[str, Any]:
    node = {
        "node_id": stable_graph_id("node", domain, node_type, stable_key),
        "domain": domain,
        "node_type": node_type,
        "stable_key": stable_key,
        "label": str(label),
        "provenance": dict(provenance),
    }
    node.update(attributes)
    return node


def make_edge(
    domain: str,
    edge_type: str,
    source_id: str,
    target_id: str,
    stable_key: str,
    provenance: Mapping[str, Any],
    directed: bool = True,
    **attributes: Any,
) -> dict[str, Any]:
    edge = {
        "edge_id": stable_graph_id("edge", domain, edge_type, source_id, target_id, stable_key),
        "domain": domain,
        "edge_type": edge_type,
        "source_id": source_id,
        "target_id": target_id,
        "stable_key": stable_key,
        "directed": bool(directed),
        "provenance": dict(provenance),
    }
    edge.update(attributes)
    return edge


def _validate_provenance(value: Any, owner: str) -> list[str]:
    if not isinstance(value, Mapping):
        return [f"{owner}: missing provenance object"]
    failures = [f"{owner}: missing provenance.{field}" for field in PROVENANCE_FIELDS if field not in value]
    if failures:
        return failures
    try:
        make_provenance(**{field: value[field] for field in PROVENANCE_FIELDS})
    except (TypeError, ValueError) as exc:
        failures.append(f"{owner}: invalid provenance ({exc})")
    return failures


def validate_graph(nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    node_ids = [str(node.get("node_id", "")) for node in nodes]
    edge_ids = [str(edge.get("edge_id", "")) for edge in edges]
    duplicate_nodes = sorted(key for key, count in Counter(node_ids).items() if key and count > 1)
    duplicate_edges = sorted(key for key, count in Counter(edge_ids).items() if key and count > 1)
    if duplicate_nodes:
        failures.append(f"duplicate node IDs: {duplicate_nodes[:5]}")
    if duplicate_edges:
        failures.append(f"duplicate edge IDs: {duplicate_edges[:5]}")
    node_set = set(node_ids)
    for node in nodes:
        owner = f"node {node.get('node_id', '<missing>')}"
        for field in ("node_id", "domain", "node_type", "stable_key", "label"):
            if not str(node.get(field, "")).strip():
                failures.append(f"{owner}: missing {field}")
        expected = stable_graph_id("node", node.get("domain"), node.get("node_type"), node.get("stable_key"))
        if node.get("node_id") != expected:
            failures.append(f"{owner}: unstable node ID")
        failures.extend(_validate_provenance(node.get("provenance"), owner))
    for edge in edges:
        owner = f"edge {edge.get('edge_id', '<missing>')}"
        for field in ("edge_id", "domain", "edge_type", "source_id", "target_id", "stable_key"):
            if not str(edge.get(field, "")).strip():
                failures.append(f"{owner}: missing {field}")
        expected = stable_graph_id(
            "edge",
            edge.get("domain"),
            edge.get("edge_type"),
            edge.get("source_id"),
            edge.get("target_id"),
            edge.get("stable_key"),
        )
        if edge.get("edge_id") != expected:
            failures.append(f"{owner}: unstable edge ID")
        if edge.get("source_id") not in node_set or edge.get("target_id") not in node_set:
            failures.append(f"{owner}: dangling endpoint")
        failures.extend(_validate_provenance(edge.get("provenance"), owner))
    return failures


def validate_evaluation_safety(edges: Sequence[Mapping[str, Any]]) -> list[str]:
    """Reject edges that expose evaluation relevance labels to retrieval."""
    forbidden = {"ANSWERED_BY", "ANSWERED_BY_DOCUMENT", "GOLD_EVIDENCE", "GOLD_RELEVANT"}
    failures: list[str] = []
    for edge in edges:
        if str(edge.get("edge_type")) in forbidden:
            failures.append(
                f"edge {edge.get('edge_id', '<missing>')}: gold-derived relation "
                f"{edge.get('edge_type')} is forbidden in the retrieval graph"
            )
    return failures


def link_wikidata(label: str, rules: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    normalized = normalize_label(label)
    exact = sorted(
        {
            str(rule["qid"])
            for rule in rules
            if normalized and normalized in {normalize_label(alias) for alias in rule.get("aliases", [])}
        }
    )
    if len(exact) == 1:
        return {
            "decision": "linked",
            "linked_qid": exact[0],
            "candidate_qids": exact,
            "method": "exact_validated_alias",
            "confidence": 1.0,
            "rationale": "One and only one validated alias matched exactly.",
        }
    if exact:
        return {
            "decision": "unresolved",
            "linked_qid": None,
            "candidate_qids": exact,
            "method": "ambiguous_exact_alias",
            "confidence": 0.0,
            "rationale": "Multiple Wikidata entities share the same validated alias; no match was forced.",
        }
    candidates = sorted(
        {
            str(rule["qid"])
            for rule in rules
            if any(normalize_label(term) in normalized for term in rule.get("candidate_terms", []) if normalize_label(term))
        }
    )
    return {
        "decision": "unresolved",
        "linked_qid": None,
        "candidate_qids": candidates,
        "method": "candidate_only" if candidates else "no_candidate",
        "confidence": 0.0,
        "rationale": (
            "Candidate generation was not an exact validated alias; no match was forced."
            if candidates
            else "No Wikidata candidate passed deterministic candidate generation."
        ),
    }


def extract_financial_concepts(text: str, lexicon: Mapping[str, Sequence[str]]) -> list[str]:
    normalized = f" {normalize_label(text)} "
    matched: list[str] = []
    for concept_id in sorted(lexicon):
        aliases = sorted({normalize_label(alias) for alias in lexicon[concept_id]}, key=lambda x: (-len(x), x))
        if any(re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized) for alias in aliases if alias):
            matched.append(concept_id)
    return matched


def build_adjacency(
    nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]]
) -> dict[str, dict[str, list[list[str]]]]:
    node_ids = sorted(str(node["node_id"]) for node in nodes)
    outgoing: dict[str, list[list[str]]] = {node_id: [] for node_id in node_ids}
    incoming: dict[str, list[list[str]]] = {node_id: [] for node_id in node_ids}
    for edge in sorted(edges, key=lambda row: str(row["edge_id"])):
        source, target, relation = str(edge["source_id"]), str(edge["target_id"]), str(edge["edge_type"])
        outgoing.setdefault(source, []).append([relation, target, str(edge["edge_id"])])
        incoming.setdefault(target, []).append([relation, source, str(edge["edge_id"])])
        if not edge.get("directed", True):
            outgoing.setdefault(target, []).append([relation, source, str(edge["edge_id"])])
            incoming.setdefault(source, []).append([relation, target, str(edge["edge_id"])])
    return {"out": outgoing, "in": incoming}


def shortest_path(
    adjacency: Mapping[str, Mapping[str, Sequence[Sequence[str]]]],
    start_id: str,
    goal_id: str,
    max_hops: int = 4,
) -> list[str]:
    if start_id == goal_id:
        return [start_id]
    outgoing = adjacency.get("out", {})
    queue: deque[tuple[str, list[str]]] = deque([(start_id, [start_id])])
    visited = {start_id}
    while queue:
        current, path = queue.popleft()
        if len(path) - 1 >= max_hops:
            continue
        for item in outgoing.get(current, []):
            target = str(item[1])
            if target == goal_id:
                return path + [target]
            if target not in visited:
                visited.add(target)
                queue.append((target, path + [target]))
    return []


def graph_stats(
    nodes: Sequence[Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
    linkable_node_types: set[str] | None = None,
) -> dict[str, Any]:
    node_ids = [str(node["node_id"]) for node in nodes]
    edge_ids = [str(edge["edge_id"]) for edge in edges]
    node_type_counts = Counter(str(node["node_type"]) for node in nodes)
    edge_type_counts = Counter(str(edge["edge_type"]) for edge in edges)
    undirected: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    degrees = Counter({node_id: 0 for node_id in node_ids})
    linked_sources: set[str] = set()
    for edge in edges:
        source, target = str(edge["source_id"]), str(edge["target_id"])
        if source in undirected and target in undirected:
            undirected[source].add(target)
            undirected[target].add(source)
            degrees[source] += 1
            degrees[target] += 1
        if edge.get("edge_type") == "SAME_AS":
            linked_sources.add(source)
    components = 0
    visited: set[str] = set()
    for node_id in sorted(undirected):
        if node_id in visited:
            continue
        components += 1
        queue = [node_id]
        visited.add(node_id)
        while queue:
            current = queue.pop()
            for neighbor in undirected[current] - visited:
                visited.add(neighbor)
                queue.append(neighbor)
    linkable_types = linkable_node_types or set()
    linkable = {str(node["node_id"]) for node in nodes if str(node["node_type"]) in linkable_types}
    degree_values = list(degrees.values())
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_type_counts": dict(sorted(node_type_counts.items())),
        "edge_type_counts": dict(sorted(edge_type_counts.items())),
        "component_count": components,
        "isolated_node_count": sum(value == 0 for value in degree_values),
        "degree": {
            "minimum": min(degree_values, default=0),
            "maximum": max(degree_values, default=0),
            "mean": round(statistics.fmean(degree_values), 6) if degree_values else 0.0,
            "median": statistics.median(degree_values) if degree_values else 0.0,
        },
        "linkable_node_count": len(linkable),
        "linked_node_count": len(linkable & linked_sources),
        "entity_link_coverage": round(len(linkable & linked_sources) / len(linkable), 6) if linkable else 0.0,
        "duplicate_node_rate": round((len(node_ids) - len(set(node_ids))) / len(node_ids), 6) if node_ids else 0.0,
        "duplicate_edge_rate": round((len(edge_ids) - len(set(edge_ids))) / len(edge_ids), 6) if edge_ids else 0.0,
    }


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_graphml(path: Path, nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]]) -> None:
    """Write GraphML incrementally so the full XML tree is never held in memory."""
    keys = (
        ("node_type", "node", "string"),
        ("label", "node", "string"),
        ("domain", "all", "string"),
        ("stable_key", "all", "string"),
        ("provenance_json", "all", "string"),
        ("edge_type", "edge", "string"),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write('<?xml version="1.0" encoding="utf-8"?>\n')
        handle.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n')
        for key_id, target, attr_type in keys:
            handle.write(
                f'  <key id={quoteattr(key_id)} for={quoteattr(target)} '
                f'attr.name={quoteattr(key_id)} attr.type={quoteattr(attr_type)}/>\n'
            )
        handle.write('  <graph id="G" edgedefault="directed">\n')
        for node in sorted(nodes, key=lambda row: str(row["node_id"])):
            handle.write(f'    <node id={quoteattr(str(node["node_id"]))}>\n')
            values = {
                "node_type": node["node_type"], "label": node["label"], "domain": node["domain"],
                "stable_key": node["stable_key"],
                "provenance_json": json.dumps(node["provenance"], ensure_ascii=False, sort_keys=True),
            }
            for key, value in values.items():
                handle.write(f'      <data key={quoteattr(key)}>{escape(str(value))}</data>\n')
            handle.write("    </node>\n")
        for edge in sorted(edges, key=lambda row: str(row["edge_id"])):
            handle.write(
                f'    <edge id={quoteattr(str(edge["edge_id"]))} source={quoteattr(str(edge["source_id"]))} '
                f'target={quoteattr(str(edge["target_id"]))}>\n'
            )
            values = {
                "edge_type": edge["edge_type"], "domain": edge["domain"], "stable_key": edge["stable_key"],
                "provenance_json": json.dumps(edge["provenance"], ensure_ascii=False, sort_keys=True),
            }
            for key, value in values.items():
                handle.write(f'      <data key={quoteattr(key)}>{escape(str(value))}</data>\n')
            handle.write("    </edge>\n")
        handle.write("  </graph>\n</graphml>\n")
