"""Real serving artifacts, TRAIN-only asynchronous requests and contract validation."""

import copy
import secrets
import time

import pytest
from jsonschema import Draft202012Validator

from apps.api.v3.inference import decode_input
from apps.api.v3.openapi import specification
from apps.api.v3.registry import Registry
from apps.api.v3.server import create_app
from src.common.contracts import validate_document

TOKEN = "client_" + "a" * 40


@pytest.fixture(scope="module")
def registry():
    return Registry()


@pytest.fixture
def app(tmp_path):
    result = create_app(database=tmp_path / "jobs.db", start_worker=False)
    result.config["TESTING"] = True
    return result


def check_response(path, method, reply):
    spec = specification()
    response = spec["paths"][path][method]["responses"][str(reply.status_code)]
    schema = response.get("content", {}).get("application/json", {}).get("schema")
    if schema:
        Draft202012Validator({**spec, **schema}).validate(reply.json)


@pytest.mark.parametrize(
    "path", ["/health", "/ready", "/api/v3/chapters", "/api/v3/datasets", "/api/v3/models", "/api/v3/runs"]
)
def test_list_contracts(app, path):
    reply = app.test_client().get(path)
    assert reply.status_code == 200
    check_response(path, "get", reply)


def test_all_model_contracts(app, registry):
    client = app.test_client()
    for identity in registry.models:
        reply = client.get(f"/api/v3/models/{identity}/contract")
        assert reply.status_code == 200
        check_response("/api/v3/models/{model_id}/contract", "get", reply)


def test_dataset_details_samples_artifact_and_run(app, registry):
    client = app.test_client()
    for identity in registry.datasets:
        reply = client.get(f"/api/v3/datasets/{identity}")
        assert reply.status_code == 200
        check_response("/api/v3/datasets/{dataset_id}", "get", reply)
        assert client.get(f"/api/v3/datasets/{identity}/overview").status_code == 200
    identity = next(iter(registry.document["public_artifacts"]))
    reply = client.get(f"/api/v3/artifacts/{identity}")
    check_response("/api/v3/artifacts/{artifact_id}", "get", reply)
    assert client.get(reply.json["data"]["content_url"]).status_code == 200
    run_id = registry.document["runs"][0]["run_id"]
    reply = client.get(f"/api/v3/runs/{run_id}")
    check_response("/api/v3/runs/{run_id}", "get", reply)


@pytest.mark.parametrize(
    "query", ["page=0", "page_size=101", "page=hi", "chapter=9", "extra=1", "page=1&page=2"]
)
def test_invalid_query(app, query):
    reply = app.test_client().get("/api/v3/datasets?" + query)
    assert reply.status_code == 400
    validate_document("api#error", reply.json)


@pytest.mark.parametrize(
    "payload,media,code",
    [
        ('{"a":1,"a":2}', "application/json", 400),
        ('{"a":NaN}', "application/json", 400),
        ("[]", "application/json", 400),
        ("{", "application/json", 400),
        ("{}", "text/plain", 415),
        ("{}", "application/json", 422),
    ],
)
def test_invalid_bodies(app, payload, media, code):
    reply = app.test_client().post(
        "/api/v3/comparisons",
        data=payload,
        content_type=media,
        headers={"X-Client-Token": TOKEN, "Idempotency-Key": "request_key_1"},
    )
    assert reply.status_code == code
    validate_document("api#error", reply.json)


def test_cors_headers_and_no_secret_leak(app):
    client = app.test_client()
    reply = client.options("/api/v3/comparisons", headers={"Origin": "http://localhost:5173"})
    assert reply.status_code == 204
    assert reply.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    denied = client.get("/health", headers={"Origin": "https://attacker.invalid"})
    assert denied.status_code == 403
    assert "Access-Control-Allow-Origin" not in denied.headers
    assert denied.headers["X-Content-Type-Options"] == "nosniff"


