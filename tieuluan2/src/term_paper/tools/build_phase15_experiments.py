"""Tune B3/B4 on validation, then execute the sealed TEST split exactly once."""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import io
import json
import platform
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from xml.sax.saxutils import escape

import joblib
import numpy as np

from term_paper.tools.build_phase14_baselines import _base_rankings
from term_paper.tools.phase12_preprocessing import normalize_answer
from term_paper.tools.phase14_rag import grounded_answer, prediction_metrics, stable_hash
from term_paper.tools.phase15_kgrag import (
    GraphRetriever,
    bootstrap_mean_ci,
    categorize_error,
    classify_kg_effect,
    decide_test_run,
    graph_filter_ranking,
    weighted_rrf,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def _load_graph(base: Path, domain: str) -> GraphRetriever:
    graph_dir = base / f"data/processed/phase13/{domain}"
    nodes = [
        {key: row.get(key) for key in ("node_id", "node_type", "source_id")}
        for row in read_jsonl(graph_dir / "nodes.jsonl")
    ]
    edges = [
        {key: row.get(key) for key in ("edge_id", "edge_type", "source_id", "target_id")}
        for row in read_jsonl(graph_dir / "edges.jsonl")
    ]
    return GraphRetriever.from_records(domain, nodes, edges)


def _load_common(workspace: Path) -> dict[str, Any]:
    base = workspace / "term_paper/knowledge_rag"
    config = json.loads((base / "config/phase15.json").read_text(encoding="utf-8"))
    phase14_config = json.loads((base / "config/phase14.json").read_text(encoding="utf-8"))
    phase14_locked = json.loads((base / "config/phase14_locked.json").read_text(encoding="utf-8"))
    phase14_manifest = json.loads((base / "artifacts/manifests/phase14_baseline_manifest.json").read_text(encoding="utf-8"))
    chunks: dict[str, list[dict[str, Any]]] = {"medical": [], "finance": []}
    for row in read_jsonl(base / "data/processed/phase12/chunks.jsonl"):
        chunks[row["domain"]].append(row)
    for domain in chunks:
        chunks[domain].sort(key=lambda row: row["chunk_id"])
    queries: dict[str, dict[str, list[dict[str, Any]]]] = {
        domain: {"validation": [], "test": []} for domain in chunks
    }
    for row in read_jsonl(base / "data/processed/phase12/queries.jsonl"):
        if row["split"] in {"validation", "test"}:
            queries[row["domain"]][row["split"]].append(row)
    for domain in queries:
        for split in queries[domain]:
            queries[domain][split].sort(key=lambda row: row["query_id"])
    challenges: dict[str, list[dict[str, Any]]] = {"medical": [], "finance": []}
    for row in read_jsonl(base / "data/processed/phase12/challenge_queries.jsonl"):
        challenges[row["domain"]].append(row)
    for domain in challenges:
        challenges[domain].sort(key=lambda row: row["query_id"])
    indexes = {
        domain: (
            joblib.load(base / f"data/processed/phase14/indexes/{domain}/bm25.joblib"),
            joblib.load(base / f"data/processed/phase14/indexes/{domain}/dense_lsa.joblib"),
        )
        for domain in ("medical", "finance")
    }
    graphs = {domain: _load_graph(base, domain) for domain in ("medical", "finance")}
    corpus_hashes = phase14_manifest["corpus_sha256"]
    return {
        "base": base, "config": config, "phase14_config": phase14_config, "phase14_locked": phase14_locked,
        "phase14_manifest": phase14_manifest, "chunks": chunks, "queries": queries, "challenges": challenges,
        "indexes": indexes, "graphs": graphs, "corpus_hashes": corpus_hashes,
    }


def _graph_rankings(
    queries: Sequence[Mapping[str, Any]],
    base_rankings: Mapping[str, Mapping[str, Any]],
    graph: GraphRetriever,
    max_hops: int,
    top_k: int,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for query in queries:
        started = time.perf_counter()
        expansion = graph.expand(str(query["query_id"]), max_hops=max_hops)
        graph_ranking = graph_filter_ranking(
            base_rankings[str(query["query_id"])]["B0"], set(expansion["chunk_ids"]), top_k
        )
        result[str(query["query_id"])] = {
            "ranking": graph_ranking,
            "expansion": expansion,
            "latency_ms": (time.perf_counter() - started) * 1000.0,
        }
    return result


def _hit(ranking: Sequence[tuple[str, float]], gold: Sequence[str], k: int) -> float:
    return float(bool({chunk_id for chunk_id, _ in ranking[:k]} & set(gold)))


def _rr(values: Sequence[str], gold: set[str], k: int = 10) -> float:
    for rank, value in enumerate(values[:k], start=1):
        if value in gold:
            return 1.0 / rank
    return 0.0


def _tune(
    common: Mapping[str, Any],
    base_by_domain: Mapping[str, Mapping[str, Mapping[str, Any]]],
    graph_by_domain_hop: Mapping[str, Mapping[int, Mapping[str, Mapping[str, Any]]]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config = common["config"]
    rows: list[dict[str, Any]] = []
    for hops in sorted(config["B3"]["candidate_max_hops"]):
        for weights in sorted(config["B4"]["candidate_weights"], key=lambda row: (row["sparse"], row["dense"], row["graph"])):
            domain_scores: dict[str, float] = {}
            for domain in ("medical", "finance"):
                hits: list[float] = []
                for query in common["queries"][domain]["validation"]:
                    query_id = query["query_id"]
                    base = base_by_domain[domain][query_id]
                    graph_ranking = graph_by_domain_hop[domain][hops][query_id]["ranking"]
                    fused = weighted_rrf(
                        {"sparse": base["B0"], "dense": base["B1"], "graph": graph_ranking},
                        weights,
                        top_k=5,
                        rrf_k=config["B4"]["rrf_k"],
                    )
                    hits.append(_hit(fused, query.get("gold_chunk_ids", []), 5))
                domain_scores[domain] = float(np.mean(hits))
            macro = float(np.mean(list(domain_scores.values())))
            rows.append(
                {
                    "max_hops": hops,
                    "weights": dict(weights),
                    "medical_chunk_recall_at_5": round(domain_scores["medical"], 6),
                    "finance_chunk_recall_at_5": round(domain_scores["finance"], 6),
                    "macro_domain_chunk_recall_at_5": round(macro, 6),
                }
            )
    selected = min(
        rows,
        key=lambda row: (
            -row["macro_domain_chunk_recall_at_5"], row["max_hops"],
            row["weights"]["sparse"], row["weights"]["dense"], row["weights"]["graph"],
        ),
    )
    return selected, rows


def _model_ranking(
    model_id: str,
    base: Mapping[str, Any],
    graph_item: Mapping[str, Any],
    config: Mapping[str, Any],
    selected_weights: Mapping[str, float],
    top_k: int,
) -> tuple[list[tuple[str, float]], float, Mapping[str, float] | None]:
    if model_id == "B0":
        return list(base["B0"][:top_k]), float(base["B0_latency_ms"]), None
    if model_id == "B1":
        return list(base["B1"][:top_k]), float(base["B1_latency_ms"]), None
    if model_id == "B2":
        weights = {"sparse": config["baseline"]["B2_sparse_weight"], "dense": 1.0 - config["baseline"]["B2_sparse_weight"]}
        started = time.perf_counter()
        ranking = weighted_rrf({"sparse": base["B0"], "dense": base["B1"]}, weights, top_k, config["B4"]["rrf_k"])
        latency = base["B0_latency_ms"] + base["B1_latency_ms"] + (time.perf_counter() - started) * 1000.0
        return ranking, float(latency), weights
    if model_id == "B3":
        return list(graph_item["ranking"][:top_k]), float(base["B0_latency_ms"] + graph_item["latency_ms"]), {"graph": 1.0}
    started = time.perf_counter()
    ranking = weighted_rrf(
        {"sparse": base["B0"], "dense": base["B1"], "graph": graph_item["ranking"]},
        selected_weights,
        top_k,
        config["B4"]["rrf_k"],
    )
    latency = base["B0_latency_ms"] + base["B1_latency_ms"] + graph_item["latency_ms"] + (time.perf_counter() - started) * 1000.0
    return ranking, float(latency), selected_weights


def _prediction_row(
    query: Mapping[str, Any],
    model_id: str,
    ranking: Sequence[tuple[str, float]],
    latency_ms: float,
    chunks_by_id: Mapping[str, Mapping[str, Any]],
    locked_hash: str,
    corpus_hash: str,
    answer_config: Mapping[str, Any],
    graph_item: Mapping[str, Any],
    fusion_weights: Mapping[str, float] | None,
    input_hashes: Mapping[str, str],
) -> dict[str, Any]:
    answer = grounded_answer(
        str(query["question"]), ranking,
        {chunk_id: str(chunks_by_id[chunk_id]["text"]) for chunk_id, _ in ranking if chunk_id in chunks_by_id},
        answer_config["minimum_overlap_terms"], answer_config["minimum_overlap_ratio"], answer_config["unsafe_patterns"],
        answer_config["maximum_characters"],
    )
    ranked_ids = [chunk_id for chunk_id, _ in ranking]
    trace_chunk = next((chunk_id for chunk_id in ranked_ids if chunk_id in graph_item["expansion"]["paths"]), None)
    return {
        "prediction_id": f"p15-{stable_hash([model_id, query['query_id'], locked_hash])[:24]}",
        "model_id": model_id,
        "domain": query["domain"],
        "dataset": query.get("dataset"),
        "split": query["split"],
        "challenge_type": query.get("challenge_type"),
        "expected_behavior": query.get("expected_behavior"),
        "query_id": query["query_id"],
        "question": query["question"],
        "ranked_chunk_ids": ranked_ids,
        "ranked_document_ids": [chunks_by_id[chunk_id]["document_id"] for chunk_id in ranked_ids],
        "retrieval_scores": [round(float(score), 8) for _, score in ranking],
        "retrieved_chunk_ids": ranked_ids,
        "gold_chunk_ids": list(query.get("gold_chunk_ids", [])),
        "gold_document_ids": list(query.get("gold_document_ids", [])),
        "gold_answer": query.get("gold_answer", ""),
        "answer": answer["answer"],
        "citations": answer["citations"],
        "abstained": answer["abstained"],
        "abstention_reason": answer["reason"],
        "latency_ms": round(latency_ms, 6),
        "config_sha256": locked_hash,
        "corpus_sha256": corpus_hash,
        "fusion_weights": dict(fusion_weights) if fusion_weights else None,
        "graph_candidate_count": len(graph_item["expansion"]["chunk_ids"]),
        "graph_anchor_node_ids": graph_item["expansion"]["anchor_node_ids"],
        "graph_trace_chunk_id": trace_chunk,
        "graph_trace_node_ids": graph_item["expansion"]["paths"].get(trace_chunk, []) if trace_chunk else [],
        "query_source_path": query.get("raw_source_path"),
        "input_artifact_hashes": dict(input_hashes),
    }


def _make_predictions(
    common: Mapping[str, Any], domain: str, queries: Sequence[Mapping[str, Any]],
    base_rankings: Mapping[str, Mapping[str, Any]], graph_rankings: Mapping[str, Mapping[str, Any]],
    locked_hash: str, selected_weights: Mapping[str, float], model_ids: Sequence[str],
) -> dict[str, list[dict[str, Any]]]:
    chunks_by_id = {row["chunk_id"]: row for row in common["chunks"][domain]}
    input_hashes = {
        "phase13_graph_manifest": sha256_file(common["base"] / "artifacts/manifests/phase13_graph_manifest.json"),
        "phase14_baseline_manifest": sha256_file(common["base"] / "artifacts/manifests/phase14_baseline_manifest.json"),
    }
    result = {model_id: [] for model_id in model_ids}
    for query in queries:
        base = base_rankings[query["query_id"]]
        graph_item = graph_rankings[query["query_id"]]
        for model_id in model_ids:
            ranking, latency, weights = _model_ranking(
                model_id, base, graph_item, common["config"], selected_weights, common["config"]["retrieval_depth"]
            )
            result[model_id].append(
                _prediction_row(
                    query, model_id, ranking, latency, chunks_by_id, locked_hash, common["corpus_hashes"][domain],
                    common["phase14_config"]["answer_layer"], graph_item, weights, input_hashes,
                )
            )
    return result


def _validation_ablation(
    common: Mapping[str, Any], base_by_domain: Mapping[str, Any], graph_by_domain_hop: Mapping[str, Any],
    selected_hops: int, selected_weights: Mapping[str, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    config = common["config"]
    for domain in ("medical", "finance"):
        queries = common["queries"][domain]["validation"]
        variants: dict[str, list[float]] = {name: [] for name in config["ablation"]["variants"]}
        topk_values: dict[int, list[float]] = {k: [] for k in config["ablation"]["top_k_sensitivity"]}
        for query in queries:
            query_id = query["query_id"]
            base = base_by_domain[domain][query_id]
            graph_selected = graph_by_domain_hop[domain][selected_hops][query_id]["ranking"]
            full = weighted_rrf({"sparse": base["B0"], "dense": base["B1"], "graph": graph_selected}, selected_weights, 10, config["B4"]["rrf_k"])
            no_graph_weights = {"sparse": config["baseline"]["B2_sparse_weight"], "dense": 1.0 - config["baseline"]["B2_sparse_weight"]}
            no_graph = weighted_rrf({"sparse": base["B0"], "dense": base["B1"]}, no_graph_weights, 10, config["B4"]["rrf_k"])
            sd = selected_weights["sparse"] + selected_weights["graph"]
            no_dense = weighted_rrf(
                {"sparse": base["B0"], "graph": graph_selected},
                {"sparse": selected_weights["sparse"] / sd, "graph": selected_weights["graph"] / sd}, 10, config["B4"]["rrf_k"],
            )
            dg = selected_weights["dense"] + selected_weights["graph"]
            no_sparse = weighted_rrf(
                {"dense": base["B1"], "graph": graph_selected},
                {"dense": selected_weights["dense"] / dg, "graph": selected_weights["graph"] / dg}, 10, config["B4"]["rrf_k"],
            )
            rankings = {"full": full, "no_graph": no_graph, "no_dense": no_dense, "no_sparse": no_sparse}
            for hops in (1, 2):
                graph_hop = graph_by_domain_hop[domain][hops][query_id]["ranking"]
                rankings[f"hop_{hops}"] = weighted_rrf(
                    {"sparse": base["B0"], "dense": base["B1"], "graph": graph_hop}, selected_weights, 10, config["B4"]["rrf_k"]
                )
            for name, ranking in rankings.items():
                variants[name].append(_hit(ranking, query.get("gold_chunk_ids", []), 5))
            for k in topk_values:
                topk_values[k].append(_hit(full, query.get("gold_chunk_ids", []), k))
        for name, values in variants.items():
            rows.append({"domain": domain, "variant": name, "metric": "chunk_recall_at_5", "value": round(float(np.mean(values)), 6)})
        for k, values in topk_values.items():
            rows.append({"domain": domain, "variant": f"full_top_k_{k}", "metric": f"chunk_recall_at_{k}", "value": round(float(np.mean(values)), 6)})
    return rows


def _challenge_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Evaluate the explicit abstention contract for OOD/adversarial queries."""
    if not rows:
        raise ValueError("Challenge prediction rows are required")
    by_type: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        by_type.setdefault(str(row.get("challenge_type", "unknown")), []).append(row)

    def summarize(items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        count = len(items)
        abstained = sum(bool(row.get("abstained")) for row in items)
        citation_free = sum(not row.get("citations") for row in items)
        matches = sum(
            row.get("expected_behavior") == "abstain" and bool(row.get("abstained")) and not row.get("citations")
            for row in items
        )
        return {
            "query_count": count,
            "abstention_rate": round(abstained / count, 6),
            "citation_free_rate": round(citation_free / count, 6),
            "expected_behavior_match_rate": round(matches / count, 6),
        }

    return {**summarize(rows), "by_challenge_type": {name: summarize(items) for name, items in sorted(by_type.items())}}


def _write_validation_artifacts(common: Mapping[str, Any]) -> dict[str, Any]:
    base = common["base"]
    config = common["config"]
    base_by_domain: dict[str, Any] = {}
    graph_by_domain_hop: dict[str, dict[int, Any]] = {"medical": {}, "finance": {}}
    for domain in ("medical", "finance"):
        bm25, dense = common["indexes"][domain]
        queries = common["queries"][domain]["validation"]
        base_by_domain[domain] = _base_rankings(
            queries, bm25, dense, config["candidate_depth"], common["phase14_config"]["runtime"]["dense_batch_size"]
        )
        for hops in config["B3"]["candidate_max_hops"]:
            graph_by_domain_hop[domain][hops] = _graph_rankings(
                queries, base_by_domain[domain], common["graphs"][domain], hops, config["candidate_depth"]
            )
    selected, tuning_rows = _tune(common, base_by_domain, graph_by_domain_hop)
    locked = {
        "schema_version": 1, "generated_at": config["generated_at"],
        "base_config_sha256": sha256_file(base / "config/phase15.json"),
        "phase13_graph_manifest_sha256": sha256_file(base / "artifacts/manifests/phase13_graph_manifest.json"),
        "phase14_locked_config_sha256": sha256_file(base / "config/phase14_locked.json"),
        "selected_max_hops": selected["max_hops"], "selected_weights": selected["weights"],
        "selection_split": "validation", "selection_metric": config["B4"]["selection_metric"],
        "test_status": "SEALED_NOT_RUN",
    }
    locked_path = base / "config/phase15_locked.json"
    locked_path.write_text(json.dumps(locked, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    locked_hash = sha256_file(locked_path)
    tuning = {
        "schema_version": 1, "selected": selected, "candidates": tuning_rows,
        "locked_config_sha256": locked_hash, "test_status": "SEALED_NOT_RUN",
    }
    metrics_dir = base / "artifacts/metrics"
    predictions_root = base / "artifacts/predictions/phase15"
    manifests_dir = base / "artifacts/manifests"
    for directory in (metrics_dir, predictions_root, manifests_dir):
        directory.mkdir(parents=True, exist_ok=True)
    tuning_path = metrics_dir / "phase15_tuning.json"
    tuning_path.write_text(json.dumps(tuning, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation_metrics: dict[str, Any] = {}
    challenge_metrics: dict[str, Any] = {}
    prediction_artifacts: list[Path] = []
    for domain in ("medical", "finance"):
        graph_selected = graph_by_domain_hop[domain][selected["max_hops"]]
        predictions = _make_predictions(
            common, domain, common["queries"][domain]["validation"], base_by_domain[domain], graph_selected,
            locked_hash, selected["weights"], ("B3", "B4"),
        )
        validation_metrics[domain] = {}
        for model_id, rows in predictions.items():
            path = predictions_root / domain / f"{model_id}_validation.jsonl"
            write_jsonl(path, rows)
            prediction_artifacts.append(path)
            validation_metrics[domain][model_id] = prediction_metrics(rows, config["top_k"])

        challenge_queries = common["challenges"][domain]
        bm25, dense = common["indexes"][domain]
        challenge_base = _base_rankings(
            challenge_queries, bm25, dense, config["candidate_depth"], common["phase14_config"]["runtime"]["dense_batch_size"]
        )
        challenge_graph = _graph_rankings(
            challenge_queries, challenge_base, common["graphs"][domain], selected["max_hops"], config["candidate_depth"]
        )
        challenge_predictions = _make_predictions(
            common, domain, challenge_queries, challenge_base, challenge_graph,
            locked_hash, selected["weights"], ("B3", "B4"),
        )
        challenge_metrics[domain] = {}
        for model_id, rows in challenge_predictions.items():
            path = predictions_root / domain / f"{model_id}_challenge.jsonl"
            write_jsonl(path, rows)
            prediction_artifacts.append(path)
            challenge_metrics[domain][model_id] = _challenge_metrics(rows)
    ablation_rows = _validation_ablation(common, base_by_domain, graph_by_domain_hop, selected["max_hops"], selected["weights"])
    ablation_path = metrics_dir / "phase15_ablation_validation.csv"
    with ablation_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("domain", "variant", "metric", "value"))
        writer.writeheader(); writer.writerows(ablation_rows)
    validation_path = metrics_dir / "phase15_validation_metrics.json"
    validation_path.write_text(
        json.dumps(
            {"config_sha256": locked_hash, "validation": validation_metrics, "challenge": challenge_metrics, "ablation": ablation_rows},
            ensure_ascii=False, indent=2, sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    validation_manifest = {
        "status": "VALIDATION_LOCKED", "generated_at": config["generated_at"], "locked_config_sha256": locked_hash,
        "test_status": "SEALED_NOT_RUN", "selected": selected,
        "artifacts": [
            {"path": path.relative_to(common["base"].parents[1]).as_posix(), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in (locked_path, tuning_path, validation_path, ablation_path, *sorted(prediction_artifacts))
        ],
    }
    validation_manifest_path = manifests_dir / "phase15_validation_manifest.json"
    validation_manifest_path.write_text(json.dumps(validation_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "locked_config_sha256": locked_hash,
        "selected": selected,
        "validation_metrics": validation_metrics,
        "challenge_metrics": challenge_metrics,
    }


def _test_query_hash(common: Mapping[str, Any]) -> str:
    return stable_hash(
        {domain: [row["query_id"] for row in common["queries"][domain]["test"]] for domain in ("medical", "finance")}
    )


def _execute_or_reuse_test(common: Mapping[str, Any], locked: Mapping[str, Any], locked_hash: str) -> str:
    base = common["base"]
    run_path = base / "artifacts/manifests/phase15_test_run.json"
    existing = json.loads(run_path.read_text(encoding="utf-8")) if run_path.exists() else None
    query_hash = _test_query_hash(common)
    decision = decide_test_run(existing, locked_hash, query_hash)
    if decision == "reuse":
        return "reused"
    reservation = {
        "status": "RUNNING", "run_count": 1, "started_at": common["config"]["generated_at"],
        "locked_config_sha256": locked_hash, "query_set_sha256": query_hash,
    }
    run_path.write_text(json.dumps(reservation, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    prediction_paths: list[Path] = []
    for domain in ("medical", "finance"):
        queries = common["queries"][domain]["test"]
        bm25, dense = common["indexes"][domain]
        base_rankings = _base_rankings(
            queries, bm25, dense, common["config"]["candidate_depth"], common["phase14_config"]["runtime"]["dense_batch_size"]
        )
        graph_rankings = _graph_rankings(
            queries, base_rankings, common["graphs"][domain], locked["selected_max_hops"], common["config"]["candidate_depth"]
        )
        predictions = _make_predictions(
            common, domain, queries, base_rankings, graph_rankings, locked_hash, locked["selected_weights"],
            ("B0", "B1", "B2", "B3", "B4"),
        )
        for model_id, rows in predictions.items():
            path = base / f"artifacts/predictions/phase15/{domain}/{model_id}_test.jsonl"
            write_jsonl(path, rows)
            prediction_paths.append(path)
    complete = {
        **reservation,
        "status": "COMPLETE",
        "completed_at": common["config"]["generated_at"],
        "prediction_artifacts": [
            {"path": path.relative_to(common["base"].parents[1]).as_posix(), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in sorted(prediction_paths)
        ],
    }
    run_path.write_text(json.dumps(complete, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return "executed"


def _bar_svg(path: Path, title: str, rows: Sequence[tuple[str, float]], maximum: float = 1.0) -> None:
    width, height = 1100, 430
    colors = {"B0": "#2563eb", "B1": "#7c3aed", "B2": "#0891b2", "B3": "#ea580c", "B4": "#059669"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<style>text{font-family:Arial,sans-serif}.title{font-size:23px;font-weight:700;fill:#0f172a}.lab{font-size:11px;fill:#334155}.val{font-size:11px;font-weight:700;fill:#0f172a}</style>',
        f'<text x="40" y="42" class="title">{escape(title)}</text>',
    ]
    step = 1000 / max(len(rows), 1)
    bar_width = max(22, step - 16)
    for index, (label, value) in enumerate(rows):
        x = 50 + index * step
        h = 270 * min(max(value / max(maximum, 1e-9), 0.0), 1.0)
        y = 345 - h
        model = label.split("-")[-1]
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{h:.1f}" rx="4" fill="{colors.get(model, "#64748b")}"/>')
        parts.append(f'<text x="{x + bar_width/2:.1f}" y="365" text-anchor="middle" class="lab">{escape(label)}</text>')
        parts.append(f'<text x="{x + bar_width/2:.1f}" y="{max(72, y-7):.1f}" text-anchor="middle" class="val">{value:.3f}</text>')
    parts.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def _build_notebook(path: Path) -> None:
    cells: list[dict[str, Any]] = [
        {"cell_type": "markdown", "metadata": {}, "source": ["# Chương 5 — KG–RAG B0–B4\n", "TEST được chạy đúng một lần sau validation lock.\n"]},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": [
            "import json\n", "from pathlib import Path\n", "ROOT=Path.cwd()\n",
            "metrics=json.loads((ROOT/'term_paper/knowledge_rag/artifacts/metrics/phase15_test_metrics.json').read_text(encoding='utf-8'))\n",
            "print(metrics['test_run_status'])\n",
        ]},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": [
            "summary={d:{m:v['chunk_recall_at_5'] for m,v in models.items()} for d,models in metrics['test'].items()}\n",
            "print(json.dumps(summary,indent=2,sort_keys=True))\n",
        ]},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": [
            "print('No hallucination-reduction claim; citation validity and unsupported-answer categories are reported directly.')\n",
        ]},
    ]
    namespace: dict[str, Any] = {}
    count = 0
    for cell in cells:
        if cell["cell_type"] != "code": continue
        count += 1; output = io.StringIO()
        with contextlib.redirect_stdout(output): exec("".join(cell["source"]), namespace)
        cell["execution_count"] = count
        cell["outputs"] = [{"name": "stdout", "output_type": "stream", "text": output.getvalue().splitlines(keepends=True)}]
    notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": platform.python_version()}}, "nbformat": 4, "nbformat_minor": 5}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _finalize(common: Mapping[str, Any], locked: Mapping[str, Any], locked_hash: str, test_mode: str) -> dict[str, Any]:
    base = common["base"]
    metrics_dir = base / "artifacts/metrics"
    figures_dir = base / "artifacts/figures/phase15"
    manifests_dir = base / "artifacts/manifests"
    predictions_root = base / "artifacts/predictions/phase15"
    test_metrics: dict[str, dict[str, Any]] = {}
    prediction_rows: dict[str, dict[str, list[dict[str, Any]]]] = {}
    metrics_csv_rows: list[dict[str, Any]] = []
    bootstrap_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []
    case_rows: list[dict[str, Any]] = []
    error_counts: dict[str, Counter[str]] = {}
    effect_counts: dict[str, Counter[str]] = {}
    for domain in ("medical", "finance"):
        prediction_rows[domain] = {}
        test_metrics[domain] = {}
        for model_id in ("B0", "B1", "B2", "B3", "B4"):
            rows = read_jsonl(predictions_root / domain / f"{model_id}_test.jsonl")
            prediction_rows[domain][model_id] = rows
            values = prediction_metrics(rows, common["config"]["top_k"])
            if domain == "finance":
                values["execution_accuracy"] = values["normalized_exact_match"]
                values["program_accuracy"] = None
            test_metrics[domain][model_id] = values
            metrics_csv_rows.append({"domain": domain, "model_id": model_id, **values})
            hits = [float(bool(set(row["ranked_chunk_ids"][:5]) & set(row["gold_chunk_ids"]))) for row in rows]
            ci = bootstrap_mean_ci(hits, common["config"]["bootstrap"]["seed"], common["config"]["bootstrap"]["n_resamples"], common["config"]["bootstrap"]["confidence"])
            bootstrap_rows.append({"domain": domain, "comparison": f"{model_id}_recall_at_5", **ci})
        b2_by_id = {row["query_id"]: row for row in prediction_rows[domain]["B2"]}
        error_counts[domain] = Counter(); effect_counts[domain] = Counter()
        for row in prediction_rows[domain]["B4"]:
            categories = categorize_error(row, int(row["graph_candidate_count"]))
            effect = classify_kg_effect(
                b2_by_id[row["query_id"]]["ranked_chunk_ids"], row["ranked_chunk_ids"], set(row["gold_chunk_ids"]), 5
            )
            error_counts[domain].update(categories); effect_counts[domain][effect] += 1
            error_rows.append({
                "domain": domain, "split": "test", "challenge_type": "", "query_id": row["query_id"],
                "categories": "|".join(categories), "kg_effect_vs_B2_at_5": effect,
                "graph_candidate_count": row["graph_candidate_count"], "gold_hit_at_5": bool(set(row["ranked_chunk_ids"][:5]) & set(row["gold_chunk_ids"])),
                "abstained": row["abstained"], "citations": "|".join(row["citations"]),
            })
        challenge_b4 = read_jsonl(predictions_root / domain / "B4_challenge.jsonl")
        for row in challenge_b4:
            categories = categorize_error(row, int(row["graph_candidate_count"]))
            error_counts[domain].update(categories)
            error_rows.append({
                "domain": domain, "split": "challenge", "challenge_type": row.get("challenge_type", ""),
                "query_id": row["query_id"], "categories": "|".join(categories), "kg_effect_vs_B2_at_5": "not_applicable",
                "graph_candidate_count": row["graph_candidate_count"], "gold_hit_at_5": False,
                "abstained": row["abstained"], "citations": "|".join(row["citations"]),
            })
        for outcome in ("helps", "hurts", "neutral"):
            selected = [row for row in error_rows if row["domain"] == domain and row["kg_effect_vs_B2_at_5"] == outcome][:3]
            for item in selected:
                b4 = next(row for row in prediction_rows[domain]["B4"] if row["query_id"] == item["query_id"])
                b2 = b2_by_id[item["query_id"]]
                case_rows.append({
                    "domain": domain, "outcome": outcome, "query_id": item["query_id"], "question": b4["question"],
                    "gold_chunk_ids": b4["gold_chunk_ids"], "B2_ranked_chunk_ids": b2["ranked_chunk_ids"],
                    "B4_ranked_chunk_ids": b4["ranked_chunk_ids"], "graph_candidate_count": b4["graph_candidate_count"],
                    "graph_anchor_node_ids": b4["graph_anchor_node_ids"], "graph_trace_node_ids": b4["graph_trace_node_ids"],
                })
        paired_delta = [
            float(bool(set(b4["ranked_chunk_ids"][:5]) & set(b4["gold_chunk_ids"]))) -
            float(bool(set(b2_by_id[b4["query_id"]]["ranked_chunk_ids"][:5]) & set(b4["gold_chunk_ids"])))
            for b4 in prediction_rows[domain]["B4"]
        ]
        delta_ci = bootstrap_mean_ci(paired_delta, common["config"]["bootstrap"]["seed"], common["config"]["bootstrap"]["n_resamples"], common["config"]["bootstrap"]["confidence"])
        bootstrap_rows.append({"domain": domain, "comparison": "B4_minus_B2_recall_at_5", **delta_ci})

    validation = json.loads((metrics_dir / "phase15_validation_metrics.json").read_text(encoding="utf-8"))
    phase14_metrics = json.loads((metrics_dir / "phase14_metrics.json").read_text(encoding="utf-8"))
    combined_validation: dict[str, Any] = {}
    for domain in ("medical", "finance"):
        combined_validation[domain] = {**phase14_metrics["validation"][domain], **validation["validation"][domain]}
    metrics_payload = {
        "schema_version": 1, "generated_at": common["config"]["generated_at"], "config_sha256": locked_hash,
        "test_run_status": "COMPLETE_ONE_SHOT", "test_run_mode": test_mode,
        "validation": combined_validation, "test": test_metrics,
        "challenge": validation.get("challenge", {}),
        "error_category_counts": {domain: dict(sorted(counts.items())) for domain, counts in error_counts.items()},
        "kg_effect_counts_vs_B2_at_5": {domain: dict(sorted(counts.items())) for domain, counts in effect_counts.items()},
        "claim_policy": "No hallucination-reduction claim; report citation validity and unsupported-answer errors directly.",
    }
    metrics_path = metrics_dir / "phase15_test_metrics.json"
    metrics_path.write_text(json.dumps(metrics_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    test_csv = metrics_dir / "phase15_test_metrics.csv"
    fields = ["domain", "model_id", "query_count", "chunk_recall_at_1", "chunk_recall_at_3", "chunk_recall_at_5", "chunk_recall_at_10", "document_recall_at_5", "mrr_at_10", "normalized_exact_match", "token_f1", "citation_validity", "citation_gold_precision", "abstention_rate", "latency_ms_p50", "latency_ms_p95"]
    with test_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore"); writer.writeheader(); writer.writerows(metrics_csv_rows)
    bootstrap_path = metrics_dir / "phase15_bootstrap_ci.csv"
    with bootstrap_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("domain", "comparison", "mean", "lower", "upper", "confidence", "n_resamples")); writer.writeheader(); writer.writerows(bootstrap_rows)
    error_path = metrics_dir / "phase15_error_analysis.csv"
    with error_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=error_rows[0].keys()); writer.writeheader(); writer.writerows(error_rows)
    cases_path = metrics_dir / "phase15_case_studies.jsonl"; write_jsonl(cases_path, case_rows)
    figures = {
        "test_recall_at_5.svg": ("TEST chunk Recall@5 — B0–B4", [(f"{d[:3]}-{m}", test_metrics[d][m]["chunk_recall_at_5"]) for d in ("medical", "finance") for m in ("B0", "B1", "B2", "B3", "B4")], 1.0),
        "test_mrr_at_10.svg": ("TEST MRR@10 — B0–B4", [(f"{d[:3]}-{m}", test_metrics[d][m]["mrr_at_10"]) for d in ("medical", "finance") for m in ("B0", "B1", "B2", "B3", "B4")], 1.0),
        "test_answer_f1.svg": ("TEST grounded answer token F1", [(f"{d[:3]}-{m}", test_metrics[d][m]["token_f1"]) for d in ("medical", "finance") for m in ("B0", "B1", "B2", "B3", "B4")], 1.0),
        "test_latency_p95.svg": ("TEST retrieval latency p95 (ms)", [(f"{d[:3]}-{m}", test_metrics[d][m]["latency_ms_p95"]) for d in ("medical", "finance") for m in ("B0", "B1", "B2", "B3", "B4")], max(test_metrics[d][m]["latency_ms_p95"] for d in ("medical", "finance") for m in ("B0", "B1", "B2", "B3", "B4")) * 1.1),
        "validation_ablation.svg": ("Validation ablation — chunk Recall@5", [(f"{row['domain'][:3]}-{row['variant']}", row["value"]) for row in validation["ablation"] if row["metric"] == "chunk_recall_at_5"], 1.0),
        "error_distribution.svg": ("B4 TEST error categories (count)", [(f"{d[:3]}-{k}", float(v)) for d, counts in error_counts.items() for k, v in sorted(counts.items())], max(max(counts.values(), default=1) for counts in error_counts.values()) * 1.1),
    }
    for filename, (title, rows, maximum) in figures.items(): _bar_svg(figures_dir / filename, title, rows, maximum)
    notebook_path = base / "notebooks/ch5_kgrag_b0_b4.ipynb"; _build_notebook(notebook_path)
    report_path = base / "phase15_experiment_report.md"
    lines = ["# Phase 15 experiment report", "", "- TEST was executed exactly once after validation lock.", f"- Locked config SHA-256: `{locked_hash}`.", "- No claim of hallucination reduction is made; citation validity and unsupported-answer errors are reported.", "", "## TEST summary", "", "| Domain | Model | R@5 | MRR@10 | Token F1 | p95 ms |", "|---|---:|---:|---:|---:|---:|"]
    for domain in ("medical", "finance"):
        for model in ("B0", "B1", "B2", "B3", "B4"):
            row = test_metrics[domain][model]; lines.append(f"| {domain} | {model} | {row['chunk_recall_at_5']:.3f} | {row['mrr_at_10']:.3f} | {row['token_f1']:.3f} | {row['latency_ms_p95']:.2f} |")
    lines += [
        "", "## Challenge/OOD abstention", "",
        "| Domain | Model | Abstention | Citation-free | Expected behavior |", "|---|---:|---:|---:|---:|",
    ]
    for domain in ("medical", "finance"):
        for model in ("B3", "B4"):
            row = metrics_payload["challenge"][domain][model]
            lines.append(
                f"| {domain} | {model} | {row['abstention_rate']:.3f} | {row['citation_free_rate']:.3f} | {row['expected_behavior_match_rate']:.3f} |"
            )
    lines += ["", "## Observed KG effects vs B2 at Recall@5", "", json.dumps(metrics_payload["kg_effect_counts_vs_B2_at_5"], ensure_ascii=False, sort_keys=True)]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    generated = [base / "config/phase15.json", base / "config/phase15_locked.json", metrics_dir / "phase15_tuning.json", metrics_dir / "phase15_validation_metrics.json", metrics_dir / "phase15_ablation_validation.csv", metrics_path, test_csv, bootstrap_path, error_path, cases_path, notebook_path, report_path, base / "artifacts/manifests/phase15_test_run.json"]
    generated.extend(figures_dir / filename for filename in figures)
    generated.extend(sorted(predictions_root.rglob("*.jsonl")))
    workspace = common["base"].parents[1]
    manifest = {
        "schema_version": 1, "generated_at": common["config"]["generated_at"], "status": "PASS",
        "models": ["B0", "B1", "B2", "B3", "B4"], "domains": ["medical", "finance"],
        "locked_config_sha256": locked_hash, "test_run_count": 1, "test_run_status": "COMPLETE",
        "test_query_set_sha256": _test_query_hash(common), "top_k": common["config"]["top_k"],
        "artifacts": [{"path": path.relative_to(workspace).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in sorted(generated)],
    }
    manifest_path = manifests_dir / "phase15_experiment_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "PASS", "test_mode": test_mode, "locked_config_sha256": locked_hash, "test_metrics": test_metrics, "manifest": manifest_path.relative_to(workspace).as_posix()}


def build_phase15(workspace: Path, execute_test: bool = False) -> dict[str, Any]:
    common = _load_common(workspace)
    locked_path = common["base"] / "config/phase15_locked.json"
    validation_manifest = common["base"] / "artifacts/manifests/phase15_validation_manifest.json"
    if not execute_test or not locked_path.exists() or not validation_manifest.exists():
        validation_result = _write_validation_artifacts(common)
        if not execute_test:
            return {"status": "VALIDATION_LOCKED", **validation_result}
    locked = json.loads(locked_path.read_text(encoding="utf-8"))
    locked_hash = sha256_file(locked_path)
    test_mode = _execute_or_reuse_test(common, locked, locked_hash)
    return _finalize(common, locked, locked_hash, test_mode)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-test", action="store_true", help="Run the sealed TEST split once after validation lock")
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parents[2]
    result = build_phase15(workspace, execute_test=args.execute_test)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
