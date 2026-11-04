"""Dataset tabs and non-neural contracts keep the Phase22 neural schemas unchanged."""

import copy

import pytest

from src.ch05_knowledge_rag.catalog import catalog, pipeline_contract, validate_pipeline
from src.ch05_knowledge_rag.service import DATASETS
from src.common.contracts import validate_document


def test_three_dataset_tab_descriptors_and_no_wikidata_qa_metric():
    result = catalog()
    validate_document("api#chapter", result["chapter"])
    assert [row["dataset_id"] for row in result["tabs"]] == list(DATASETS)
    assert result["tabs"][2]["mode"] == "structural_browser"
    assert result["tabs"][2]["historical_metrics"] == []
    assert all(row["data_card"] and row["eda"] and row["source_manifest"] for row in result["tabs"])


@pytest.mark.parametrize("dataset", DATASETS)
@pytest.mark.parametrize("method", ["B0", "B1", "B2", "B3", "B4"])
def test_non_neural_contract_does_not_fabricate_layers(dataset, method):
    contract = pipeline_contract(dataset, method)
    validate_pipeline(contract)
    assert contract["parameter_count"] is None
    assert contract["learnable_layers"] is None
    assert contract["lifecycle"] != "trained_v3"
    assert bool(contract["available"]) == (dataset != DATASETS[2])
    assert contract["functions"] and contract["composition"]


def test_bad_pipeline_model_dataset_or_composition_is_rejected():
    for field, value in (
        ("method", "B9"),
        ("dataset_id", "ch2_cdc_diabetes"),
        ("learnable_layers", 6),
        ("composition", ["missing"]),
    ):
        contract = copy.deepcopy(pipeline_contract(DATASETS[0], "B4"))
        contract[field] = value
        with pytest.raises(ValueError):
            validate_pipeline(contract)
