"""Metrics and validation-only threshold selection for Chapter 4."""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix, f1_score,
    mean_absolute_error, mean_squared_error, precision_score, r2_score,
    recall_score, roc_auc_score,
)


def binary_metrics(y_true, scores, threshold):
    y_true = np.asarray(y_true, dtype=int).reshape(-1)
    scores = np.asarray(scores, dtype=float).reshape(-1)
    predicted = (scores >= float(threshold)).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, predicted)),
        "precision": float(precision_score(y_true, predicted, zero_division=0)),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "f1": float(f1_score(y_true, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "pr_auc": float(average_precision_score(y_true, scores)),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def regression_metrics(y_true, prediction):
    y_true = np.asarray(y_true, dtype=float).reshape(-1)
    prediction = np.asarray(prediction, dtype=float).reshape(-1)
    return {
        "mae": float(mean_absolute_error(y_true, prediction)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, prediction))),
        "r2": float(r2_score(y_true, prediction)),
    }


def select_f1_threshold(y_true, scores, thresholds=None):
    thresholds = np.asarray(thresholds if thresholds is not None else np.linspace(0.05, 0.95, 181))
    rows = []
    for threshold in thresholds:
        metric = binary_metrics(y_true, scores, float(threshold))
        rows.append({"threshold": float(threshold), "f1": metric["f1"], "precision": metric["precision"], "recall": metric["recall"]})
    table = pd.DataFrame(rows)
    best = table.sort_values(["f1", "threshold"], ascending=[False, True]).iloc[0]
    return float(best["threshold"]), table
