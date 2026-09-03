import json
import math
import os
import statistics
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
ARTIFACT_DIR = BASE_DIR.parent / "artifacts"

DIABETES_FEATURES = [
    "Glucose",
    "BMI",
    "Age",
    "Pregnancies",
    "BloodPressure",
    "DiabetesPedigreeFunction",
]
HOUSE_FEATURES = [
    "Area",
    "Frontage",
    "Access Road",
    "Floors",
    "Bedrooms",
    "Bathrooms",
]

DIABETES_DISCLAIMER = (
    "Educational machine-learning prediction only - not a medical diagnosis."
)
HOUSE_UNIT_NOTE = "Prediction uses the same unit as the dataset Price column."


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


diabetes_metadata = load_json(ARTIFACT_DIR / "diabetes_metadata.json")
house_metadata = load_json(ARTIFACT_DIR / "house_metadata.json")
customer_metadata = load_json(ARTIFACT_DIR / "customer_behavior_metadata.json")

CUSTOMER_FEATURES = customer_metadata["features"]
CUSTOMER_NUMERIC_FEATURES = customer_metadata["numeric_features"]
CUSTOMER_CATEGORICAL_FEATURES = customer_metadata["categorical_features"]
CUSTOMER_TEXT_FEATURE = customer_metadata["text_feature"]

if diabetes_metadata.get("features") != DIABETES_FEATURES:
    raise RuntimeError("Diabetes metadata features do not match backend schema.")

if house_metadata.get("features") != HOUSE_FEATURES:
    raise RuntimeError("House metadata features do not match backend schema.")


def normalize_artifact_relative_path(relative_path):
    return tuple(part for part in relative_path.replace("\\", "/").split("/") if part)


def resolve_artifact_path(relative_path):
    path = ARTIFACT_DIR.joinpath(
        *normalize_artifact_relative_path(relative_path)
    ).resolve()
    artifact_root = ARTIFACT_DIR.resolve()

    if artifact_root not in path.parents and path != artifact_root:
        raise RuntimeError("Model artifact path escapes artifacts directory.")

    return path


def load_model_catalog(metadata, fallback_model_path):
    available_models = metadata.get("available_models", {})
    catalog = {}

    for model_id, model_info in available_models.items():
        artifact_path = resolve_artifact_path(model_info["artifact"])
        catalog[model_id] = {
            "id": model_id,
            "name": model_info["name"],
            "recommended": bool(model_info.get("recommended", False)),
            "model": joblib.load(artifact_path),
        }

    recommended_id = metadata.get("recommended_model_id")
    if not catalog:
        recommended_id = "default"
        catalog[recommended_id] = {
            "id": recommended_id,
            "name": metadata.get("selected_model", "Default model"),
            "recommended": True,
            "model": joblib.load(fallback_model_path),
        }

    if recommended_id not in catalog:
        raise RuntimeError("Recommended model id is not present in metadata catalog.")

    return catalog, recommended_id


diabetes_models, DEFAULT_DIABETES_MODEL_ID = load_model_catalog(
    diabetes_metadata,
    MODEL_DIR / "diabetes_pipeline.joblib",
)
house_models, DEFAULT_HOUSE_MODEL_ID = load_model_catalog(
    house_metadata,
    MODEL_DIR / "house_pipeline.joblib",
)
customer_models, DEFAULT_CUSTOMER_MODEL_ID = load_model_catalog(
    customer_metadata,
    ARTIFACT_DIR / "customer_churn_pipeline.joblib",
)


def allowed_origins():
    origins = {"http://localhost:5173", "http://127.0.0.1:5173"}
    web_origin = os.getenv("WEB_ORIGIN", "").strip().rstrip("/")

    if web_origin:
        origins.add(web_origin)

    return sorted(origins)


app = Flask(__name__)
CORS(
    app,
    resources={
        r"/api/*": {"origins": allowed_origins()},
        r"/health": {"origins": allowed_origins()},
    },
)


class ValidationError(Exception):
    pass


def parse_json_body():
    try:
        payload = request.get_json(force=False, silent=False)
    except BadRequest as exc:
        raise ValidationError("Request body must be valid JSON.") from exc

    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object.")

    return payload


def parse_numeric_payload(payload, features):
    values = {}

    for field in features:
        if field not in payload:
            raise ValidationError(f"Missing required field: {field}")

        value = payload[field]
        if isinstance(value, bool):
            raise ValidationError(f"Invalid number for field: {field}")

        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"Invalid number for field: {field}") from exc

        if not math.isfinite(number):
            raise ValidationError(f"Invalid number for field: {field}")

        values[field] = number

    return pd.DataFrame([[values[field] for field in features]], columns=features)


