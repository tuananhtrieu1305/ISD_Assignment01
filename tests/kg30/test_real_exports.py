"""Acceptance checks on produced local artifacts; never evaluate the sealed TEST."""

from src.ch05_knowledge_rag.preservation import BASE, checked
from src.common.contracts import read_json, validate_document


def test_three_real_notebook_exports_and_ten_qa_slots():
    export = read_json(BASE / "export.json")
    assert export["status"] == "PASS"
    assert export["notebooks_executed"] == 3
    assert export["qa_slots_executed"] == 10
    assert export["wikidata_entities_inspected"] == 10
    assert export["new_test_evaluation_executed"] is False
    for record in export["artifacts"]:
        checked(record)


def test_real_catalog_fifteen_contracts_and_non_benchmark_wikidata():
    registry = read_json(BASE / "reused_registry.json")
    assert registry["initialized_registry_replaced"] is False
    assert len(registry["models"]) == 15
    assert sum(row["available"] for row in registry["models"]) == 10
    for row in registry["models"]:
        checked(row["contract"])
        assert not row["new_training_executed"]
    for dataset in ("ch5_medquad_diabetes", "ch5_finqa"):
        output = read_json(BASE / "demos" / f"{dataset}.json")
        validate_document("api#job", output["job"])
        assert output["job"]["comparison_valid"]
        assert all(row["prediction"] is not None for row in output["job"]["results"])
        assert any(not row["prediction"]["abstained"] for row in output["job"]["results"])


def test_active_manuscript_is_qa_corrected_r2_and_legacy_r1_remains():
    active = read_json(BASE / "active_report.json")
    assert active["revision"] == "presentation_r2"
    generation = read_json(checked(active["generation"]))
    assert active["manuscript"] == generation["manuscript"]
    checked(generation["manuscript"])
    checked(generation["supersedes"])
