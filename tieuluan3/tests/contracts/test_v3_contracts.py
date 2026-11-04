"""Contract tests precede implementation; examples are explicitly synthetic, not results."""

import json
from pathlib import Path

import pytest

from src.common.contracts import (
    ContractError,
    audit_specification,
    canonical_sha256,
    check_seal_transition,
    load_schemas,
    validate_document,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "docs/contracts/v3/examples"


def example(name):
    return json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))


def test_all_schemas_are_valid_offline():
    assert len(load_schemas()) >= 8


@pytest.mark.parametrize("name", ["dataset", "split", "model", "run", "artifact", "seal", "agent", "api"])
def test_examples_are_structurally_and_semantically_valid(name):
    validate_document(name, example(name))


def test_unknown_schema_is_rejected():
    with pytest.raises(ContractError, match="Unknown schema"):
        validate_document("nonexistent", {})


def test_extra_fields_are_rejected():
    value = example("dataset")
    value["silent_change"] = True
    with pytest.raises(ContractError):
        validate_document("dataset", value)


def test_schema_version_is_not_optional():
    value = example("dataset")
    del value["schema_version"]
    with pytest.raises(ContractError):
        validate_document("dataset", value)


def test_fixture_must_not_be_published_as_real_result():
    with pytest.raises(ContractError, match="synthetic"):
        validate_document("run", example("run"), publish=True)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_numbers_are_rejected(value):
    document = example("run")
    document["metrics"][0]["value"] = value
    with pytest.raises(ContractError, match="finite"):
        validate_document("run", document)


def test_bad_sha256_is_rejected():
    value = example("artifact")
    value["sha256"] = "not-a-hash"
    with pytest.raises(ContractError):
        validate_document("artifact", value)


@pytest.mark.parametrize("path", ["../secret", "/etc/passwd", "C:\\secret", "artifacts/../secret"])
def test_artifact_path_cannot_escape_repository(path):
    value = example("artifact")
    value["path"] = path
    with pytest.raises(ContractError):
        validate_document("artifact", value)


def test_five_layers_fail_depth_requirement():
    value = example("model")
    value["layers"] = value["layers"][:5]
    with pytest.raises(ContractError):
        validate_document("model", value)


def test_pooling_cannot_be_counted_as_learnable_layer():
    value = example("model")
    for layer in value["layers"]:
        layer["kind"] = "pooling"
    with pytest.raises(ContractError, match="layer"):
        validate_document("model", value)


def test_parameter_count_must_match_layers():
    value = example("model")
    value["parameter_count"] += 1
    with pytest.raises(ContractError, match="parameter"):
        validate_document("model", value)


def test_composition_must_reference_existing_functions():
    value = example("model")
    value["composition"][0] = "missing_function"
    with pytest.raises(ContractError, match="function"):
        validate_document("model", value)


def test_scratch_cannot_claim_framework_backend():
    value = example("model")
    value["implementation"] = "scratch"
    value["backend"] = "tensorflow"
    with pytest.raises(ContractError, match="backend"):
        validate_document("model", value)


def test_temporal_split_cannot_overlap_target_times():
    value = example("split")
    value["partitions"][1]["target_start"] = value["partitions"][0]["target_end"]
    with pytest.raises(ContractError, match="time"):
        validate_document("split", value)


def test_duplicate_split_partitions_are_rejected():
    value = example("split")
    value["partitions"][1]["name"] = "train"
    with pytest.raises(ContractError, match="partition"):
        validate_document("split", value)


def test_dataset_chapter_mapping_is_locked():
    value = example("api")
    value["chapter"] = 3
    with pytest.raises(ContractError, match="dataset"):
        validate_document("api", value)


def test_compare_request_cannot_omit_an_implementation():
    value = example("api")
    value["implementations"] = ["keras"]
    with pytest.raises(ContractError):
        validate_document("api", value)


def test_one_shot_seal_transition_requires_locked_config():
    seal = example("seal")
    check_seal_transition(seal, "evaluating", config_sha256=seal["locked_config_sha256"])
    with pytest.raises(ContractError, match="config"):
        check_seal_transition(seal, "evaluating", config_sha256="f" * 64)


def test_evaluated_test_cannot_be_reopened():
    seal = example("seal")
    seal.update(state="evaluated", evaluation_count=1)
    with pytest.raises(ContractError, match="sealed"):
        check_seal_transition(seal, "evaluated", config_sha256=seal["locked_config_sha256"])


def test_hash_is_order_independent_but_content_sensitive():
    assert canonical_sha256({"a": 1, "b": 2}) == canonical_sha256({"b": 2, "a": 1})
    assert canonical_sha256({"a": 1}) != canonical_sha256({"a": 2})


def test_full_phase22_specification_audit():
    result = audit_specification(ROOT)
    assert result["errors"] == []
    assert result["requirements"] >= 40
    assert result["datasets"] == 18


def test_audit_rejects_missing_files(tmp_path):
    assert audit_specification(tmp_path)["errors"]


@pytest.mark.parametrize("field,value", [("cpu_loadable", False), ("load_policy", "data_only")])
def test_checkpoint_requires_safe_cpu_loader(field, value):
    document = example("artifact")
    document[field] = value
    with pytest.raises(ContractError):
        validate_document("artifact", document)


def test_job_example_is_valid():
    validate_document("api#job", example("api_job"))


def test_job_cannot_claim_success_without_prediction():
    document = example("api_job")
    document["results"][0]["prediction"] = None
    with pytest.raises(ContractError):
        validate_document("api#job", document)


def test_job_cannot_omit_failed_implementation():
    document = example("api_job")
    document["results"].pop()
    with pytest.raises(ContractError):
        validate_document("api#job", document)


