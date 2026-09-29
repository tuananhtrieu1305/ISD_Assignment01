"""Artifact validation and summary helpers for A06 framework comparison."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)


CUSTOMER_COLUMNS = [
    "CustomerID",
    "target_week",
    "true_label",
    "probability",
    "predicted_label",
]
STOCK_COLUMNS = ["target_date", "actual_close", "predicted_close", "naive_close"]


def validate_customer_prediction_alignment(
    pytorch: pd.DataFrame,
    keras: pd.DataFrame,
) -> None:
    """Require both customer outputs to describe the same labeled TEST rows."""

    for name, frame in (("PyTorch", pytorch), ("Keras", keras)):
        if frame.columns.tolist() != CUSTOMER_COLUMNS:
            raise ValueError(f"{name} customer prediction schema is invalid")
        if frame.empty or frame.isna().any().any():
            raise ValueError(f"{name} customer predictions must be non-empty and complete")
        if frame.duplicated(["CustomerID", "target_week"]).any():
            raise ValueError(f"{name} customer keys must be unique")
        if not frame["probability"].between(0, 1).all():
            raise ValueError(f"{name} customer probabilities must lie in [0, 1]")

    keys_and_labels = ["CustomerID", "target_week", "true_label"]
    if not pytorch[keys_and_labels].equals(keras[keys_and_labels]):
        raise ValueError("customer keys and labels differ between frameworks")


def validate_stock_prediction_alignment(
    pytorch: pd.DataFrame,
    keras: pd.DataFrame,
) -> None:
    """Require both stock outputs to share dates, targets, and naive predictions."""

    for name, frame in (("PyTorch", pytorch), ("Keras", keras)):
        if frame.columns.tolist() != STOCK_COLUMNS:
            raise ValueError(f"{name} stock prediction schema is invalid")
        if frame.empty or frame.isna().any().any():
            raise ValueError(f"{name} stock predictions must be non-empty and complete")
        dates = pd.to_datetime(frame["target_date"], errors="raise")
        if dates.duplicated().any() or not dates.is_monotonic_increasing:
            raise ValueError(f"{name} target dates must be unique and chronological")

    if not pytorch["target_date"].equals(keras["target_date"]):
        raise ValueError("stock target dates differ between frameworks")
    if not np.allclose(pytorch["actual_close"], keras["actual_close"], rtol=0, atol=1e-10):
        raise ValueError("stock actual targets differ between frameworks")
    if not np.allclose(pytorch["naive_close"], keras["naive_close"], rtol=0, atol=1e-10):
        raise ValueError("stock naive predictions differ between frameworks")


def classification_metrics_from_predictions(
    predictions: pd.DataFrame,
    *,
    threshold: float = 0.5,
) -> dict[str, float]:
    """Recompute customer metrics directly from saved probabilities."""

    if not 0 <= threshold <= 1:
        raise ValueError("threshold must lie in [0, 1]")
    labels = predictions["true_label"].to_numpy(dtype=np.int8)
    probabilities = predictions["probability"].to_numpy(dtype=np.float64)
    predicted = (probabilities >= threshold).astype(np.int8)
    if "predicted_label" in predictions and not np.array_equal(
        predicted, predictions["predicted_label"].to_numpy(dtype=np.int8)
    ):
        raise ValueError("stored customer labels do not match the fixed threshold")
    return {
        "accuracy": float(accuracy_score(labels, predicted)),
        "precision": float(precision_score(labels, predicted, zero_division=0)),
        "recall": float(recall_score(labels, predicted, zero_division=0)),
        "f1": float(f1_score(labels, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(labels, probabilities)),
    }


def regression_metrics_from_predictions(
    predictions: pd.DataFrame,
    prediction_column: str,
) -> dict[str, float]:
    """Recompute real-scale stock metrics from saved prediction rows."""

    if prediction_column not in predictions:
        raise ValueError(f"missing prediction column: {prediction_column}")
    actual = predictions["actual_close"].to_numpy(dtype=np.float64)
    predicted = predictions[prediction_column].to_numpy(dtype=np.float64)
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def build_customer_metric_table(
    pytorch_metrics: dict[str, Any],
    keras_metrics: dict[str, Any],
) -> pd.DataFrame:
    """Create the required customer metric and training-metadata table."""

    rows = []
    for label, payload in (
        ("PyTorch RNN", pytorch_metrics),
        ("Keras SimpleRNN", keras_metrics),
    ):
        metrics = payload["evaluation"]["metrics"]
        rows.append(
            {
                "Model": label,
                "Accuracy": metrics["accuracy"],
                "Precision": metrics["precision"],
                "Recall": metrics["recall"],
                "F1-score": metrics["f1"],
                "ROC-AUC": metrics["roc_auc"],
                "Parameters": payload["architecture"]["parameter_count"],
                "Epochs": payload["training"]["epochs_actually_run"],
                "Training seconds": payload["training"]["training_duration_seconds"],
                "Device": payload["device"],
            }
        )
    return pd.DataFrame(rows).set_index("Model")


def build_stock_metric_table(
    pytorch_metrics: dict[str, Any],
    keras_metrics: dict[str, Any],
) -> pd.DataFrame:
    """Create stock comparison rows after checking stored baseline equality."""

    baseline_keys = ("naive_MAE", "naive_RMSE", "naive_R2")
    if not all(
        np.isclose(pytorch_metrics[key], keras_metrics[key], rtol=0, atol=1e-12)
        for key in baseline_keys
    ):
        raise ValueError("stored stock baseline metrics differ between frameworks")

    return pd.DataFrame(
        [
            {
                "Model": "PyTorch RNN",
                "MAE (USD)": pytorch_metrics["MAE"],
                "RMSE (USD)": pytorch_metrics["RMSE"],
                "R²": pytorch_metrics["R2"],
            },
            {
                "Model": "Keras SimpleRNN",
                "MAE (USD)": keras_metrics["MAE"],
                "RMSE (USD)": keras_metrics["RMSE"],
                "R²": keras_metrics["R2"],
            },
            {
                "Model": "Naive last Close",
                "MAE (USD)": pytorch_metrics["naive_MAE"],
                "RMSE (USD)": pytorch_metrics["naive_RMSE"],
                "R²": pytorch_metrics["naive_R2"],
            },
        ]
    ).set_index("Model")
