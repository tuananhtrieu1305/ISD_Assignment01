"""Synthetic six-file packages exercise budgets/corruption before any real joblib load."""

import gzip
import hashlib
import json
from types import SimpleNamespace

import pytest

from src.ch05_knowledge_rag import runtime


def package(tmp_path, monkeypatch, issue=None):
    folder = tmp_path / "apps/api/models"
    folder.mkdir(parents=True)
    rows = [
        {"domain": "medical", "chunk_id": "m", "document_id": "mdoc", "text": "synthetic medical"},
        {"domain": "finance", "chunk_id": "f", "document_id": "fdoc", "text": "synthetic finance"},
    ]
    if issue == "duplicate":
        rows.append(rows[0])
    if issue == "domain":
        rows[0]["domain"] = "shell"
    graph = {
        d: {"anchor": {"node_id": "anchor", "chunk_ids": [key]}}
        for d, key in (("medical", "m"), ("finance", "f"))
    }
    if issue == "dangling":
        graph["medical"]["anchor"]["chunk_ids"] = ["missing"]
    payloads = {
        "chunks.gz": gzip.compress("\n".join(json.dumps(r) for r in rows).encode()),
        "graph.gz": gzip.compress(json.dumps(graph).encode()),
        "ms": b"fixture",
        "md": b"fixture",
        "fs": b"fixture",
        "fd": b"fixture",
    }
    files = []
    for name, value in payloads.items():
        (folder / name).write_bytes(value)
        files.append({"path": name, "sha256": hashlib.sha256(value).hexdigest(), "size_bytes": len(value)})
    total = sum(r["size_bytes"] for r in files)
    manifest = {
        "files": files,
        "chunks_file": "chunks.gz",
        "graph_file": "graph.gz",
        "indexes": {"medical": {"sparse": "ms", "dense": "md"}, "finance": {"sparse": "fs", "dense": "fd"}},
        "package_bytes": total,
        "artifact_budget_bytes": total,
        "counts": {"chunks": {"medical": 1, "finance": 1}, "graph_anchors": {"medical": 1, "finance": 1}},
    }
    if issue == "size":
        files[0]["size_bytes"] += 1
    if issue == "budget":
        manifest["artifact_budget_bytes"] -= 1
    if issue == "chunks":
        manifest["counts"]["chunks"]["medical"] = 2
    if issue == "graph":
        manifest["counts"]["graph_anchors"]["medical"] = 2
    encoded = json.dumps(manifest).encode()
    (tmp_path / runtime.RUNTIME).write_bytes(encoded)
    monkeypatch.setattr(runtime, "RUNTIME_SHA", hashlib.sha256(encoded).hexdigest())
    monkeypatch.setattr(
        runtime.joblib,
        "load",
        lambda path: SimpleNamespace(
            doc_ids=[] if issue == "index" else (["m"] if path.name.startswith("m") else ["f"])
        ),
    )


def test_synthetic_verified_bundle_loads_without_deserializing_user_bytes(tmp_path, monkeypatch):
    package(tmp_path, monkeypatch)
    result = runtime.load_bundle(tmp_path)
    assert set(result.chunks["medical"]) == {"m"}


@pytest.mark.parametrize(
    "issue", ["size", "budget", "duplicate", "domain", "chunks", "graph", "dangling", "index"]
)
def test_bad_runtime_package_fails_closed(tmp_path, monkeypatch, issue):
    package(tmp_path, monkeypatch, issue)
    with pytest.raises(ValueError):
        runtime.load_bundle(tmp_path)


@pytest.mark.parametrize(
    "indexes", [{}, {"medical": {}, "finance": {}}, {"medical": {"sparse": "m"}, "finance": {"sparse": "f"}}]
)
def test_missing_runtime_roles_are_rejected(indexes):
    with pytest.raises(ValueError):
        runtime.validate_layout(
            {"files": [], "chunks_file": "chunks.gz", "graph_file": "graph.gz", "indexes": indexes}
        )