def test_agent_failure_may_have_a_partial_trace():
    document = example("agent")
    document.update(variant="A2", status="timeout")
    document["nodes"][0].update(agent="router", outcome="timeout")
    validate_document("agent", document)


def test_agent_cannot_disguise_verifier_as_a0_baseline():
    document = example("agent")
    extra = dict(document["nodes"][0], node_id="node_2", agent="verifier", parent_ids=["node_1"])
    document["nodes"].append(extra)
    with pytest.raises(ContractError):
        validate_document("agent", document)


def test_agent_task_must_use_a_chapter6_task_view():
    document = {
        "schema_version": "3.0.0",
        "dataset_id": "ch2_cdc_diabetes",
        "question": "fixture",
        "variants": ["A0", "A1", "A2"],
    }
    with pytest.raises(ContractError):
        validate_document("api#agent_task", document)


def test_model_dataset_family_must_match():
    document = example("model")
    document["dataset_id"] = "ch3_cifar10"
    with pytest.raises(ContractError):
        validate_document("model", document)


@pytest.mark.parametrize(
    "name,path,value",
    [
        ("dataset", ["source", "license_status"], "pending"),
        ("dataset", ["logical_size", "records"], None),
        ("dataset", ["files"], []),
        ("run", ["subset_sha256"], None),
        ("run", ["split"], "test"),
        ("run", ["finished_at"], "2025-01-01T00:00:00Z"),
        ("run", ["efficiency", "inference_p95_ms"], 0),
        ("run", ["efficiency", "peak_vram_bytes"], 1),
        ("run", ["metrics", 0, "value"], None),
        ("run", ["metrics", 0, "undefined_reason"], "not actually undefined"),
        ("seal", ["evaluation_count"], 1),
        ("seal", ["approved_run_ids"], ["fixture_run", "fixture_run"]),
        ("api", ["family"], "cnn"),
        ("api", ["implementations"], ["A0", "A1", "A2"]),
        ("api#job", ["results", 0, "implementation"], "keras"),
        ("api#job", ["comparison_blockers"], ["input differs"]),
        ("api#job", ["results", 0, "status"], "failed"),
        ("api#job", ["results", 0, "prediction", "probabilities", 0, "value"], 0.9),
        ("agent", ["nodes", 0, "parent_ids"], ["node_1"]),
    ],
)
def test_semantic_negative_cases(name, path, value):
    document = example(name.replace("#", "_"))
    cursor = document
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    with pytest.raises(ContractError):
        validate_document(name, document)


def test_formula_cannot_omit_plain_language_and_symbols():
    document = example("model")
    document["functions"][0]["formula"] = {"expression": "y = Wx + b"}
    with pytest.raises(ContractError):
        validate_document("model", document)


def test_nonempty_formula_with_explanation_is_valid():
    document = example("model")
    document["functions"][0]["formula"] = {
        "expression": "y = Wx + b",
        "symbols": [
            {"symbol": "x", "meaning": "input vector"},
            {"symbol": "W", "meaning": "learned weights"},
            {"symbol": "b", "meaning": "bias"},
            {"symbol": "y", "meaning": "output vector"},
        ],
        "why_needed": "Read the scratch forward function",
        "plain_explanation": "Multiply inputs by weights, then add a bias",
        "example": "batch x 4 -> batch x 2",
    }
    validate_document("model", document)


def test_undefined_metric_can_be_null_with_reason():
    document = example("run")
    document["metrics"][0].update(value=None, undefined_reason="single-class fixture")
    validate_document("run", document)


def test_timestamp_order_uses_instants_not_string_order():
    document = example("run")
    document.update(started_at="2026-10-17T08:00:00+07:00", finished_at="2026-10-17T01:00:01Z")
    validate_document("run", document)


def test_valid_measured_document_may_pass_publication_gate():
    document = example("run")
    document["evidence_kind"] = "measured"
    # Contract validation is not a replacement for Phase25 file/provenance checks.
    validate_document("run", document, publish=True)


def test_recurrent_contract_must_explain_time_and_layers():
    document = example("model")
    document.update(family="rnn", dataset_id="ch4_gold_pink_sheet")
    for layer in document["layers"][:3]:
        layer["kind"] = "rnn"
    with pytest.raises(ContractError, match="unroll"):
        validate_document("model", document)


def test_task_view_requires_parents():
    document = example("dataset")
    document["kind"] = "task_view"
    with pytest.raises(ContractError):
        validate_document("dataset", document)


def test_valid_chapter6_request():
    document = {
        "schema_version": "3.0.0",
        "dataset_id": "ch6_diabetes_tasks",
        "question": "fixture",
        "variants": ["A0", "A1", "A2"],
    }
    validate_document("api#agent_task", document)


def test_unknown_schema_definition_is_rejected():
    with pytest.raises(ContractError, match="Unknown schema"):
        validate_document("api#missing", {})


def test_draft_and_inflight_seal_transitions_do_not_mutate_input():
    document = example("seal")
    document["state"] = "draft"
    original_hash = canonical_sha256(document)
    check_seal_transition(document, "locked", config_sha256=document["locked_config_sha256"])
    assert canonical_sha256(document) == original_hash
    document.update(state="evaluating", evaluation_count=1)
    check_seal_transition(document, "failed_sealed", config_sha256=document["locked_config_sha256"])
    with pytest.raises(ContractError, match="transition"):
        check_seal_transition(document, "draft", config_sha256=document["locked_config_sha256"])


@pytest.mark.parametrize(
    "field,error", [("input_sha256", "input hash"), ("comparison_group_sha256", "comparison group")]
)
def test_comparison_cannot_rank_different_inputs_or_training_conditions(field, error):
    document = example("api_job")
    document["results"][0][field] = "f" * 64
    with pytest.raises(ContractError, match=error):
        validate_document("api#job", document)
