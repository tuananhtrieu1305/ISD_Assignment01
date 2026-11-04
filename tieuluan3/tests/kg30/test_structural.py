"""Wikidata snapshots are local provenance objects, never an invented QA metric."""

import pytest

from src.ch05_knowledge_rag.structural import inspect_entity


def test_entity_snapshot_has_exact_revision_and_source_hash():
    item = inspect_entity("Q12206")
    assert item["revision_id"] == 2554502707
    assert item["claim_count"] == 186
    assert (
        item["citation"]["source_sha256"]
        == "d78017cab4a383f45194004bdcbeaf0aa371b592bfe28119ba26ba3634dd41c1"
    )
    assert item["qa_benchmark"] is False
    assert item["training_executed"] is False


@pytest.mark.parametrize("qid", ["../Q12206", "Q1", "Q12206.json", "https://example.com", None])
def test_structural_view_rejects_unlisted_paths_ids_and_urls(qid):
    with pytest.raises(ValueError):
        inspect_entity(qid)