def parse_customer_payload(payload):
    values = {}

    for field in CUSTOMER_NUMERIC_FEATURES:
        if field not in payload:
            raise ValidationError(f"Missing required field: {field}")

        value = payload[field]
        if isinstance(value, bool):
            raise ValidationError(f"Invalid number for field: {field}")

        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"Invalid number for field: {field}") from exc

        if not math.isfinite(number):
            raise ValidationError(f"Invalid number for field: {field}")

        values[field] = number

    for field in CUSTOMER_CATEGORICAL_FEATURES:
        if field not in payload:
            raise ValidationError(f"Missing required field: {field}")

        value = payload[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"Invalid text for field: {field}")

        values[field] = value.strip()

    text_value = payload.get(CUSTOMER_TEXT_FEATURE, "")
    if text_value is None:
        text_value = ""

    if not isinstance(text_value, str):
        raise ValidationError(f"Invalid text for field: {CUSTOMER_TEXT_FEATURE}")

    values[CUSTOMER_TEXT_FEATURE] = text_value.strip()

    return pd.DataFrame(
        [[values[field] for field in CUSTOMER_FEATURES]],
        columns=CUSTOMER_FEATURES,
    )


def parse_model_id(payload, catalog, default_model_id):
    model_id = payload.get("model", default_model_id)

    if not isinstance(model_id, str):
        raise ValidationError("Invalid model selection.")

    if model_id not in catalog:
        raise ValidationError("Invalid model selection.")

    return model_id


def public_model_options(catalog, default_model_id):
    return [
        {
            "id": model_id,
            "name": item["name"],
            "recommended": model_id == default_model_id or item["recommended"],
        }
        for model_id, item in catalog.items()
    ]


def positive_class_probability(model, frame):
    if not hasattr(model, "predict_proba"):
        return None

    probabilities = model.predict_proba(frame)[0]
    classes = getattr(model, "classes_", None)

    if classes is not None and 1 in classes:
        class_index = list(classes).index(1)
    else:
        class_index = 1

    return float(probabilities[class_index])


def positive_class_score(model, frame):
    probability = positive_class_probability(model, frame)
    if probability is not None:
        return probability

    if not hasattr(model, "decision_function"):
        return None

    score = model.decision_function(frame)
    if hasattr(score, "ravel"):
        raw_score = float(score.ravel()[0])
    else:
        raw_score = float(score[0])

    return 1 / (1 + math.exp(-raw_score))


def diabetes_prediction_result(model_id, model_entry, frame):
    model = model_entry["model"]
    prediction = int(model.predict(frame)[0])
    probability = positive_class_probability(model, frame)
    result = {
        "model_id": model_id,
        "model_name": model_entry["name"],
        "recommended": model_id == DEFAULT_DIABETES_MODEL_ID
        or model_entry["recommended"],
        "prediction": prediction,
    }

    if probability is not None:
        result["probability"] = probability

    return result


def house_prediction_result(model_id, model_entry, frame):
    return {
        "model_id": model_id,
        "model_name": model_entry["name"],
        "recommended": model_id == DEFAULT_HOUSE_MODEL_ID or model_entry["recommended"],
        "predicted_price": float(model_entry["model"].predict(frame)[0]),
    }


def customer_prediction_result(model_id, model_entry, frame):
    model = model_entry["model"]
    prediction = int(model.predict(frame)[0])
    churn_score = positive_class_score(model, frame)
    result = {
        "model_id": model_id,
        "model_name": model_entry["name"],
        "recommended": model_id == DEFAULT_CUSTOMER_MODEL_ID
        or model_entry["recommended"],
        "prediction": prediction,
    }

    if churn_score is not None:
        result["churn_score"] = churn_score

    return result


def diabetes_consensus(results):
    prediction_counts = {}
    for result in results:
        prediction = result["prediction"]
        prediction_counts[prediction] = prediction_counts.get(prediction, 0) + 1

    majority_prediction, agreeing_models = max(
        prediction_counts.items(),
        key=lambda item: item[1],
    )
    total_models = len(results)

    return {
        "majority_prediction": majority_prediction,
        "agreeing_models": agreeing_models,
        "total_models": total_models,
        "agreement_ratio": agreeing_models / total_models if total_models else 0,
    }


def customer_consensus(results):
    prediction_counts = {}
    for result in results:
        prediction = result["prediction"]
        prediction_counts[prediction] = prediction_counts.get(prediction, 0) + 1

    majority_prediction, agreeing_models = max(
        prediction_counts.items(),
        key=lambda item: item[1],
    )
    total_models = len(results)

    return {
        "majority_prediction": majority_prediction,
        "agreeing_models": agreeing_models,
        "total_models": total_models,
        "agreement_ratio": agreeing_models / total_models if total_models else 0,
    }


def house_spread(results):
    prices = [result["predicted_price"] for result in results]
    min_price = min(prices)
    max_price = max(prices)

    return {
        "min": min_price,
        "max": max_price,
        "mean": statistics.fmean(prices),
        "median": statistics.median(prices),
        "range": max_price - min_price,
    }


