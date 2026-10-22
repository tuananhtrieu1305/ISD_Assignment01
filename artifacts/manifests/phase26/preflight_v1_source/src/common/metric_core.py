"""Finite metrics in original units; undefined metrics are null with a reason."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    recall_score,
    roc_auc_score,
)


def metric(value=None, reason=None):
    return {"value": float(value) if value is not None else None, "undefined_reason": reason}


def classification_metrics(target, probabilities):
    target = np.asarray(target)
    probs = np.asarray(probabilities, dtype=float)
    if (
        target.ndim != 1
        or not len(target)
        or probs.ndim != 2
        or len(probs) != len(target)
        or probs.shape[1] < 2
        or not np.isfinite(probs).all()
        or np.any(probs < 0)
        or np.any(probs > 1)
        or not np.allclose(probs.sum(axis=1), 1)
        or not np.isin(target, np.arange(probs.shape[1])).all()
    ):
        raise ValueError("Invalid classification labels/probabilities")
    classes = np.arange(probs.shape[1])
    prediction = probs.argmax(axis=1)
    result = {
        "accuracy": metric(accuracy_score(target, prediction)),
        "macro_f1": metric(f1_score(target, prediction, labels=classes, average="macro", zero_division=0)),
        "weighted_f1": metric(
            f1_score(target, prediction, labels=classes, average="weighted", zero_division=0)
        ),
        "confusion_matrix": confusion_matrix(target, prediction, labels=classes).tolist(),
        "per_class_recall": {
            str(c): metric(recall_score(target, prediction, labels=[c], average=None, zero_division=0)[0])
            if np.any(target == c)
            else metric(reason="No true samples for this class")
            for c in classes
        },
    }
    if len(np.unique(target)) != len(classes):
        result.update(
            {
                key: metric(reason="Not all classes have positive and negative support")
                for key in ("auroc", "average_precision")
            }
        )
    elif len(classes) == 2:
        result["auroc"] = metric(roc_auc_score(target, probs[:, 1]))
        result["average_precision"] = metric(average_precision_score(target, probs[:, 1]))
    else:
        result["auroc"] = metric(roc_auc_score(target, probs, multi_class="ovr", average="macro"))
        result["average_precision"] = metric(
            average_precision_score(np.eye(len(classes))[target.astype(int)], probs, average="macro")
        )
    return result


def regression_metrics(target, prediction, horizons=None, series=None):
    target = np.asarray(target, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    if (
        target.shape != prediction.shape
        or not target.size
        or target.ndim not in {1, 2}
        or not np.isfinite(target).all()
        or not np.isfinite(prediction).all()
    ):
        raise ValueError("Invalid regression arrays")
    residual = prediction - target
    denom = np.abs(target) + np.abs(prediction)
    ratios = np.divide(2 * np.abs(residual), denom, out=np.zeros_like(residual), where=denom != 0)
    centered = np.sum((target - target.mean(axis=0)) ** 2)
    result = {
        "mae": metric(np.abs(residual).mean()),
        "rmse": metric(np.sqrt(np.mean(residual**2))),
        "smape": metric(100 * ratios.mean()),
        "r2": metric(1 - np.sum(residual**2) / centered)
        if len(target) > 1 and centered > 0
        else metric(reason="Insufficient samples or constant target"),
    }
    if horizons is not None:
        if target.ndim != 2 or len(horizons) != target.shape[1] or len(set(horizons)) != len(horizons):
            raise ValueError("Horizon shape mismatch")
        result["by_horizon"] = {
            str(h): regression_metrics(target[:, i], prediction[:, i]) for i, h in enumerate(horizons)
        }
    if series is not None:
        series = np.asarray(series)
        if series.shape != (len(target),):
            raise ValueError("Series shape mismatch")
        result["by_series"] = {
            str(s): regression_metrics(target[series == s], prediction[series == s], horizons)
            for s in np.unique(series)
        }
        result["macro_series_rmse"] = metric(
            np.mean([row["rmse"]["value"] for row in result["by_series"].values()])
        )
    return result
