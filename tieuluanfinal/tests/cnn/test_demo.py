import base64
import io
import sys

import numpy as np
import pytest
from PIL import Image

from scripts.demo_phase27 import decode_request, infer, saliency, sample_request
from src.common.contracts import validate_document
from src.common.model_core import build_plan, canonical_weights


def request():
    buffer = io.BytesIO()
    Image.fromarray(np.zeros((32, 32, 3), dtype="uint8")).save(buffer, format="PNG")
    return {
        "schema_version": "3.0.0",
        "chapter": 3,
        "dataset_id": "ch3_cifar10",
        "family": "cnn",
        "implementations": ["scratch", "keras", "pytorch"],
        "input": {
            "kind": "image",
            "encoding": "base64",
            "media_type": "image/png",
            "data": base64.b64encode(buffer.getvalue()).decode(),
        },
    }


def test_request_tensor_and_canonical_hash():
    x = decode_request(request())
    assert x.shape == (1, 32, 32, 3) and x.dtype == np.float32
    assert not x.any()


def test_invalid_image_and_family_are_rejected():
    value = request()
    value["input"]["data"] = "eHh4eA=="
    with pytest.raises(ValueError):
        decode_request(value)
    value = request()
    value["family"] = "mlp"
    with pytest.raises(ValueError):
        decode_request(value)
    value = request()
    value["input"]["data"] = "@@@@"
    with pytest.raises(ValueError):
        decode_request(value)


def test_saliency_finite_and_not_a_clinical_explanation():
    plan = build_plan("cnn", [8, 8, 3], 3, tiny=True)
    x = np.random.default_rng(9).random((1, 8, 8, 3), dtype=np.float32)
    output = saliency(plan, canonical_weights(plan, 17), x)
    assert output["map"].shape == (8, 8)
    assert np.isfinite(output["map"]).all()
    assert 0 <= output["map"].min() <= output["map"].max() <= 1


def test_real_idrid_checkpoints_obey_cpu_api_contract_on_train_sample():
    before = set(sys.modules)
    value, sample_id = sample_request("ch3_idrid")
    job = infer(value, seed=42)
    validate_document("api#job", job)
    assert sample_id.startswith("train/")
    assert job["comparison_valid"] and len(job["results"]) == 3
    assert {row["actual_backend"] for row in job["results"]} == {"numpy"}
    assert {row["actual_device"] for row in job["results"]} == {"cpu"}
    added = set(sys.modules) - before
    assert not any(
        name == prefix or name.startswith(prefix + ".")
        for name in added
        for prefix in ("torch", "tensorflow", "keras")
    )
