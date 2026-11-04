"""Trusted six-file CPU bundle, lexical graph anchors and frozen rank fusion."""

import gzip
import json
import threading
from pathlib import PurePosixPath

import joblib

from apps.api.knowledge_rag_service import RuntimeBundle
from src.ch05_knowledge_rag.preservation import ROOT, RUNTIME, RUNTIME_SHA, checked
from src.common.contracts import read_json
from term_paper.tools.phase13_graph import normalize_label
from term_paper.tools.phase14_rag import reciprocal_rank_fusion
from term_paper.tools.phase15_kgrag import graph_filter_ranking, weighted_rrf


def validate_layout(manifest):
    files = [row["path"] for row in manifest["files"]]
    roles = [manifest["chunks_file"], manifest["graph_file"]]
    if set(manifest["indexes"]) != {"medical", "finance"}:
        raise ValueError("Require exact two retrieval domains")
    for domain in ("medical", "finance"):
        if set(manifest["indexes"][domain]) != {"sparse", "dense"}:
            raise ValueError("Require sparse/dense index roles")
        roles.extend(manifest["indexes"][domain].values())
    if len(files) != 6 or len(set(files)) != 6 or len(set(roles)) != 6 or set(files) != set(roles):
        raise ValueError("Exact six verified artifacts and distinct role references required")
    if any(not name or len(PurePosixPath(name).parts) != 1 or ":" in name or "\\" in name for name in files):
        raise ValueError("Unsafe runtime filename")
    return set(files)


def graph_candidates(question, graph):
    normalized = normalize_label(question)
    terms = set(normalized.split())
    matched = [
        (key, row)
        for key, row in graph.items()
        if key and (key in normalized or (len(key.split()) > 1 and set(key.split()) <= terms))
    ]
    matched.sort(key=lambda pair: (-len(pair[0]), pair[0]))
    paths = {}
    for _, row in matched[:4]:
        for chunk_id in row["chunk_ids"]:
            paths.setdefault(chunk_id, [row["node_id"], chunk_id])
    return set(paths), paths


def compare_rankings(sparse, dense, candidates, sparse_weight, weights, top_k, rrf_k):
    graph = graph_filter_ranking(sparse, candidates, 100)
    return {
        "B0": sparse[:top_k],
        "B1": dense[:top_k],
        "B2": reciprocal_rank_fusion(sparse, dense, sparse_weight, top_k, rrf_k),
        "B3": graph[:top_k],
        "B4": weighted_rrf({"sparse": sparse, "dense": dense, "graph": graph}, weights, top_k, rrf_k),
    }


def _read_gzip(path, max_bytes):
    with gzip.open(path, "rb") as stream:
        payload = stream.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ValueError("Runtime decompressed budget exceeded")
    return payload.decode("utf-8")


def load_bundle(root=ROOT):
    manifest_path = checked({"path": RUNTIME, "sha256": RUNTIME_SHA}, root)
    manifest = read_json(manifest_path)
    validate_layout(manifest)
    total = 0
    for record in manifest["files"]:
        name = "apps/api/models/" + record["path"]
        path = checked({"path": name, "sha256": record["sha256"]}, root)
        if path.stat().st_size != record["size_bytes"]:
            raise ValueError("Runtime artifact size mismatch")
        total += path.stat().st_size
    if total != manifest["package_bytes"] or total > min(manifest["artifact_budget_bytes"], 192 * 1024**2):
        raise ValueError("Runtime package budget mismatch")
    folder = manifest_path.parent
    chunks = {"medical": {}, "finance": {}}
    for line in _read_gzip(folder / manifest["chunks_file"], 256 * 1024**2).splitlines():
        row = json.loads(line)
        domain, key = row["domain"], row["chunk_id"]
        if domain not in chunks or key in chunks[domain]:
            raise ValueError("Duplicate or unknown-domain chunk")
        chunks[domain][key] = row
    if {name: len(rows) for name, rows in chunks.items()} != manifest["counts"]["chunks"]:
        raise ValueError("Runtime chunk count mismatch")
    graph = json.loads(_read_gzip(folder / manifest["graph_file"], 64 * 1024**2))
    for domain, rows in chunks.items():
        if len(graph[domain]) != manifest["counts"]["graph_anchors"][domain]:
            raise ValueError("Runtime graph count mismatch")
        valid_ids = set(rows)
        if any(not set(row["chunk_ids"]) <= valid_ids for row in graph[domain].values()):
            raise ValueError("Dangling compact graph reference")
    # Only the hard-pinned manifest's four local joblib files reach deserialization.
    # Never accept uploaded pickles, user paths, or a replacement manifest.
    indexes = {
        domain: {kind: joblib.load(folder / name) for kind, name in roles.items()}
        for domain, roles in manifest["indexes"].items()
    }
    for domain, roles in indexes.items():
        if any(set(index.doc_ids) != set(chunks[domain]) for index in roles.values()):
            raise ValueError("Index/corpus ID mismatch")
    return RuntimeBundle(manifest, chunks, indexes, graph)


class LazyBundle:
    def __init__(self, loader=load_bundle):
        self.loader = loader
        self.value = None
        self.lock = threading.Lock()

    def get(self):
        with self.lock:
            if self.value is None:
                self.value = self.loader()
        return self.value
