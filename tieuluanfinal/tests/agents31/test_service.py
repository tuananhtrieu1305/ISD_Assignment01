"""Local V3 agent-task adapter; not an HTTP endpoint or LLM interpreter."""

import pytest

from src.ch06_multi_agent.core import VARIANTS
from src.ch06_multi_agent.service import AgentService, decode_question, pipeline_contract, sample_request
from tests.agents31.test_core import FakeTools


@pytest.mark.parametrize("domain", ["diabetes", "house", "gold"])
def test_public_contract_compare(domain):
    request = sample_request(domain)
    result = AgentService(FakeTools(), "a" * 64).compare(request)
    assert set(result["outputs"]) == set(VARIANTS)
    assert all(r["trace"]["status"] == "succeeded" for r in result["outputs"].values())
    assert result["scope"] == "local_task_demo_not_http"


def test_free_text_without_record_is_unsupported_not_guessed():
    task = decode_question("diabetes", "Tiểu đường là gì?")
    assert task["operation"] == "unsupported"


@pytest.mark.parametrize(
    "question", ["tiểu đường record=../secret", "giá vàng record=gold_numeric_000 record=gold_numeric_001"]
)
def test_decoder_rejects_injection_or_multiple_records(question):
    with pytest.raises(ValueError):
        decode_question("gold", question)


def test_domain_and_unknown_dataset():
    with pytest.raises(ValueError):
        decode_question("gold", "giá vàng record=house_numeric_000")
    with pytest.raises(ValueError):
        AgentService(FakeTools(), "a" * 64).compare({**sample_request("gold"), "dataset_id": "unknown"})


@pytest.mark.parametrize("variant", VARIANTS)
def test_pipeline_composition_explains_actual_functions(variant):
    contract = pipeline_contract("diabetes", variant)
    assert contract["learnable_layers"] is None
    assert set(contract["composition"]) == {r["id"] for r in contract["functions"]}
    assert all(r["corner_case"] and r["role"] for r in contract["functions"])
