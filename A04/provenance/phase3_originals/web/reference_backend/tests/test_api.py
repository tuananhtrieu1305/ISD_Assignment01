import math
import statistics
import json
from pathlib import Path

import pandas as pd

from app import (
    CUSTOMER_FEATURES,
    DEFAULT_DIABETES_MODEL_ID,
    DEFAULT_CUSTOMER_MODEL_ID,
    DEFAULT_HOUSE_MODEL_ID,
    DIABETES_FEATURES,
    HOUSE_FEATURES,
    allowed_origins,
    app,
    customer_models,
    diabetes_models,
    house_models,
    normalize_artifact_relative_path,
)


ROOT = Path(__file__).resolve().parents[2]


def load_demo_input(folder):
    return json.loads((ROOT / "pipeline" / folder / "demo_input.json").read_text())


DIABETES_DEMO_INPUT = load_demo_input("diabetes")
HOUSE_DEMO_INPUT = load_demo_input("house_price")
CUSTOMER_DEMO_INPUT = load_demo_input("customer_behavior")


def test_health_reports_loaded_models():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "models": {"diabetes": True, "house": True, "customer_behavior": True},
    }


def test_cors_allows_local_development_origin():
    client = app.test_client()

    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"


def test_allowed_origins_includes_configured_web_origin(monkeypatch):
    monkeypatch.setenv("WEB_ORIGIN", "https://assignment-web.onrender.com/")

    assert "https://assignment-web.onrender.com" in allowed_origins()


def test_artifact_paths_accept_windows_style_metadata_paths():
    assert normalize_artifact_relative_path(
        "diabetes_models\\logistic_regression.joblib"
    ) == ("diabetes_models", "logistic_regression.joblib")


def test_model_options_are_available():
    client = app.test_client()

    response = client.get("/api/models")
    data = response.get_json()

    assert response.status_code == 200
    assert data["diabetes"]["default_model"] == DEFAULT_DIABETES_MODEL_ID
    assert data["house"]["default_model"] == DEFAULT_HOUSE_MODEL_ID
    assert data["customer_behavior"]["default_model"] == DEFAULT_CUSTOMER_MODEL_ID
    assert len(data["diabetes"]["models"]) >= 1
    assert len(data["house"]["models"]) >= 1
    assert len(data["customer_behavior"]["models"]) >= 1


def test_feature_schemas_return_demo_inputs():
    client = app.test_client()

    response = client.get("/api/schemas")
    data = response.get_json()

    assert response.status_code == 200
    assert data["diabetes"]["feature_order"] == DIABETES_FEATURES
    assert data["house"]["feature_order"] == HOUSE_FEATURES
    assert data["customer_behavior"]["feature_order"] == CUSTOMER_FEATURES
    assert data["diabetes"]["demo_input"] == DIABETES_DEMO_INPUT


def test_diabetes_prediction_matches_direct_joblib():
    client = app.test_client()
    model = diabetes_models[DEFAULT_DIABETES_MODEL_ID]["model"]
    frame = pd.DataFrame([[DIABETES_DEMO_INPUT[name] for name in DIABETES_FEATURES]], columns=DIABETES_FEATURES)
    expected_prediction = int(model.predict(frame)[0])
    expected_probability = float(model.predict_proba(frame)[0][1])

    response = client.post("/api/diabetes", json=DIABETES_DEMO_INPUT)
    data = response.get_json()

    assert response.status_code == 200
    assert data["task"] == "diabetes"
    assert data["prediction"] == expected_prediction
    assert math.isclose(data["probability"], expected_probability, rel_tol=1e-12)
    assert data["model"]["id"] == DEFAULT_DIABETES_MODEL_ID


def test_house_prediction_matches_direct_joblib():
    client = app.test_client()
    model = house_models[DEFAULT_HOUSE_MODEL_ID]["model"]
    frame = pd.DataFrame([[HOUSE_DEMO_INPUT[name] for name in HOUSE_FEATURES]], columns=HOUSE_FEATURES)
    expected_price = float(model.predict(frame)[0])

    response = client.post("/api/house", json=HOUSE_DEMO_INPUT)
    data = response.get_json()

    assert response.status_code == 200
    assert data["task"] == "house"
    assert math.isclose(data["predicted_price"], expected_price, rel_tol=1e-12)
    assert data["model"]["id"] == DEFAULT_HOUSE_MODEL_ID


