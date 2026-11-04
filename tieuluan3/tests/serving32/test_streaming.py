"""Streaming must preserve the exact old compact-demo semantic outputs."""

import gzip

import pytest

from apps.api.v3.rag_streaming import iter_jsonl_gzip, load_domain_bundle
from apps.api.v3.registry import Registry
from src.ch05_knowledge_rag.service import KgRagService, sample_request


def test_stream_budget(tmp_path):
    path = tmp_path / "sample.gz"
    with gzip.open(path, "wb") as stream:
        stream.write(b'{"x":1}\n{"x":2}\n')
    assert list(iter_jsonl_gzip(path)) == [{"x": 1}, {"x": 2}]
    with pytest.raises(ValueError):
        list(iter_jsonl_gzip(path, max_expanded_bytes=3))
    with pytest.raises(ValueError):
        list(iter_jsonl_gzip(path, max_line_bytes=4))


@pytest.mark.parametrize("dataset,domain", [("ch5_medquad_diabetes", "medical"), ("ch5_finqa", "finance")])
def test_compact_demo_exact_parity(dataset, domain):
    registry = Registry()
    request = sample_request(dataset)
    original = KgRagService().compare(request)
    streamed = KgRagService(
        loader=lambda: load_domain_bundle(registry, domain, request["input"]["text"])
    ).compare(request)
    assert streamed["evidence"] == original["evidence"]
    assert streamed["graph_paths"] == original["graph_paths"]
    assert [r["prediction"] for r in streamed["job"]["results"]] == [
        r["prediction"] for r in original["job"]["results"]
    ]
    assert streamed["job"]["comparison_valid"] is True


def test_unknown_domain():
    with pytest.raises(ValueError):
        load_domain_bundle(Registry(), "untrusted")


def test_only_retrieved_texts_are_cached():
    bundle = load_domain_bundle(Registry(), "finance", "what is the the interest expense in 2009?")
    assert len(bundle.chunks["finance"]) <= 50
    assert len(bundle.indexes["finance"]["dense"].doc_ids) == 86421
