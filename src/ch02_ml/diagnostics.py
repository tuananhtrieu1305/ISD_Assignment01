"""Descriptive calibration/group diagnostics; no threshold or TEST tuning."""

import numpy as np


def groups_for_frame(dataset, frame):
    if dataset == "ch2_cdc_diabetes":
        return np.asarray(frame.sex.astype(str).to_numpy(), dtype=str)
    if dataset == "ch2_bank_marketing":
        return np.where(frame.age.to_numpy() < 60, "age_lt60", "age_ge60")
    if dataset == "ch2_ames_housing":
        return np.where(frame.year_built.to_numpy() < 1980, "built_before1980", "built_from1980")
    raise ValueError("Unknown group diagnostic dataset")


def calibration(target, probability, bins=10):
    y = np.asarray(target).reshape(-1)
    p = np.asarray(probability).reshape(-1)
    if (
        bins < 1
        or y.shape != p.shape
        or not len(y)
        or not np.isin(y, [0, 1]).all()
        or not np.isfinite(p).all()
        or np.any((p < 0) | (p > 1))
    ):
        raise ValueError("Invalid calibration input")
    indices = np.minimum((p * bins).astype(int), bins - 1)
    rows = []
    ece = 0.0
    for i in range(bins):
        mask = indices == i
        count = int(mask.sum())
        confidence = float(p[mask].mean()) if count else None
        rate = float(y[mask].mean()) if count else None
        if count:
            ece += count / len(y) * abs(confidence - rate)
        rows.append(
            {
                "bin": i,
                "lower": i / bins,
                "upper": (i + 1) / bins,
                "count": count,
                "mean_probability": confidence,
                "observed_rate": rate,
            }
        )
    return {"brier": float(np.mean((p - y) ** 2)), "ece": float(ece), "bins": rows, "fit_calibrator": False}


def group_diagnostics(target, prediction, groups, task):
    y = np.asarray(target).reshape(-1)
    p = np.asarray(prediction).reshape(-1)
    groups = np.asarray(groups).reshape(-1)
    if y.shape != p.shape or groups.shape != y.shape or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("Invalid diagnostic arrays")
    rows = {}
    for group in np.unique(groups):
        mask = groups == group
        a, b = y[mask], p[mask]
        count = int(mask.sum())
        if task == "binary":
            positive = a == 1
            negative = a == 0
            pred = b > 0.5
            rows[str(group)] = {
                "count": count,
                "prevalence": float(a.mean()),
                "predicted_positive_rate": float(pred.mean()),
                "recall": float(pred[positive].mean()) if positive.any() else None,
                "false_positive_rate": float(pred[negative].mean()) if negative.any() else None,
                "brier": float(np.mean((b - a) ** 2)),
                "undefined_reason": "No positive or negative support"
                if not positive.any() or not negative.any()
                else None,
            }
        elif task == "mse":
            rows[str(group)] = {
                "count": count,
                "mae": float(np.abs(a - b).mean()),
                "rmse": float(np.sqrt(np.mean((a - b) ** 2))),
            }
        else:
            raise ValueError("Unknown diagnostic task")
    return rows
