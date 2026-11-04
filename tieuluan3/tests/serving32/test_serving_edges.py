"""Security/partial failure tests before final hardening."""

import base64
import copy
import io

import numpy as np
import pytest
from PIL import Image

from apps.api.v3.inference import decode_input, neural_compare, prediction_from
from apps.api.v3.registry import ArtifactError, Registry
from apps.api.v3.server import create_app, depth_guard, strict_object


@pytest.fixture(scope="module")
def registry():
    return Registry()


def test_one_failed_slot_is_explicit(registry, monkeypatch):
    from apps.api.v3 import inference

    request = registry.json(registry.document["samples"])["ch2_cdc_diabetes"]["request"]
    original = inference.load_model

    def failing(registry, spec):
        if spec["implementation"] == "keras":
            raise ArtifactError("Synthetic unavailable slot")
        return original(registry, spec)

    monkeypatch.setattr(inference, "load_model", failing)
    job, _ = neural_compare(registry, request)
    assert job["status"] == "partial_failed"
    assert [r["status"] for r in job["results"]] == ["succeeded", "unavailable", "succeeded"]
    assert not job["comparison_valid"]
    assert job["results"][1]["prediction"] is None


@pytest.mark.parametrize("features", [{"bmi": float("nan")}, {"bmi": 1e20}, {"bmi": "33"}])
def test_numeric_input_fails_closed(registry, features):
    request = copy.deepcopy(registry.json(registry.document["samples"])["ch2_cdc_diabetes"]["request"])
    request["input"]["features"].update(features)
    with pytest.raises(ValueError):
        decode_input(registry, request)


@pytest.mark.parametrize("kind", ["wrong_mime", "rgba", "broken"])
def test_encoded_image_validation(registry, kind):
    request = copy.deepcopy(registry.json(registry.document["samples"])["ch3_cifar10"]["request"])
    if kind == "wrong_mime":
        request["input"]["media_type"] = "image/jpeg"
    elif kind == "rgba":
        out = io.BytesIO()
        Image.new("RGBA", (8, 8)).save(out, format="PNG")
        request["input"]["data"] = base64.b64encode(out.getvalue()).decode()
    else:
        request["input"]["data"] = "abcd"
    with pytest.raises(ValueError):
        decode_input(registry, request)


def test_bis_one_country_and_domain(registry):
    samples = registry.json(registry.document["samples"])
    request = copy.deepcopy(samples["ch4_bis_house_prices"]["request"])
    request["input"]["values"][0][2:] = [0] * 49
    with pytest.raises(ValueError):
        decode_input(registry, request)
    request = copy.deepcopy(samples["ch5_finqa"]["request"])
    request["input"]["domain"] = "medical"
    with pytest.raises(ValueError):
        decode_input(registry, request)


def test_budget_and_unknowns(tmp_path):
    app = create_app(database=tmp_path / "jobs.db", start_worker=False)
    client = app.test_client()
    assert (
        client.post("/api/v3/comparisons", data="x" * 6_400_001, content_type="application/json").status_code
        == 413
    )
    for path in [
        "chapters/9",
        "datasets/unknown",
        "datasets/unknown/overview",
        "models/unknown/contract",
        "runs/unknown",
        "artifacts/unknown",
        "artifacts/unknown/content",
        "agent-traces/unknown",
    ]:
        reply = client.get("/api/v3/" + path)
        assert reply.status_code == 404
    assert client.get("/health", headers={"Host": "evil.invalid"}).status_code == 400
    assert client.get("/api/v3/openapi.json").status_code == 200
    assert client.get("/api/v3/runs?chapter=4&dataset_id=ch4_gold_pink_sheet").status_code == 200


def test_bad_agent_and_key(tmp_path, registry):
    app = create_app(database=tmp_path / "jobs.db", start_worker=False)
    client = app.test_client()
    assert client.post("/api/v3/agent-tasks", json={}).status_code == 422
    request = registry.json(registry.document["samples"])["ch2_cdc_diabetes"]["request"]
    assert client.post("/api/v3/comparisons", json=request).status_code == 400
    assert client.post("/api/v3/jobs/unknown/cancellations", json={}).status_code == 422


def test_json_depth_and_duplicate():
    with pytest.raises(ValueError):
        strict_object([("x", 1), ("x", 2)])
    value = 0
    for _ in range(12):
        value = [value]
    with pytest.raises(ValueError):
        depth_guard(value)


def test_nonfinite_output_rejected():
    with pytest.raises(ValueError):
        prediction_from(np.asarray([[float("nan")]]), {}, None, {})
