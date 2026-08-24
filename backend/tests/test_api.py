import math
import statistics

import pandas as pd

from app import (
    DEFAULT_DIABETES_MODEL_ID,
    DEFAULT_HOUSE_MODEL_ID,
    DIABETES_FEATURES,
    HOUSE_FEATURES,
    allowed_origins,
    app,
    diabetes_models,
    house_models,
)


DIABETES_DEMO_INPUT = {
    "Glucose": 125,
    "BMI": 29.5,
    "Age": 38,
    "Pregnancies": 3,
    "BloodPressure": 78,
    "DiabetesPedigreeFunction": 0.55,
}

HOUSE_DEMO_INPUT = {
    "Area": 70,
    "Frontage": 5.0,
    "Access Road": 6.0,
    "Floors": 4,
    "Bedrooms": 4,
    "Bathrooms": 3,
}


def test_health_reports_loaded_models():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "models": {"diabetes": True, "house": True},
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


def test_model_options_are_available():
    client = app.test_client()

    response = client.get("/api/models")
    data = response.get_json()

    assert response.status_code == 200
    assert data["diabetes"]["default_model"] == DEFAULT_DIABETES_MODEL_ID
    assert data["house"]["default_model"] == DEFAULT_HOUSE_MODEL_ID
    assert len(data["diabetes"]["models"]) >= 1
    assert len(data["house"]["models"]) >= 1


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
    payload.pop("BMI")

    response = client.post("/api/diabetes", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": "Missing required field: BMI"}


def test_invalid_numeric_value_returns_400():
    client = app.test_client()
    payload = HOUSE_DEMO_INPUT.copy()
    payload["Area"] = "sixty"

    response = client.post("/api/house", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid number for field: Area"}


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
    assert len(results) == len(diabetes_models) == 5
    assert len({result["model_id"] for result in results}) == 5
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
    assert consensus["total_models"] == 5
    assert math.isclose(consensus["agreement_ratio"], agreeing_models / 5)


def test_house_compare_returns_all_models_and_spread():
    client = app.test_client()

    response = client.post("/api/house/compare", json=HOUSE_DEMO_INPUT)
    data = response.get_json()
    results = data["results"]

    assert response.status_code == 200
    assert data["task"] == "house"
    assert len(results) == len(house_models) == 5
    assert len({result["model_id"] for result in results}) == 5
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
