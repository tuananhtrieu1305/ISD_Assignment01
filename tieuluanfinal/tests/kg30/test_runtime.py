"""Synthetic tests do not use benchmark queries or public TEST predictions."""

import copy

import pytest

from src.ch05_knowledge_rag.runtime import compare_rankings, graph_candidates, validate_layout


def test_graph_trace_contains_only_reachable_chunks():
    graph = {"diabetes": {"node_id": "entity1", "label": "Diabetes", "chunk_ids": ["c2"]}}
    candidates, paths = graph_candidates("diabetes complications", graph)
    assert candidates == {"c2"}
    assert paths == {"c2": ["entity1", "c2"]}
    assert graph_candidates("unknown", graph) == (set(), {})


def test_compare_uses_all_five_declared_rankers_and_frozen_weights():
    sparse, dense = [("c1", 1.0), ("c2", 0.5)], [("c2", 0.9), ("c1", 0.1)]
    output = compare_rankings(
        sparse, dense, {"c2"}, 0.75, {"sparse": 0.6, "dense": 0.1, "graph": 0.3}, 10, 60
    )
    assert list(output) == ["B0", "B1", "B2", "B3", "B4"]
    assert output["B0"] == sparse
    assert output["B1"] == dense
    assert [v[0] for v in output["B3"]] == ["c2"]
    assert output["B2"][0][0] == "c1"
    assert output["B4"][0][0] == "c2"
    assert all(
        not rank
        for rank in compare_rankings(
            [], [], set(), 0.75, {"sparse": 0.6, "dense": 0.1, "graph": 0.3}, 10, 60
        ).values()
    )


def test_manifest_paths_must_be_exact_verified_members():
    manifest = {
        "files": [{"path": name} for name in ("chunks.gz", "graph.gz", "ms", "md", "fs", "fd")],
        "chunks_file": "chunks.gz",
        "graph_file": "graph.gz",
        "indexes": {"medical": {"sparse": "ms", "dense": "md"}, "finance": {"sparse": "fs", "dense": "fd"}},
    }
    assert validate_layout(manifest) == {r["path"] for r in manifest["files"]}
    for invalid in ("../bad", "/tmp/bad", "unlisted", "graph.gz"):
        changed = copy.deepcopy(manifest)
        changed["chunks_file"] = invalid
        with pytest.raises(ValueError):
            validate_layout(changed)


def test_gzip_read_budget_and_lazy_single_load(tmp_path):
    import gzip

    from src.ch05_knowledge_rag.runtime import LazyBundle, _read_gzip

    path = tmp_path / "text.gz"
    path.write_bytes(gzip.compress(b"0123456789"))
    assert _read_gzip(path, 10) == "0123456789"
    with pytest.raises(ValueError, match="budget"):
        _read_gzip(path, 9)
    calls = []
    lazy = LazyBundle(lambda: calls.append(1) or "bundle")
    assert lazy.get() == lazy.get() == "bundle"
    assert len(calls) == 1


def test_modified_manifest_rejected_before_joblib(tmp_path, monkeypatch):
    from src.ch05_knowledge_rag import runtime

    path = tmp_path / runtime.RUNTIME
    path.parent.mkdir(parents=True)
    path.write_bytes(b"{}")
    monkeypatch.setattr(runtime.joblib, "load", lambda _: pytest.fail("Must not deserialize untrusted bytes"))
    with pytest.raises(ValueError, match="hash"):
        runtime.load_bundle(tmp_path)
