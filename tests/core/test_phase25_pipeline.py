"""Small pipeline tests: schemas and deterministic generation contracts."""

import copy

import pytest
from jsonschema import Draft202012Validator

from scripts.prepare_phase25 import architecture_for, validate_adapter
from src.common.contracts import ROOT, read_json
from src.common.data_access import DatasetView


def test_schema_and_architecture_from_locked_data():
    for name in ["tensor_adapter", "training_plan"]:
        Draft202012Validator.check_schema(read_json(ROOT / f"src/common/schemas/phase25/{name}.schema.json"))
    view = DatasetView("ch2_ames_housing")
    document = view.contract()
    validate_adapter(document)
    plan = architecture_for(view, "mlp")
    assert plan["input_shape"] == [313] and plan["output_shape"] == [1]
    invalid = copy.deepcopy(document)
    invalid["output_feature_names"].append(invalid["output_feature_names"][0])
    with pytest.raises(ValueError):
        validate_adapter(invalid)
    invalid = copy.deepcopy(document)
    invalid["preprocessing"]["sha256"] = "invalid"
    with pytest.raises(ValueError):
        validate_adapter(invalid)