def test_missing_required_field_returns_400():
    client = app.test_client()
    payload = DIABETES_DEMO_INPUT.copy()
    payload.pop(DIABETES_FEATURES[0])

    response = client.post("/api/diabetes", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": f"Missing required field: {DIABETES_FEATURES[0]}"}


def test_invalid_numeric_value_returns_400():
    client = app.test_client()
    payload = HOUSE_DEMO_INPUT.copy()
    payload[HOUSE_FEATURES[0]] = "sixty"

    response = client.post("/api/house", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": f"Invalid number for field: {HOUSE_FEATURES[0]}"}


def test_invalid_model_selection_returns_400():
    client = app.test_client()
    payload = DIABETES_DEMO_INPUT.copy()
    payload["model"] = "not_a_real_model"

    response = client.post("/api/diabetes", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid model selection."}


def test_diabetes_compare_returns_all_models_and_consensus():
    client = app.test_client()

    response = client.post("/api/diabetes/compare", json=DIABETES_DEMO_INPUT)
    data = response.get_json()
    results = data["results"]

    assert response.status_code == 200
    assert data["task"] == "diabetes"
    assert len(results) == len(diabetes_models)
    assert len({result["model_id"] for result in results}) == len(diabetes_models)
    assert any(result["recommended"] for result in results)

    for result in results:
        if "probability" in result:
            assert 0 <= result["probability"] <= 1

        single_payload = DIABETES_DEMO_INPUT | {"model": result["model_id"]}
        single_response = client.post("/api/diabetes", json=single_payload)
        single_data = single_response.get_json()

        assert single_response.status_code == 200
        assert single_data["prediction"] == result["prediction"]
        if "probability" in result:
            assert math.isclose(
                single_data["probability"],
                result["probability"],
                rel_tol=1e-12,
            )

    predictions = [result["prediction"] for result in results]
    majority_prediction = max(set(predictions), key=predictions.count)
    agreeing_models = predictions.count(majority_prediction)
    consensus = data["consensus"]

    assert consensus["majority_prediction"] == majority_prediction
    assert consensus["agreeing_models"] == agreeing_models
    assert consensus["total_models"] == len(diabetes_models)
    assert math.isclose(consensus["agreement_ratio"], agreeing_models / len(diabetes_models))


def test_house_compare_returns_all_models_and_spread():
    client = app.test_client()

    response = client.post("/api/house/compare", json=HOUSE_DEMO_INPUT)
    data = response.get_json()
    results = data["results"]

    assert response.status_code == 200
    assert data["task"] == "house"
    assert len(results) == len(house_models)
    assert len({result["model_id"] for result in results}) == len(house_models)
    assert any(result["recommended"] for result in results)

    for result in results:
        single_payload = HOUSE_DEMO_INPUT | {"model": result["model_id"]}
        single_response = client.post("/api/house", json=single_payload)
        single_data = single_response.get_json()

        assert single_response.status_code == 200
        assert math.isclose(
            single_data["predicted_price"],
            result["predicted_price"],
            rel_tol=1e-12,
        )

    prices = [result["predicted_price"] for result in results]
    spread = data["spread"]

    assert spread["min"] == min(prices)
    assert spread["max"] == max(prices)
    assert math.isclose(spread["mean"], statistics.fmean(prices))
    assert math.isclose(spread["median"], statistics.median(prices))
    assert math.isclose(spread["range"], max(prices) - min(prices))


def test_customer_behavior_prediction_matches_direct_numpy_dnn():
    client = app.test_client()
    model = customer_models[DEFAULT_CUSTOMER_MODEL_ID]["model"]
    frame = pd.DataFrame([[CUSTOMER_DEMO_INPUT[name] for name in CUSTOMER_FEATURES]], columns=CUSTOMER_FEATURES)
    expected_prediction = int(model.predict(frame)[0])
    expected_probability = float(model.predict_proba(frame)[0][1])

    response = client.post("/api/customer-behavior", json=CUSTOMER_DEMO_INPUT)
    data = response.get_json()

    assert response.status_code == 200
    assert data["task"] == "customer_behavior"
    assert data["prediction"] == expected_prediction
    assert math.isclose(data["churn_score"], expected_probability, rel_tol=1e-12)
    assert data["model"]["id"] == DEFAULT_CUSTOMER_MODEL_ID
