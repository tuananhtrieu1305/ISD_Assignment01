"""Domain-scoped, streaming loader over the same six immutable KG–RAG assets.

Changes allocation strategy only. Index weights, corpus text, ranking and answering
remain the frozen Phase30 implementation; no corpus rebuild or TEST execution.
"""

import gzip
import json

import joblib

from apps.api.knowledge_rag_service import RuntimeBundle, validate_question
from src.ch05_knowledge_rag.preservation import RUNTIME, RUNTIME_SHA
from src.ch05_knowledge_rag.runtime import compare_rankings, graph_candidates, validate_layout


def iter_jsonl_gzip(path, *, max_expanded_bytes=256 * 1024**2, max_line_bytes=1024**2):
    consumed = 0
    with gzip.open(path, "rb") as stream:
        while True:
            line = stream.readline(max_line_bytes + 1)
            if not line:
                break
            consumed += len(line)
            if len(line) > max_line_bytes or consumed > max_expanded_bytes:
                raise ValueError("Corpus streaming budget exceeded")
            yield json.loads(line)


def load_domain_bundle(registry, domain, question=None):
    if domain not in {"medical", "finance"}:
        raise ValueError("Unknown retrieval domain")
    question = validate_question(question)
    manifest = registry.json({"path": RUNTIME, "sha256": RUNTIME_SHA})
    validate_layout(manifest)
    paths = {}
    total = 0
    for record in manifest["files"]:
        path = registry.checked({"path": "apps/api/models/" + record["path"], "sha256": record["sha256"]})
        if path.stat().st_size != record["size_bytes"]:
            raise ValueError("Runtime size mismatch")
        total += record["size_bytes"]
        paths[record["path"]] = path
    if total != manifest["package_bytes"] or total > 192 * 1024**2:
        raise ValueError("Runtime package budget mismatch")
    # Rank with the immutable full indexes first. Only text allocation is bounded;
    # the searchable corpus/candidates/ranking algorithm are not narrowed.
    indexes = {domain: {kind: joblib.load(paths[name]) for kind, name in manifest["indexes"][domain].items()}}
    with gzip.open(paths[manifest["graph_file"]], "rb") as stream:
        payload = stream.read(64 * 1024**2 + 1)
    if len(payload) > 64 * 1024**2:
        raise ValueError("Graph decompressed budget exceeded")
    graph = json.loads(payload)
    config = manifest["retrieval"]
    name = "experiments/configs/ch5/phase14_locked.json"
    weight = registry.json(registry.files[name])["selected_sparse_weight"]
    sparse = indexes[domain]["sparse"].search(question, config["candidate_depth"])
    dense = indexes[domain]["dense"].search(question, config["candidate_depth"])
    candidates, _ = graph_candidates(question, graph[domain])
    rankings = compare_rankings(
        sparse, dense, candidates, weight, config["weights"], config["top_k"], config["rrf_k"]
    )
    requested = {key for rank in rankings.values() for key, _ in rank}
    if len(requested) > 50:
        raise ValueError("Retrieved text cache budget")
    chunks, counts, valid_ids = {"medical": {}, "finance": {}}, {"medical": 0, "finance": 0}, set()
    for row in iter_jsonl_gzip(paths[manifest["chunks_file"]]):
        category, key = row["domain"], row["chunk_id"]
        if category not in counts:
            raise ValueError("Unknown corpus domain")
        counts[category] += 1
        if category == domain:
            if key in valid_ids:
                raise ValueError("Duplicate chunk ID")
            valid_ids.add(key)
            if key in requested:
                chunks[domain][key] = row
    if counts != manifest["counts"]["chunks"]:
        raise ValueError("Corpus count mismatch")
    if set(chunks[domain]) != requested:
        raise ValueError("Retrieved text missing from corpus")
    if len(graph[domain]) != manifest["counts"]["graph_anchors"][domain] or any(
        not set(row["chunk_ids"]) <= valid_ids for row in graph[domain].values()
    ):
        raise ValueError("Graph/corpus mismatch")
    # Only the hard-pinned role filenames reached joblib; never request paths/pickles.
    if any(set(index.doc_ids) != valid_ids for index in indexes[domain].values()):
        raise ValueError("Index/corpus ID mismatch")
    return RuntimeBundle(manifest, chunks, indexes, graph)
