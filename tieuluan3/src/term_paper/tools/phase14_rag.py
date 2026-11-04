"""CPU-only retrieval, grounded answering, and evaluation for Phase 14."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.preprocessing import normalize

from term_paper.tools.phase12_preprocessing import normalize_answer, token_f1


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "did", "do", "does", "for", "from", "how",
    "in", "is", "it", "of", "on", "or", "that", "the", "their", "this", "to", "was", "were", "what",
    "when", "where", "which", "who", "why", "with", "would",
}


def tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", str(text).casefold()) if token not in STOPWORDS]


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _stable_ranking(doc_ids: Sequence[str], scores: np.ndarray, top_k: int, positive_only: bool = False) -> list[tuple[str, float]]:
    if top_k <= 0 or len(doc_ids) == 0:
        return []
    values = np.asarray(scores, dtype=np.float64).reshape(-1)
    candidates = np.flatnonzero(values > 0) if positive_only else np.arange(len(values))
    if candidates.size == 0:
        return []
    ids = np.asarray(doc_ids, dtype=str)
    order = candidates[np.lexsort((ids[candidates], -values[candidates]))]
    return [(str(ids[index]), float(values[index])) for index in order[:top_k]]


@dataclass
class BM25Index:
    doc_ids: list[str]
    vectorizer: CountVectorizer
    counts_csc: sparse.csc_matrix
    doc_lengths: np.ndarray
    idf: np.ndarray
    average_doc_length: float
    k1: float = 1.5
    b: float = 0.75

    @classmethod
    def fit(cls, doc_ids: Sequence[str], texts: Sequence[str], k1: float = 1.5, b: float = 0.75) -> "BM25Index":
        if len(doc_ids) != len(texts) or not doc_ids:
            raise ValueError("doc_ids and texts must be non-empty and aligned")
        vectorizer = CountVectorizer(analyzer=tokenize, lowercase=False, dtype=np.int32)
        counts = vectorizer.fit_transform(texts).astype(np.float32).tocsr()
        lengths = np.asarray(counts.sum(axis=1)).reshape(-1).astype(np.float32)
        document_frequency = np.asarray((counts > 0).sum(axis=0)).reshape(-1)
        total = counts.shape[0]
        idf = np.log1p((total - document_frequency + 0.5) / (document_frequency + 0.5)).astype(np.float32)
        return cls(list(doc_ids), vectorizer, counts.tocsc(), lengths, idf, float(lengths.mean()), float(k1), float(b))

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        query_vector = self.vectorizer.transform([query])
        terms = query_vector.indices
        if terms.size == 0:
            return []
        scores = np.zeros(len(self.doc_ids), dtype=np.float32)
        norm = self.k1 * (1.0 - self.b + self.b * self.doc_lengths / max(self.average_doc_length, 1e-8))
        for term in terms:
            start, end = self.counts_csc.indptr[term], self.counts_csc.indptr[term + 1]
            rows = self.counts_csc.indices[start:end]
            frequencies = self.counts_csc.data[start:end]
            scores[rows] += self.idf[term] * (frequencies * (self.k1 + 1.0)) / (frequencies + norm[rows])
        return _stable_ranking(self.doc_ids, scores, top_k, positive_only=True)


@dataclass
class DenseLSAIndex:
    doc_ids: list[str]
    vectorizer: CountVectorizer
    tfidf: TfidfTransformer
    svd: TruncatedSVD
    vectors: np.ndarray

    @classmethod
    def fit(
        cls,
        doc_ids: Sequence[str],
        texts: Sequence[str],
        n_components: int = 128,
        seed: int = 42,
        max_features: int | None = 12_000,
        min_df: int = 2,
    ) -> "DenseLSAIndex":
        if len(doc_ids) != len(texts) or len(doc_ids) < 2:
            raise ValueError("Dense LSA needs at least two aligned documents")
        vectorizer = CountVectorizer(
            analyzer=tokenize, lowercase=False, dtype=np.int32, max_features=max_features, min_df=min_df
        )
        counts = vectorizer.fit_transform(texts)
        tfidf = TfidfTransformer(sublinear_tf=True)
        matrix = tfidf.fit_transform(counts)
        dimensions = max(1, min(int(n_components), matrix.shape[0] - 1, matrix.shape[1] - 1))
        svd = TruncatedSVD(n_components=dimensions, algorithm="randomized", n_iter=5, random_state=seed)
        vectors = normalize(svd.fit_transform(matrix).astype(np.float32), norm="l2", copy=False)
        return cls(list(doc_ids), vectorizer, tfidf, svd, np.asarray(vectors, dtype=np.float32))

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        return self.search_batch([query], top_k=top_k, batch_size=1)[0]

    def search_batch(self, queries: Sequence[str], top_k: int = 10, batch_size: int = 32) -> list[list[tuple[str, float]]]:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        results: list[list[tuple[str, float]]] = []
        for start in range(0, len(queries), batch_size):
            batch = list(queries[start : start + batch_size])
            counts = self.vectorizer.transform(batch)
            vectors = self.svd.transform(self.tfidf.transform(counts)).astype(np.float32)
            vectors = normalize(vectors, norm="l2", copy=False)
            score_matrix = vectors @ self.vectors.T
            for offset, query in enumerate(batch):
                if not tokenize(query) or counts[offset].nnz == 0:
                    results.append([])
                else:
                    results.append(_stable_ranking(self.doc_ids, score_matrix[offset], top_k, positive_only=False))
        return results


def reciprocal_rank_fusion(
    sparse_ranking: Sequence[tuple[str, float]],
    dense_ranking: Sequence[tuple[str, float]],
    sparse_weight: float,
    top_k: int,
    rrf_k: int = 60,
) -> list[tuple[str, float]]:
    if not 0.0 <= sparse_weight <= 1.0:
        raise ValueError("sparse_weight must be in [0, 1]")
    scores: dict[str, float] = {}
    for rank, (doc_id, _) in enumerate(sparse_ranking, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + sparse_weight / (rrf_k + rank)
    dense_weight = 1.0 - sparse_weight
    for rank, (doc_id, _) in enumerate(dense_ranking, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + dense_weight / (rrf_k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:top_k]


def grounded_answer(
    query: str,
    ranking: Sequence[tuple[str, float]],
    chunk_lookup: Mapping[str, str],
    minimum_overlap_terms: int,
    minimum_overlap_ratio: float,
    unsafe_patterns: Sequence[str],
    maximum_characters: int = 420,
) -> dict[str, Any]:
    normalized_query = " ".join(tokenize(query))
    if any(" ".join(tokenize(pattern)) in normalized_query for pattern in unsafe_patterns if tokenize(pattern)):
        return {"answer": "", "citations": [], "abstained": True, "reason": "guardrail"}
    query_terms = set(tokenize(query))
    for chunk_id, score in ranking:
        text = chunk_lookup.get(chunk_id)
        if not text:
            continue
        overlap = query_terms & set(tokenize(text))
        ratio = len(overlap) / max(len(query_terms), 1)
        if len(overlap) < minimum_overlap_terms or ratio < minimum_overlap_ratio:
            continue
        excerpt = " ".join(text.split())
        if len(excerpt) > maximum_characters:
            excerpt = excerpt[:maximum_characters].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
        return {
            "answer": excerpt,
            "citations": [chunk_id],
            "abstained": False,
            "reason": "grounded_extract",
            "support_score": float(score),
            "overlap_terms": sorted(overlap),
        }
    return {"answer": "", "citations": [], "abstained": True, "reason": "insufficient_evidence"}


def _reciprocal_rank(ranked: Sequence[str], gold: set[str], cutoff: int = 10) -> float:
    for rank, item in enumerate(ranked[:cutoff], start=1):
        if item in gold:
            return 1.0 / rank
    return 0.0


def prediction_metrics(rows: Sequence[Mapping[str, Any]], top_ks: Sequence[int]) -> dict[str, Any]:
    if not rows:
        raise ValueError("Prediction rows are required")
    result: dict[str, Any] = {"query_count": len(rows)}
    for k in top_ks:
        result[f"chunk_recall_at_{k}"] = round(
            float(np.mean([bool(set(row.get("ranked_chunk_ids", [])[:k]) & set(row.get("gold_chunk_ids", []))) for row in rows])), 6
        )
        result[f"document_recall_at_{k}"] = round(
            float(np.mean([bool(set(row.get("ranked_document_ids", [])[:k]) & set(row.get("gold_document_ids", []))) for row in rows])), 6
        )
    result["mrr_at_10"] = round(
        float(np.mean([_reciprocal_rank(row.get("ranked_chunk_ids", []), set(row.get("gold_chunk_ids", []))) for row in rows])), 6
    )
    exact = [normalize_answer(row.get("answer", "")) == normalize_answer(row.get("gold_answer", "")) for row in rows]
    result["normalized_exact_match"] = round(float(np.mean(exact)), 6)
    result["token_f1"] = round(float(np.mean([token_f1(row.get("answer", ""), row.get("gold_answer", "")) for row in rows])), 6)
    citations = [citation for row in rows for citation in row.get("citations", [])]
    valid = [citation in set(row.get("retrieved_chunk_ids", [])) for row in rows for citation in row.get("citations", [])]
    supported = [citation in set(row.get("gold_chunk_ids", [])) for row in rows for citation in row.get("citations", [])]
    result["citation_validity"] = round(float(np.mean(valid)), 6) if valid else 1.0
    result["citation_gold_precision"] = round(float(np.mean(supported)), 6) if citations else 0.0
    result["abstention_rate"] = round(float(np.mean([bool(row.get("abstained")) for row in rows])), 6)
    latencies = np.asarray([float(row.get("latency_ms", 0.0)) for row in rows], dtype=np.float64)
    result["latency_ms_p50"] = round(float(np.percentile(latencies, 50)), 6)
    result["latency_ms_p95"] = round(float(np.percentile(latencies, 95)), 6)
    return result


def build_cache_manifest(
    model_id: str,
    corpus_sha256: str,
    config_sha256: str,
    chunk_count: int,
    artifact_files: Mapping[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "model_id": model_id,
        "corpus_sha256": corpus_sha256,
        "config_sha256": config_sha256,
        "chunk_count": int(chunk_count),
        "artifact_files": dict(sorted(artifact_files.items())),
    }


def validate_cache_manifest(manifest: Mapping[str, Any], expected_corpus_hash: str, expected_config_hash: str) -> None:
    if manifest.get("corpus_sha256") != expected_corpus_hash:
        raise ValueError("Cache invalid: corpus hash changed")
    if manifest.get("config_sha256") != expected_config_hash:
        raise ValueError("Cache invalid: config hash changed")
    if int(manifest.get("chunk_count", 0)) <= 0 or not manifest.get("artifact_files"):
        raise ValueError("Cache invalid: incomplete artifact inventory")