def test_capability_and_idempotency(app, registry):
    client = app.test_client()
    payload = registry.json(registry.document["samples"])["ch2_cdc_diabetes"]["request"]
    headers = {"X-Client-Token": TOKEN, "Idempotency-Key": "key_123456"}
    accepted = client.post("/api/v3/comparisons", json=payload, headers=headers)
    check_response("/api/v3/comparisons", "post", accepted)
    again = client.post("/api/v3/comparisons", json=payload, headers=headers)
    assert again.json["job_id"] == accepted.json["job_id"]
    url = accepted.json["poll_url"]
    assert client.get(url).status_code == 400
    assert client.get(url, headers={"X-Client-Token": "b" * 40}).status_code == 404
    reply = client.get(url, headers=headers)
    check_response("/api/v3/jobs/{job_id}", "get", reply)
    cancellation = client.post(url + "/cancellations", json={"reason": "user_cancelled"}, headers=headers)
    check_response("/api/v3/jobs/{job_id}/cancellations", "post", cancellation)
    assert client.get(url, headers=headers).json["status"] == "cancelled"
    assert client.get(url + "/details", headers=headers).status_code == 200


def test_rate_limit(app):
    client = app.test_client()
    codes = [client.get("/no-such-path").status_code for _ in range(241)]
    assert codes[-1] == 429
    assert client.get("/health").status_code == 200


@pytest.mark.parametrize(
    "family,dataset",
    [
        ("mlp", "ch2_cdc_diabetes"),
        ("mlp", "ch2_ames_housing"),
        ("mlp", "ch2_bank_marketing"),
        ("cnn", "ch3_idrid"),
        ("cnn", "ch3_eurosat"),
        ("cnn", "ch3_cifar10"),
        ("rnn", "ch4_gold_pink_sheet"),
        ("rnn", "ch4_bis_house_prices"),
        ("rnn", "ch4_household_power"),
        ("lstm", "ch4_gold_pink_sheet"),
        ("lstm", "ch4_bis_house_prices"),
        ("lstm", "ch4_household_power"),
        ("kg_rag", "ch5_medquad_diabetes"),
        ("kg_rag", "ch5_finqa"),
        ("kg_rag", "ch5_wikidata_subgraphs"),
        ("multi_agent", "ch6_diabetes_tasks"),
        ("multi_agent", "ch6_house_tasks"),
        ("multi_agent", "ch6_gold_tasks"),
    ],
)
def test_real_async_cpu_compare(tmp_path, registry, family, dataset):
    application = create_app(database=tmp_path / "real.db", mode="cpu")
    # Pytest collection imports the old sklearn bundle for parity tests in this
    # same process; this is not the production web footprint. Keep actual PSS
    # telemetry, use an explicit harness budget. Live Gunicorn probes retain448MiB.
    application.extensions["supervisor"].memory_bytes = 2 * 1024**3
    client = application.test_client()
    payload = copy.deepcopy(registry.json(registry.document["samples"])[dataset]["request"])
    payload["family"] = family
    headers = {"X-Client-Token": TOKEN, "Idempotency-Key": secrets.token_hex(12)}
    try:
        reply = client.post("/api/v3/comparisons", json=payload, headers=headers)
        assert reply.status_code == 202, reply.json
        deadline = time.monotonic() + 65
        while time.monotonic() < deadline:
            job = client.get(reply.json["poll_url"], headers=headers)
            if job.json["status"] not in {"queued", "running"}:
                break
            time.sleep(0.4)
        validate_document("api#job", job.json)
        if dataset == "ch5_wikidata_subgraphs":
            assert job.json["status"] == "failed"
            assert all(r["status"] == "unavailable" for r in job.json["results"])
            details = client.get(reply.json["poll_url"] + "/details", headers=headers).json["data"]
            assert details["entity"]["qa_benchmark"] is False
        else:
            assert job.json["status"] == "succeeded", job.json
            assert all(
                r["actual_backend"] == "numpy" and r["actual_device"] == "cpu" for r in job.json["results"]
            )
        for trace_id in job.json["trace_ids"]:
            trace = client.get("/api/v3/agent-traces/" + trace_id, headers=headers)
            check_response("/api/v3/agent-traces/{trace_id}", "get", trace)
    finally:
        application.extensions["supervisor"].close()


def test_sequence_bad_shape_and_tabular_extra(registry):
    samples = registry.json(registry.document["samples"])
    request = copy.deepcopy(samples["ch4_gold_pink_sheet"]["request"])
    request["input"]["values"] = [[0]]
    with pytest.raises(ValueError):
        decode_input(registry, request)
    request = copy.deepcopy(samples["ch2_cdc_diabetes"]["request"])
    request["input"]["features"]["target"] = 1
    with pytest.raises(ValueError):
        decode_input(registry, request)
