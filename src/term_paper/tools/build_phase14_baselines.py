"""Build, tune, evaluate, and package Phase 14 B0-B2 baselines."""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import platform
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from xml.sax.saxutils import escape

import joblib
import numpy as np
import scipy
import sklearn

from term_paper.tools.phase14_rag import (
    BM25Index,
    DenseLSAIndex,
    build_cache_manifest,
    grounded_answer,
    prediction_metrics,
    reciprocal_rank_fusion,
    stable_hash,
    validate_cache_manifest,
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


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def _domain_corpus_hash(chunks: Sequence[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in chunks:
        digest.update(str(row["chunk_id"]).encode("utf-8"))
        digest.update(b"\x1f")
        digest.update(str(row["text"]).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _cache_valid(cache_dir: Path, corpus_hash: str, config_hash: str) -> bool:
    manifest_path = cache_dir / "cache_manifest.json"
    if not manifest_path.exists():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_cache_manifest(manifest, corpus_hash, config_hash)
        for relative, expected_hash in manifest["artifact_files"].items():
            path = cache_dir / relative
            if not path.exists() or sha256_file(path) != expected_hash:
                return False
        return True
    except (OSError, ValueError, json.JSONDecodeError, KeyError):
        return False


def _build_or_load_indexes(
    base: Path,
    domain: str,
    chunks: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    config_hash: str,
) -> tuple[BM25Index, DenseLSAIndex, dict[str, Any], bool]:
    cache_dir = base / f"data/processed/phase14/indexes/{domain}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    corpus_hash = _domain_corpus_hash(chunks)
    bm25_path = cache_dir / "bm25.joblib"
    dense_path = cache_dir / "dense_lsa.joblib"
    reused = _cache_valid(cache_dir, corpus_hash, config_hash)
    if reused:
        return (
            joblib.load(bm25_path),
            joblib.load(dense_path),
            json.loads((cache_dir / "cache_manifest.json").read_text(encoding="utf-8")),
            True,
        )
    doc_ids = [row["chunk_id"] for row in chunks]
    texts = [row["text"] for row in chunks]
    b0 = config["models"]["B0"]
    b1 = config["models"]["B1"]
    bm25 = BM25Index.fit(doc_ids, texts, k1=b0["k1"], b=b0["b"])
    dense = DenseLSAIndex.fit(
        doc_ids,
        texts,
        n_components=b1["dimensions"],
        seed=config["seed"],
        max_features=b1["max_features"],
        min_df=b1[f"{domain}_min_df"],
    )
    joblib.dump(bm25, bm25_path, compress=3)
    joblib.dump(dense, dense_path, compress=3)
    artifact_files = {"bm25.joblib": sha256_file(bm25_path), "dense_lsa.joblib": sha256_file(dense_path)}
    manifest = build_cache_manifest("B0+B1", corpus_hash, config_hash, len(chunks), artifact_files)
    manifest.update(
        {
            "domain": domain,
            "chunk_ids_sha256": stable_hash(doc_ids),
            "dense_dimensions": int(dense.vectors.shape[1]),
            "libraries": {
                "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__, "scikit_learn": sklearn.__version__,
            },
        }
    )
    (cache_dir / "cache_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return bm25, dense, manifest, False


def _base_rankings(
    queries: Sequence[Mapping[str, Any]],
    bm25: BM25Index,
    dense: DenseLSAIndex,
    depth: int,
    dense_batch_size: int,
) -> dict[str, dict[str, Any]]:
    texts = [str(row["question"]) for row in queries]
    dense_start = time.perf_counter()
    dense_rankings = dense.search_batch(texts, top_k=depth, batch_size=dense_batch_size)
    dense_elapsed = (time.perf_counter() - dense_start) * 1000.0
    dense_per_query = dense_elapsed / max(len(queries), 1)
    result: dict[str, dict[str, Any]] = {}
    for query, dense_ranking in zip(queries, dense_rankings):
        sparse_start = time.perf_counter()
        sparse_ranking = bm25.search(str(query["question"]), top_k=depth)
        sparse_elapsed = (time.perf_counter() - sparse_start) * 1000.0
        result[str(query["query_id"])] = {
            "B0": sparse_ranking,
            "B1": dense_ranking,
            "B0_latency_ms": sparse_elapsed,
            "B1_latency_ms": dense_per_query,
        }
    return result


def _recall_at(ranking: Sequence[tuple[str, float]], gold: Sequence[str], k: int) -> float:
    return float(bool({item[0] for item in ranking[:k]} & set(gold)))


def _tune_weight(
    validation: Mapping[str, Sequence[Mapping[str, Any]]],
    base_rankings: Mapping[str, Mapping[str, Mapping[str, Any]]],
    candidates: Sequence[float],
    rrf_k: int,
) -> tuple[float, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    for weight in sorted(float(value) for value in candidates):
        domain_scores: dict[str, float] = {}
        for domain, queries in validation.items():
            scores = []
            for query in queries:
                base = base_rankings[domain][query["query_id"]]
                fused = reciprocal_rank_fusion(base["B0"], base["B1"], weight, 5, rrf_k)
                scores.append(_recall_at(fused, query.get("gold_chunk_ids", []), 5))
            domain_scores[domain] = float(np.mean(scores)) if scores else 0.0
        macro = float(np.mean(list(domain_scores.values())))
        rows.append(
            {
                "sparse_weight": weight,
                "medical_chunk_recall_at_5": round(domain_scores.get("medical", 0.0), 6),
                "finance_chunk_recall_at_5": round(domain_scores.get("finance", 0.0), 6),
                "macro_domain_chunk_recall_at_5": round(macro, 6),
            }
        )
    selected = min(rows, key=lambda row: (-row["macro_domain_chunk_recall_at_5"], row["sparse_weight"]))
    return float(selected["sparse_weight"]), rows


def _prediction_row(
    query: Mapping[str, Any],
    model_id: str,
    ranking: Sequence[tuple[str, float]],
    latency_ms: float,
    chunks_by_id: Mapping[str, Mapping[str, Any]],
    locked_config_hash: str,
    corpus_hash: str,
    answer_config: Mapping[str, Any],
    fusion_weight: float | None,
) -> dict[str, Any]:
    ranking = list(ranking)
    answer = grounded_answer(
        str(query["question"]),
        ranking,
        {chunk_id: str(chunks_by_id[chunk_id]["text"]) for chunk_id, _ in ranking if chunk_id in chunks_by_id},
        minimum_overlap_terms=answer_config["minimum_overlap_terms"],
        minimum_overlap_ratio=answer_config["minimum_overlap_ratio"],
        unsafe_patterns=answer_config["unsafe_patterns"],
        maximum_characters=answer_config["maximum_characters"],
    )
    ranked_chunk_ids = [chunk_id for chunk_id, _ in ranking]
    ranked_document_ids = [chunks_by_id[chunk_id]["document_id"] for chunk_id in ranked_chunk_ids]
    return {
        "prediction_id": f"p14-{stable_hash([model_id, query['query_id'], locked_config_hash])[:24]}",
        "model_id": model_id,
        "domain": query["domain"],
        "dataset": query.get("dataset", "challenge"),
        "split": query["split"],
        "query_id": query["query_id"],
        "question": query["question"],
        "ranked_chunk_ids": ranked_chunk_ids,
        "ranked_document_ids": ranked_document_ids,
        "retrieval_scores": [round(float(score), 8) for _, score in ranking],
        "retrieved_chunk_ids": ranked_chunk_ids,
        "gold_chunk_ids": list(query.get("gold_chunk_ids", [])),
        "gold_document_ids": list(query.get("gold_document_ids", [])),
        "gold_answer": query.get("gold_answer", ""),
        "answer": answer["answer"],
        "citations": answer["citations"],
        "abstained": answer["abstained"],
        "abstention_reason": answer["reason"],
        "latency_ms": round(float(latency_ms), 6),
        "config_sha256": locked_config_hash,
        "corpus_sha256": corpus_hash,
        "query_source_path": query.get("raw_source_path", "phase12/challenge_queries.jsonl"),
        "fusion_sparse_weight": fusion_weight,
    }


def _make_predictions(
    queries: Sequence[Mapping[str, Any]],
    base_rankings: Mapping[str, Mapping[str, Any]],
    model_id: str,
    selected_weight: float,
    rrf_k: int,
    output_depth: int,
    chunks_by_id: Mapping[str, Mapping[str, Any]],
    locked_config_hash: str,
    corpus_hash: str,
    answer_config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    predictions: list[dict[str, Any]] = []
    for query in queries:
        base = base_rankings[query["query_id"]]
        fusion_weight: float | None = None
        if model_id == "B0":
            ranking = base["B0"][:output_depth]
            latency = base["B0_latency_ms"]
        elif model_id == "B1":
            ranking = base["B1"][:output_depth]
            latency = base["B1_latency_ms"]
        else:
            start = time.perf_counter()
            ranking = reciprocal_rank_fusion(base["B0"], base["B1"], selected_weight, output_depth, rrf_k)
            latency = base["B0_latency_ms"] + base["B1_latency_ms"] + (time.perf_counter() - start) * 1000.0
            fusion_weight = selected_weight
        predictions.append(
            _prediction_row(
                query, model_id, ranking, latency, chunks_by_id, locked_config_hash, corpus_hash, answer_config, fusion_weight
            )
        )
    return predictions


def _bar_svg(path: Path, title: str, subtitle: str, rows: Sequence[tuple[str, float]], maximum: float, suffix: str = "") -> None:
    width, height = 980, 420
    colors = {"B0": "#2563eb", "B1": "#7c3aed", "B2": "#059669"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<style>text{font-family:Arial,sans-serif}.title{font-size:23px;font-weight:700;fill:#0f172a}.sub{font-size:13px;fill:#475569}.lab{font-size:12px;fill:#334155}.val{font-size:12px;font-weight:700;fill:#0f172a}</style>',
        f'<text x="45" y="42" class="title">{escape(title)}</text>',
        f'<text x="45" y="66" class="sub">{escape(subtitle)}</text>',
    ]
    bar_width = max(24, int(760 / max(len(rows), 1)) - 16)
    for index, (label, value) in enumerate(rows):
        x = 70 + index * (bar_width + 16)
        bar_height = 260 * min(max(value / max(maximum, 1e-9), 0.0), 1.0)
        y = 340 - bar_height
        model = label.split("-")[-1]
        parts.append(f'<rect x="{x}" y="{y:.2f}" width="{bar_width}" height="{bar_height:.2f}" rx="5" fill="{colors.get(model, "#64748b")}"/>')
        parts.append(f'<text x="{x + bar_width / 2:.1f}" y="360" text-anchor="middle" class="lab">{escape(label)}</text>')
        parts.append(f'<text x="{x + bar_width / 2:.1f}" y="{max(88, y - 8):.1f}" text-anchor="middle" class="val">{value:.3f}{escape(suffix)}</text>')
    parts.append('</svg>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")


def _build_notebook(path: Path, metrics_relative: str, tuning_relative: str, metrics: Mapping[str, Any], tuning: Mapping[str, Any]) -> None:
    cells = [
        {
            "cell_type": "markdown", "metadata": {},
            "source": ["# Chương 5 — RAG baselines B0–B2\n", "Notebook đọc artifact đã khóa; không chạy hoặc tune trên TEST.\n"],
        },
        {
            "cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": [
                "import json\n", "from pathlib import Path\n", "ROOT = Path.cwd()\n",
                f"metrics = json.loads((ROOT / '{metrics_relative}').read_text(encoding='utf-8'))\n",
                f"tuning = json.loads((ROOT / '{tuning_relative}').read_text(encoding='utf-8'))\n",
                "print(metrics['test_split_status'])\n",
            ],
        },
        {
            "cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": [
                "summary = {domain: {model: values['chunk_recall_at_5'] for model, values in models.items()} for domain, models in metrics['validation'].items()}\n",
                "print(json.dumps(summary, indent=2, sort_keys=True))\n",
            ],
        },
        {
            "cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": ["print('Selected B2 sparse weight:', tuning['selected_sparse_weight'])\n"],
        },
    ]
    namespace: dict[str, Any] = {}
    execution_count = 0
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        execution_count += 1
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec("".join(cell["source"]), namespace)
        cell["execution_count"] = execution_count
        cell["outputs"] = [{"name": "stdout", "output_type": "stream", "text": output.getvalue().splitlines(keepends=True)}]
    notebook = {
        "cells": cells,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": platform.python_version()}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _artifact_row(workspace: Path, path: Path) -> dict[str, Any]:
    return {"path": path.relative_to(workspace).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}


def build_phase14(workspace: Path) -> dict[str, Any]:
    base = workspace / "term_paper/knowledge_rag"
    config_path = base / "config/phase14.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base_config_hash = sha256_file(config_path)
    phase12 = base / "data/processed/phase12"
    chunks_by_domain: dict[str, list[dict[str, Any]]] = {"medical": [], "finance": []}
    for chunk in read_jsonl(phase12 / "chunks.jsonl"):
        chunks_by_domain[chunk["domain"]].append(chunk)
    for domain in chunks_by_domain:
        chunks_by_domain[domain].sort(key=lambda row: row["chunk_id"])
    queries_by_domain: dict[str, dict[str, list[dict[str, Any]]]] = {
        domain: {"validation": [], "train": []} for domain in chunks_by_domain
    }
    for query in read_jsonl(phase12 / "queries.jsonl"):
        if query["split"] in ("validation", "train"):
            queries_by_domain[query["domain"]][query["split"]].append(query)
    for domain in queries_by_domain:
        for split in queries_by_domain[domain]:
            queries_by_domain[domain][split].sort(key=lambda row: row["query_id"])
    challenges: dict[str, list[dict[str, Any]]] = {"medical": [], "finance": []}
    for row in read_jsonl(phase12 / "challenge_queries.jsonl"):
        item = dict(row)
        item.update(
            {
                "dataset": "challenge", "split": "challenge", "question": row.get("question", row.get("query", "")),
                "gold_chunk_ids": [], "gold_document_ids": [], "gold_answer": "", "raw_source_path": "term_paper/knowledge_rag/data/processed/phase12/challenge_queries.jsonl",
            }
        )
        challenges[item["domain"]].append(item)
    for domain in challenges:
        challenges[domain].sort(key=lambda row: row["query_id"])

    indexes: dict[str, tuple[BM25Index, DenseLSAIndex]] = {}
    cache_manifests: dict[str, dict[str, Any]] = {}
    cache_reused: dict[str, bool] = {}
    corpus_hashes: dict[str, str] = {}
    base_validation: dict[str, dict[str, dict[str, Any]]] = {}
    for domain in ("medical", "finance"):
        bm25, dense, cache_manifest, reused = _build_or_load_indexes(
            base, domain, chunks_by_domain[domain], config, base_config_hash
        )
        indexes[domain] = (bm25, dense)
        cache_manifests[domain] = cache_manifest
        cache_reused[domain] = reused
        corpus_hashes[domain] = cache_manifest["corpus_sha256"]
        base_validation[domain] = _base_rankings(
            queries_by_domain[domain]["validation"], bm25, dense,
            config["fusion_candidate_depth"], config["runtime"]["dense_batch_size"],
        )

    b2 = config["models"]["B2"]
    selected_weight, tuning_rows = _tune_weight(
        {domain: queries_by_domain[domain]["validation"] for domain in ("medical", "finance")},
        base_validation,
        b2["candidate_sparse_weights"],
        b2["rrf_k"],
    )
    locked_config = {
        "schema_version": 1,
        "generated_at": config["generated_at"],
        "base_config_sha256": base_config_hash,
        "selected_sparse_weight": selected_weight,
        "selection_split": "validation",
        "selection_metric": b2["tuning_metric"],
        "test_split_status": "SEALED_NOT_RUN",
    }
    locked_path = base / "config/phase14_locked.json"
    locked_path.write_text(json.dumps(locked_config, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    locked_hash = sha256_file(locked_path)
    tuning = {
        "schema_version": 1,
        "selected_sparse_weight": selected_weight,
        "selection_split": "validation",
        "metric": b2["tuning_metric"],
        "candidates": tuning_rows,
        "test_split_status": "SEALED_NOT_RUN",
        "locked_config_sha256": locked_hash,
    }
    metrics_dir = base / "artifacts/metrics"
    predictions_root = base / "artifacts/predictions/phase14"
    figures_dir = base / "artifacts/figures/phase14"
    manifests_dir = base / "artifacts/manifests"
    for directory in (metrics_dir, predictions_root, figures_dir, manifests_dir):
        directory.mkdir(parents=True, exist_ok=True)
    tuning_path = metrics_dir / "phase14_tuning.json"
    tuning_path.write_text(json.dumps(tuning, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    all_metrics: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": config["generated_at"],
        "test_split_status": "SEALED_NOT_RUN",
        "config_sha256": locked_hash,
        "selected_sparse_weight": selected_weight,
        "validation": {},
        "train_smoke": {},
        "challenge": {},
        "corpus": {},
    }
    prediction_paths: list[Path] = []
    for domain in ("medical", "finance"):
        chunks_by_id = {row["chunk_id"]: row for row in chunks_by_domain[domain]}
        validation_queries = queries_by_domain[domain]["validation"]
        all_metrics["validation"][domain] = {}
        domain_dir = predictions_root / domain
        for model_id in ("B0", "B1", "B2"):
            predictions = _make_predictions(
                validation_queries, base_validation[domain], model_id, selected_weight, b2["rrf_k"],
                config["retrieval_depth"], chunks_by_id, locked_hash, corpus_hashes[domain], config["answer_layer"],
            )
            path = domain_dir / f"{model_id}_validation.jsonl"
            write_jsonl(path, predictions)
            prediction_paths.append(path)
            model_metrics = prediction_metrics(predictions, config["top_k"])
            if domain == "finance":
                model_metrics["execution_accuracy"] = model_metrics["normalized_exact_match"]
                model_metrics["program_accuracy"] = None
                model_metrics["program_accuracy_note"] = "Not applicable: B0-B2 answer layer is extractive and does not generate programs."
            all_metrics["validation"][domain][model_id] = model_metrics

        train_queries = queries_by_domain[domain]["train"][: config["smoke"]["train_queries_per_domain"]]
        bm25, dense = indexes[domain]
        train_base = _base_rankings(
            train_queries, bm25, dense, config["fusion_candidate_depth"], config["runtime"]["dense_batch_size"]
        )
        all_metrics["train_smoke"][domain] = {}
        for model_id in ("B0", "B1", "B2"):
            rows = _make_predictions(
                train_queries, train_base, model_id, selected_weight, b2["rrf_k"], config["retrieval_depth"],
                chunks_by_id, locked_hash, corpus_hashes[domain], config["answer_layer"],
            )
            path = domain_dir / f"{model_id}_train_smoke.jsonl"
            write_jsonl(path, rows)
            prediction_paths.append(path)
            all_metrics["train_smoke"][domain][model_id] = prediction_metrics(rows, config["top_k"])

        challenge_queries = challenges[domain][: config["smoke"]["challenge_queries_per_domain"]]
        challenge_base = _base_rankings(
            challenge_queries, bm25, dense, config["fusion_candidate_depth"], config["runtime"]["dense_batch_size"]
        )
        all_metrics["challenge"][domain] = {}
        for model_id in ("B0", "B1", "B2"):
            rows = _make_predictions(
                challenge_queries, challenge_base, model_id, selected_weight, b2["rrf_k"], config["retrieval_depth"],
                chunks_by_id, locked_hash, corpus_hashes[domain], config["answer_layer"],
            )
            path = domain_dir / f"{model_id}_challenge.jsonl"
            write_jsonl(path, rows)
            prediction_paths.append(path)
            all_metrics["challenge"][domain][model_id] = {
                "query_count": len(rows),
                "abstention_rate": round(float(np.mean([row["abstained"] for row in rows])), 6),
                "citation_validity": round(
                    float(np.mean([all(citation in row["ranked_chunk_ids"] for citation in row["citations"]) for row in rows])), 6
                ),
            }
        all_metrics["corpus"][domain] = {
            "chunk_count": len(chunks_by_domain[domain]),
            "corpus_sha256": corpus_hashes[domain],
            "cache_reused": cache_reused[domain],
            "dense_dimensions": cache_manifests[domain]["dense_dimensions"],
        }

    metrics_path = metrics_dir / "phase14_metrics.json"
    metrics_path.write_text(json.dumps(all_metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    metrics_csv = metrics_dir / "phase14_metrics.csv"
    metric_fields = [
        "domain", "model_id", "query_count", "chunk_recall_at_1", "chunk_recall_at_3", "chunk_recall_at_5",
        "chunk_recall_at_10", "document_recall_at_1", "document_recall_at_3", "document_recall_at_5",
        "document_recall_at_10", "mrr_at_10", "normalized_exact_match", "token_f1", "citation_validity",
        "citation_gold_precision", "abstention_rate", "latency_ms_p50", "latency_ms_p95",
    ]
    with metrics_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=metric_fields)
        writer.writeheader()
        for domain in ("medical", "finance"):
            for model_id in ("B0", "B1", "B2"):
                writer.writerow({"domain": domain, "model_id": model_id, **{key: all_metrics["validation"][domain][model_id].get(key) for key in metric_fields[2:]}})

    retrieval_rows = [
        (f"{domain[:3]}-{model}", all_metrics["validation"][domain][model]["chunk_recall_at_5"])
        for domain in ("medical", "finance") for model in ("B0", "B1", "B2")
    ]
    answer_rows = [
        (f"{domain[:3]}-{model}", all_metrics["validation"][domain][model]["token_f1"])
        for domain in ("medical", "finance") for model in ("B0", "B1", "B2")
    ]
    latency_rows = [
        (f"{domain[:3]}-{model}", all_metrics["validation"][domain][model]["latency_ms_p95"])
        for domain in ("medical", "finance") for model in ("B0", "B1", "B2")
    ]
    _bar_svg(figures_dir / "retrieval_recall_at_k.svg", "Validation retrieval — Recall@5", "Cùng corpus, query và top-k; TEST chưa chạy.", retrieval_rows, 1.0)
    _bar_svg(figures_dir / "answer_quality.svg", "Grounded extractive answer — token F1", "Câu trả lời luôn trích từ citation hoặc abstain.", answer_rows, 1.0)
    _bar_svg(
        figures_dir / "latency.svg", "Validation retrieval latency — p95", "CPU local; B2 bao gồm B0 + B1 + fusion.",
        latency_rows, max(value for _, value in latency_rows) * 1.1, " ms",
    )

    notebook_path = base / "notebooks/ch5_rag_baselines_b0_b2.ipynb"
    _build_notebook(
        notebook_path,
        "term_paper/knowledge_rag/artifacts/metrics/phase14_metrics.json",
        "term_paper/knowledge_rag/artifacts/metrics/phase14_tuning.json",
        all_metrics,
        tuning,
    )
    report_path = base / "phase14_build_report.md"
    report_lines = [
        "# Phase 14 build report", "", f"- Locked config SHA-256: `{locked_hash}`.",
        f"- B2 selected sparse weight on validation: `{selected_weight}`.",
        "- TEST status: `SEALED_NOT_RUN`.",
        "- All models use the same per-domain corpus, validation queries, top-k and grounded answer contract.",
        "- Program accuracy is not applicable to the extractive B0-B2 answer layer; FinQA execution accuracy is reported as normalized numeric/string exact match.",
        "", "## Validation summary", "",
        "| Domain | Model | Chunk R@5 | MRR@10 | Token F1 | Abstain | p95 ms |", "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for domain in ("medical", "finance"):
        for model_id in ("B0", "B1", "B2"):
            row = all_metrics["validation"][domain][model_id]
            report_lines.append(
                f"| {domain} | {model_id} | {row['chunk_recall_at_5']:.3f} | {row['mrr_at_10']:.3f} | "
                f"{row['token_f1']:.3f} | {row['abstention_rate']:.3f} | {row['latency_ms_p95']:.2f} |"
            )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    generated: list[Path] = [
        config_path, locked_path, tuning_path, metrics_path, metrics_csv, notebook_path, report_path,
        figures_dir / "retrieval_recall_at_k.svg", figures_dir / "answer_quality.svg", figures_dir / "latency.svg",
    ]
    generated.extend(prediction_paths)
    for domain in ("medical", "finance"):
        cache_dir = base / f"data/processed/phase14/indexes/{domain}"
        generated.extend([cache_dir / "bm25.joblib", cache_dir / "dense_lsa.joblib", cache_dir / "cache_manifest.json"])
    manifest = {
        "schema_version": 1,
        "generated_at": config["generated_at"],
        "status": "PASS",
        "models": ["B0", "B1", "B2"],
        "domains": ["medical", "finance"],
        "evaluation_split": "validation",
        "test_split_status": "SEALED_NOT_RUN",
        "top_k": config["top_k"],
        "base_config_sha256": base_config_hash,
        "config_sha256": locked_hash,
        "selected_sparse_weight": selected_weight,
        "corpus_sha256": corpus_hashes,
        "artifacts": [_artifact_row(workspace, path) for path in sorted(generated)],
    }
    manifest_path = manifests_dir / "phase14_baseline_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "status": "PASS", "selected_sparse_weight": selected_weight, "cache_reused": cache_reused,
        "metrics": all_metrics["validation"], "manifest": manifest_path.relative_to(workspace).as_posix(),
    }


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    result = build_phase14(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
