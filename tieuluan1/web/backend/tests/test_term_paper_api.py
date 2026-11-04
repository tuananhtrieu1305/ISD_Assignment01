import json

import pytest

from backend.app import RateLimiter, allowed_origins, app, create_app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_root_describes_the_term_paper_api(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json() == {
        "name": "AI/ML/CNN/RNN Term Paper API",
        "docs": "/api/models",
        "health": "/health",
        "version": "2.0.0",
    }


def test_health_reports_all_verified_models(client):
    response = client.get("/health")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert set(payload["models"]) == {
        "diabetes",
        "eurosat",
        "customer_rnn",
        "aapl_rnn",
    }
    assert all(model["hash_verified"] for model in payload["models"].values())


def test_models_endpoint_exposes_only_public_registry_data(client):
    response = client.get("/api/models")
    payload = response.get_json()

    assert response.status_code == 200
    assert set(payload["models"]) == {
        "diabetes",
        "eurosat",
        "customer_rnn",
        "aapl_rnn",
    }
    assert "model_sha256" in payload["models"]["eurosat"]
    assert "model" not in payload["models"]["eurosat"]
    assert "preprocessors" not in payload["models"]["eurosat"]


@pytest.mark.parametrize(
    ("use_case", "expected_field"),
    [
        ("diabetes", "probability"),
        ("eurosat", "top_classes"),
        ("customer", "probability"),
        ("aapl", "naive_last_close_usd"),
    ],
)
def test_demo_to_prediction_flow_for_every_use_case(client, use_case, expected_field):
    demo_response = client.get(f"/api/demo/{use_case}")
    demo = demo_response.get_json()

    assert demo_response.status_code == 200
    assert demo["use_case"] == use_case

    prediction_response = client.post(
        f"/api/predict/{use_case}",
        json=demo["input"],
    )
    prediction = prediction_response.get_json()

    assert prediction_response.status_code == 200
    assert expected_field in prediction
    assert prediction["request_id"].startswith("req_")


def test_invalid_payload_uses_safe_consistent_error_envelope(client):
    response = client.post(
        "/api/predict/customer",
        json={"sequence": [[0, 0, 0, 0, 0]]},
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "invalid_input"
    assert "8 hàng" in payload["error"]["message"]
    assert payload["request_id"].startswith("req_")
    assert "Traceback" not in json.dumps(payload)


def test_prediction_requires_json_content_type(client):
    response = client.post(
        "/api/predict/diabetes",
        data="not-json",
        content_type="text/plain",
    )

    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "unsupported_media_type"


def test_unknown_api_route_returns_json_not_html(client):
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["error"]["code"] == "not_found"


def test_security_headers_are_present(client):
    response = client.get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["Cache-Control"] == "no-store"


def test_cors_accepts_local_react_and_configured_render_origin(client, monkeypatch):
    monkeypatch.setenv(
        "WEB_ORIGIN",
        "ai-term-paper-web.onrender.com,https://example.edu/",
    )

    assert "http://localhost:5173" in allowed_origins()
    assert "https://ai-term-paper-web.onrender.com" in allowed_origins()
    assert "https://example.edu" in allowed_origins()

    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"


def test_payload_larger_than_seven_megabytes_is_rejected(client):
    response = client.post(
        "/api/predict/eurosat",
        data=b"{" + b"x" * (7 * 1024 * 1024) + b"}",
        content_type="application/json",
    )

    assert response.status_code == 413
    assert response.get_json()["error"]["code"] == "payload_too_large"


def test_prediction_rate_limit_returns_429_before_inference():
    limited_app = create_app(
        model_service=object(),
        rate_limiter=RateLimiter(limit=0),
    )
    limited_app.config.update(TESTING=True)

    response = limited_app.test_client().post(
        "/api/predict/customer",
        json={"sequence": []},
    )

    assert response.status_code == 429
    assert response.get_json()["error"]["code"] == "rate_limited"


def test_https_proxy_response_includes_hsts(client):
    response = client.get(
        "/health",
        headers={"X-Forwarded-Proto": "https"},
    )

    assert response.headers["Strict-Transport-Security"].startswith("max-age=")
