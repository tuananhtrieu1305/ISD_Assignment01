"""Tests for artifact-only framework comparison helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.framework_comparison import (
    build_customer_metric_table,
    build_stock_metric_table,
    classification_metrics_from_predictions,
    regression_metrics_from_predictions,
    validate_customer_prediction_alignment,
    validate_stock_prediction_alignment,
)


def _customer_frame(probabilities: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CustomerID": [1, 2, 3, 4],
            "target_week": ["2020-01-06"] * 4,
            "true_label": [0, 0, 1, 1],
            "probability": probabilities,
            "predicted_label": (np.asarray(probabilities) >= 0.5).astype(int),
        }
    )


def _stock_frame(naive: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "target_date": ["2025-01-02", "2025-01-03", "2025-01-06"],
            "actual_close": [10.0, 20.0, 30.0],
            "predicted_close": [12.0, 18.0, 30.0],
            "naive_close": naive,
        }
    )


def test_customer_alignment_requires_identical_keys_and_labels() -> None:
    pytorch = _customer_frame([0.1, 0.7, 0.8, 0.2])
    keras = _customer_frame([0.2, 0.6, 0.7, 0.3])

    validate_customer_prediction_alignment(pytorch, keras)
    keras.loc[0, "true_label"] = 1
    with pytest.raises(ValueError, match="keys and labels"):
        validate_customer_prediction_alignment(pytorch, keras)


def test_stock_alignment_rejects_inconsistent_naive_baseline() -> None:
    pytorch = _stock_frame([9.0, 10.0, 20.0])
    keras = _stock_frame([9.0, 10.0, 20.0])

    validate_stock_prediction_alignment(pytorch, keras)
    keras.loc[1, "naive_close"] = 999.0
    with pytest.raises(ValueError, match="naive"):
        validate_stock_prediction_alignment(pytorch, keras)


def test_metrics_recomputed_from_prediction_rows() -> None:
    customer = classification_metrics_from_predictions(_customer_frame([0.1, 0.7, 0.8, 0.2]))
    stock = regression_metrics_from_predictions(_stock_frame([9.0, 10.0, 20.0]), "predicted_close")

    assert customer == {
        "accuracy": 0.5,
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
        "roc_auc": 0.75,
    }
    assert stock["mae"] == 4.0 / 3.0
    assert np.isclose(stock["rmse"], np.sqrt(8.0 / 3.0))
    assert np.isclose(stock["r2"], 0.96)


def test_customer_table_includes_metrics_and_training_metadata() -> None:
    base = {
        "architecture": {"parameter_count": 4609},
        "training": {"epochs_actually_run": 11, "training_duration_seconds": 2.5},
        "device": "cpu",
        "evaluation": {"metrics": {"accuracy": 0.7, "precision": 0.2, "recall": 0.6, "f1": 0.3, "roc_auc": 0.75}},
    }
    table = build_customer_metric_table(base, base)

    assert table.index.tolist() == ["PyTorch RNN", "Keras SimpleRNN"]
    assert table.columns.tolist() == [
        "Accuracy", "Precision", "Recall", "F1-score", "ROC-AUC",
        "Parameters", "Epochs", "Training seconds", "Device",
    ]


def test_stock_table_contains_one_verified_naive_row() -> None:
    pytorch = {"MAE": 4.0, "RMSE": 5.0, "R2": 0.1, "naive_MAE": 1.0, "naive_RMSE": 2.0, "naive_R2": 0.9}
    keras = {"MAE": 6.0, "RMSE": 7.0, "R2": -0.1, "naive_MAE": 1.0, "naive_RMSE": 2.0, "naive_R2": 0.9}
    table = build_stock_metric_table(pytorch, keras)

    assert table.index.tolist() == ["PyTorch RNN", "Keras SimpleRNN", "Naive last Close"]
    assert table.loc["Naive last Close", "RMSE (USD)"] == 2.0


def test_stock_table_rejects_different_stored_baselines() -> None:
    pytorch = {"MAE": 4.0, "RMSE": 5.0, "R2": 0.1, "naive_MAE": 1.0, "naive_RMSE": 2.0, "naive_R2": 0.9}
    keras = {**pytorch, "naive_RMSE": 2.1}

    with pytest.raises(ValueError, match="baseline"):
        build_stock_metric_table(pytorch, keras)
