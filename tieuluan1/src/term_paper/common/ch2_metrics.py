"""Metric computation from prediction artifacts for Chapter 2."""

from pathlib import Path

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


def compute_classification_metrics(y_true, y_pred, y_score):
    y_true = np.asarray(y_true, dtype=int).reshape(-1)
    y_pred = np.asarray(y_pred, dtype=int).reshape(-1)
    y_score = np.asarray(y_score, dtype=float).reshape(-1)
    metrics = {
        "Accuracy": float(accuracy_score(y_true, y_pred)),
        "Precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "Recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "F1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    metrics["ROC-AUC"] = (
        float(roc_auc_score(y_true, y_score)) if np.unique(y_true).size == 2 else np.nan
    )
    return metrics


def compute_regression_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float).reshape(-1)
    y_pred = np.asarray(y_pred, dtype=float).reshape(-1)
    mse = float(mean_squared_error(y_true, y_pred))
    denominator = np.maximum(np.abs(y_true), 1e-8)
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "MSE": mse,
        "RMSE": float(np.sqrt(mse)),
        "R2": float(r2_score(y_true, y_pred)),
        "MAPE": float(np.mean(np.abs((y_true - y_pred) / denominator)) * 100.0),
    }


def metrics_from_prediction_csv(path):
    frame = pd.read_csv(Path(path))
    tasks = frame["task"].dropna().astype(str).unique()
    if len(tasks) != 1:
        raise ValueError("Prediction artifact must contain exactly one task")
    if tasks[0] == "binary":
        return compute_classification_metrics(
            frame["y_true"], frame["y_pred"], frame["y_score"]
        )
    if tasks[0] == "regression":
        return compute_regression_metrics(frame["y_true"], frame["y_pred"])
    raise ValueError(f"Unsupported task: {tasks[0]}")

