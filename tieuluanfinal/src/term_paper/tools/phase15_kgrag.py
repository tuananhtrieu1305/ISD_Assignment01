"""Graph retrieval, KG-aware fusion, and analysis contracts for Phase 15."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from term_paper.tools.phase12_preprocessing import normalize_answer


@dataclass
class GraphRetriever:
    domain: str
    nodes: dict[str, dict[str, Any]]
    query_nodes: dict[str, str]
    outgoing: dict[str, list[dict[str, Any]]]
    incoming: dict[str, list[dict[str, Any]]]

    @classmethod
    def from_records(
        cls, domain: str, nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]]
    ) -> "GraphRetriever":
        node_map = {str(node["node_id"]): dict(node) for node in nodes}
        query_nodes = {
            str(node["source_id"]): str(node["node_id"])
            for node in nodes
            if node.get("node_type") == "Question" and node.get("source_id")
        }
        outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
        incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in edges:
            item = dict(edge)
            outgoing[str(edge["source_id"])].append(item)
            incoming[str(edge["target_id"])].append(item)
        for mapping in (outgoing, incoming):
            for key in mapping:
                mapping[key].sort(key=lambda edge: str(edge["edge_id"]))
        return cls(domain, node_map, query_nodes, dict(outgoing), dict(incoming))

    def expand(self, query_id: str, max_hops: int = 2) -> dict[str, Any]:
        if max_hops < 0:
            raise ValueError("max_hops must be non-negative")
        query_node = self.query_nodes.get(query_id)
        if not query_node:
            return {"query_node_id": None, "anchor_node_ids": [], "chunk_ids": [], "paths": {}}
        anchor_edges = [
            edge for edge in self.outgoing.get(query_node, [])
            if edge.get("edge_type") in {"ASKS_ABOUT", "MENTIONS"}
        ]
        anchors = sorted({str(edge["target_id"]) for edge in anchor_edges})
        paths: dict[str, list[str]] = {}
        if self.domain == "medical" and max_hops >= 2:
            for anchor in anchors:
                documents = sorted(
                    str(edge["source_id"])
                    for edge in self.incoming.get(anchor, [])
                    if edge.get("edge_type") == "DESCRIBES"
                )
                for document in documents:
                    for edge in self.outgoing.get(document, []):
                        if edge.get("edge_type") != "HAS_CHUNK":
                            continue
                        chunk_node = str(edge["target_id"])
                        chunk_id = self.nodes.get(chunk_node, {}).get("source_id")
                        if chunk_id:
                            paths[str(chunk_id)] = [query_node, anchor, document, chunk_node]
        elif self.domain == "finance" and max_hops >= 1:
            for anchor in anchors:
                for edge in self.incoming.get(anchor, []):
                    if edge.get("edge_type") != "MENTIONS":
                        continue
                    chunk_node = str(edge["source_id"])
                    node = self.nodes.get(chunk_node, {})
                    if node.get("node_type") == "Chunk" and node.get("source_id"):
                        paths[str(node["source_id"])] = [query_node, anchor, chunk_node]
        return {
            "query_node_id": query_node,
            "anchor_node_ids": anchors,
            "chunk_ids": sorted(paths),
            "paths": dict(sorted(paths.items())),
        }


def graph_filter_ranking(
    lexical_ranking: Sequence[tuple[str, float]], candidate_ids: set[str], top_k: int
) -> list[tuple[str, float]]:
    if top_k <= 0 or not candidate_ids:
        return []
    seen: set[str] = set()
    ranked: list[tuple[str, float]] = []
    for chunk_id, score in lexical_ranking:
        if chunk_id in candidate_ids and chunk_id not in seen:
            ranked.append((chunk_id, float(score)))
            seen.add(chunk_id)
            if len(ranked) == top_k:
                return ranked
    for chunk_id in sorted(candidate_ids - seen):
        ranked.append((chunk_id, 0.0))
        if len(ranked) == top_k:
            break
    return ranked


def weighted_rrf(
    rankings: Mapping[str, Sequence[tuple[str, float]]],
    weights: Mapping[str, float],
    top_k: int,
    rrf_k: int = 60,
) -> list[tuple[str, float]]:
    if set(rankings) != set(weights):
        raise ValueError("Every ranking must have exactly one weight")
    if any(float(value) < 0 for value in weights.values()) or not np.isclose(sum(weights.values()), 1.0):
        raise ValueError("Weights must be non-negative and sum to one")
    scores: dict[str, float] = {}
    for name in sorted(rankings):
        for rank, (chunk_id, _) in enumerate(rankings[name], start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + float(weights[name]) / (rrf_k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:top_k]


def bootstrap_mean_ci(
    values: Sequence[float], seed: int = 42, n_resamples: int = 1000, confidence: float = 0.95
) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0 or n_resamples <= 0 or not 0.0 < confidence < 1.0:
        raise ValueError("Non-empty values, positive resamples, and confidence in (0,1) are required")
    rng = np.random.default_rng(seed)
    samples = rng.choice(array, size=(n_resamples, array.size), replace=True).mean(axis=1)
    alpha = (1.0 - confidence) / 2.0
    return {
        "mean": round(float(array.mean()), 6),
        "lower": round(float(np.quantile(samples, alpha)), 6),
        "upper": round(float(np.quantile(samples, 1.0 - alpha)), 6),
        "confidence": confidence,
        "n_resamples": n_resamples,
    }


def classify_kg_effect(
    baseline_ranking: Sequence[str], kg_ranking: Sequence[str], gold_ids: set[str], k: int
) -> str:
    baseline_hit = bool(set(baseline_ranking[:k]) & gold_ids)
    kg_hit = bool(set(kg_ranking[:k]) & gold_ids)
    if kg_hit and not baseline_hit:
        return "helps"
    if baseline_hit and not kg_hit:
        return "hurts"
    return "neutral"


def categorize_error(prediction: Mapping[str, Any], graph_candidate_count: int) -> list[str]:
    categories: list[str] = []
    if prediction.get("split") == "challenge":
        challenge_type = str(prediction.get("challenge_type", "ood"))
        categories.append(challenge_type if challenge_type in {"ood", "adversarial"} else "ood")
    ranked = set(prediction.get("ranked_chunk_ids", [])[:10])
    gold = set(prediction.get("gold_chunk_ids", []))
    if graph_candidate_count == 0:
        categories.append("entity_linking")
    if gold and not ranked & gold:
        categories.append("retrieval_miss")
    exact = normalize_answer(prediction.get("answer", "")) == normalize_answer(prediction.get("gold_answer", ""))
    if prediction.get("domain") == "finance" and ranked & gold and not exact:
        categories.append("numerical_reasoning")
    citations = set(prediction.get("citations", []))
    if not prediction.get("abstained") and citations and not citations & gold:
        categories.append("unsupported_answer")
    if not categories:
        categories.append("correct_or_other")
    return categories


def decide_test_run(
    existing_manifest: Mapping[str, Any] | None,
    locked_config_sha256: str,
    query_set_sha256: str,
) -> str:
    if existing_manifest is None:
        return "execute"
    if existing_manifest.get("status") != "COMPLETE" or existing_manifest.get("run_count") != 1:
        raise ValueError("TEST run manifest is incomplete or run_count is not exactly one")
    if existing_manifest.get("locked_config_sha256") != locked_config_sha256:
        raise ValueError("TEST run belongs to a different locked config")
    if existing_manifest.get("query_set_sha256") != query_set_sha256:
        raise ValueError("TEST run belongs to a different query set")
    return "reuse"
