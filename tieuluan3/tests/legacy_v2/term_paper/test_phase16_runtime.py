"""Tests for the compact, deployable Phase 16 KG-RAG package."""

from __future__ import annotations

from term_paper.tools.build_phase16_runtime import compact_graph_map
from term_paper.tools.verify_phase16 import verify_runtime_manifest


def test_medical_compact_graph_maps_entity_to_document_chunks():
    nodes = [
        {"node_id": "entity", "node_type": "MedicalEntity", "label": "Diabetes", "source_id": None},
        {"node_id": "doc", "node_type": "Document", "label": "Document", "source_id": "doc-1"},
        {"node_id": "chunk", "node_type": "Chunk", "label": "Chunk", "source_id": "med-1"},
    ]
    edges = [
        {"edge_type": "DESCRIBES", "source_id": "doc", "target_id": "entity"},
        {"edge_type": "HAS_CHUNK", "source_id": "doc", "target_id": "chunk"},
    ]
    result = compact_graph_map("medical", nodes, edges)
    assert result["diabetes"]["chunk_ids"] == ["med-1"]
    assert result["diabetes"]["node_id"] == "entity"


def test_finance_compact_graph_maps_concept_to_mentioning_chunks():
    nodes = [
        {"node_id": "concept", "node_type": "FinancialConcept", "label": "Operating revenue", "source_id": None},
        {"node_id": "chunk", "node_type": "Chunk", "label": "Chunk", "source_id": "fin-1"},
    ]
    edges = [{"edge_type": "MENTIONS", "source_id": "chunk", "target_id": "concept"}]
    result = compact_graph_map("finance", nodes, edges)
    assert result["operating revenue"]["chunk_ids"] == ["fin-1"]


def test_compact_graph_deduplicates_and_sorts_chunk_ids():
    nodes = [
        {"node_id": "concept", "node_type": "FinancialConcept", "label": "Revenue", "source_id": None},
        {"node_id": "a", "node_type": "Chunk", "label": "A", "source_id": "fin-2"},
        {"node_id": "b", "node_type": "Chunk", "label": "B", "source_id": "fin-1"},
    ]
    edges = [
        {"edge_type": "MENTIONS", "source_id": "a", "target_id": "concept"},
        {"edge_type": "MENTIONS", "source_id": "b", "target_id": "concept"},
        {"edge_type": "MENTIONS", "source_id": "b", "target_id": "concept"},
    ]
    result = compact_graph_map("finance", nodes, edges)
    assert result["revenue"]["chunk_ids"] == ["fin-1", "fin-2"]


def test_runtime_manifest_verifier_rejects_unapproved_tool():
    manifest = {
        "allowed_tools": ["medical_retriever", "shell"],
        "artifact_budget_bytes": 100,
        "package_bytes": 50,
        "private_test_included": False,
        "external_api_required": False,
        "files": [{"path": "kg.bin", "size_bytes": 50, "sha256": "a" * 64}],
    }
    failures = verify_runtime_manifest(manifest)
    assert any("allow-list" in failure for failure in failures)


def test_runtime_manifest_verifier_accepts_safe_package_contract():
    manifest = {
        "allowed_tools": ["finance_retriever", "medical_retriever"],
        "artifact_budget_bytes": 100,
        "package_bytes": 50,
        "private_test_included": False,
        "external_api_required": False,
        "files": [{"path": "kg.bin", "size_bytes": 50, "sha256": "a" * 64}],
    }
    assert verify_runtime_manifest(manifest) == []