@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({"error": str(error)}), 400


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.exception("Unexpected API error")
    return jsonify({"error": "Unexpected server error."}), 500


@app.get("/")
def index():
    return jsonify(
        {
            "name": "Intelligent Systems Assignment API",
            "endpoints": [
                "/health",
                "/api/diabetes",
                "/api/house",
                "/api/customer-behavior",
            ],
        }
    )


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "models": {
                "diabetes": bool(diabetes_models),
                "house": bool(house_models),
                "customer_behavior": bool(customer_models),
            },
        }
    )


@app.get("/api/models")
def model_options():
    return jsonify(
        {
            "diabetes": {
                "default_model": DEFAULT_DIABETES_MODEL_ID,
                "models": public_model_options(
                    diabetes_models,
                    DEFAULT_DIABETES_MODEL_ID,
                ),
            },
            "house": {
                "default_model": DEFAULT_HOUSE_MODEL_ID,
                "models": public_model_options(house_models, DEFAULT_HOUSE_MODEL_ID),
            },
            "customer_behavior": {
                "default_model": DEFAULT_CUSTOMER_MODEL_ID,
                "models": public_model_options(
                    customer_models,
                    DEFAULT_CUSTOMER_MODEL_ID,
                ),
            },
        }
    )


@app.post("/api/diabetes")
def predict_diabetes():
    payload = parse_json_body()
    frame = parse_numeric_payload(payload, DIABETES_FEATURES)
    model_id = parse_model_id(payload, diabetes_models, DEFAULT_DIABETES_MODEL_ID)
    model_entry = diabetes_models[model_id]
    result = diabetes_prediction_result(model_id, model_entry, frame)

    response = {
        "task": "diabetes",
        "model": {"id": model_id, "name": model_entry["name"]},
        "prediction": result["prediction"],
        "label": "Positive class"
        if result["prediction"] == 1
        else "Negative class",
        "disclaimer": DIABETES_DISCLAIMER,
    }

    if "probability" in result:
        response["probability"] = result["probability"]

    return jsonify(response)


@app.post("/api/diabetes/compare")
def compare_diabetes_models():
    payload = parse_json_body()
    frame = parse_numeric_payload(payload, DIABETES_FEATURES)
    results = [
        diabetes_prediction_result(model_id, model_entry, frame)
        for model_id, model_entry in diabetes_models.items()
    ]

    return jsonify(
        {
            "task": "diabetes",
            "results": results,
            "consensus": diabetes_consensus(results),
        }
    )


@app.post("/api/house")
def predict_house():
    payload = parse_json_body()
    frame = parse_numeric_payload(payload, HOUSE_FEATURES)
    model_id = parse_model_id(payload, house_models, DEFAULT_HOUSE_MODEL_ID)
    model_entry = house_models[model_id]
    predicted_price = float(model_entry["model"].predict(frame)[0])

    return jsonify(
        {
            "task": "house",
            "model": {"id": model_id, "name": model_entry["name"]},
            "predicted_price": predicted_price,
            "unit_note": house_metadata.get("price_unit_note", HOUSE_UNIT_NOTE),
        }
    )


@app.post("/api/house/compare")
def compare_house_models():
    payload = parse_json_body()
    frame = parse_numeric_payload(payload, HOUSE_FEATURES)
    results = [
        house_prediction_result(model_id, model_entry, frame)
        for model_id, model_entry in house_models.items()
    ]

    return jsonify(
        {
            "task": "house",
            "results": results,
            "spread": house_spread(results),
            "unit_note": house_metadata.get("price_unit_note", HOUSE_UNIT_NOTE),
        }
    )


@app.post("/api/customer-behavior")
def predict_customer_behavior():
    payload = parse_json_body()
    frame = parse_customer_payload(payload)
    model_id = parse_model_id(payload, customer_models, DEFAULT_CUSTOMER_MODEL_ID)
    model_entry = customer_models[model_id]
    result = customer_prediction_result(model_id, model_entry, frame)

    response = {
        "task": "customer_behavior",
        "model": {"id": model_id, "name": model_entry["name"]},
        "prediction": result["prediction"],
        "label": "Có nguy cơ rời bỏ" if result["prediction"] == 1 else "Đang gắn bó",
        "interpretation": (
            "Mô hình xếp khách hàng vào nhóm có nguy cơ churn."
            if result["prediction"] == 1
            else "Mô hình xếp khách hàng vào nhóm còn gắn bó."
        ),
    }

    if "churn_score" in result:
        response["churn_score"] = result["churn_score"]

    return jsonify(response)


@app.post("/api/customer-behavior/compare")
def compare_customer_behavior_models():
    payload = parse_json_body()
    frame = parse_customer_payload(payload)
    results = [
        customer_prediction_result(model_id, model_entry, frame)
        for model_id, model_entry in customer_models.items()
    ]

    return jsonify(
        {
            "task": "customer_behavior",
            "results": results,
            "consensus": customer_consensus(results),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
