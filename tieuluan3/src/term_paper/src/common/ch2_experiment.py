"""Artifact helpers for the Chapter 2 matched-framework experiment."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score


def artifact_suffix(seed):
    return "" if int(seed) == 42 else f"_seed{int(seed)}"


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select_binary_threshold(y_true, y_score):
    y_true = np.asarray(y_true, dtype=int).reshape(-1)
    y_score = np.asarray(y_score, dtype=float).reshape(-1)
    rows = []
    for threshold in np.linspace(0.2, 0.8, 61):
        prediction = (y_score >= threshold).astype(int)
        rows.append(
            {
                "threshold": float(threshold),
                "F1": float(f1_score(y_true, prediction, zero_division=0)),
            }
        )
    table = pd.DataFrame(rows)
    best = table.sort_values(["F1", "threshold"], ascending=[False, True]).iloc[0]
    return float(best["threshold"]), table


def build_prediction_frame(
    dataset_id,
    framework,
    task,
    keys,
    y_true,
    y_score,
    y_pred,
    threshold,
    model_sha256,
    preprocessor_sha256,
    split_sha256,
    seed=42,
):
    count = len(keys)
    scores = (
        np.asarray(y_score, dtype=float).reshape(-1)
        if y_score is not None
        else np.full(count, np.nan)
    )
    return pd.DataFrame(
        {
            "chapter": 2,
            "dataset_id": dataset_id,
            "framework": framework,
            "seed": int(seed),
            "split": "test",
            "sample_key": np.asarray(keys).astype(str),
            "task": task,
            "y_true": np.asarray(y_true).reshape(-1),
            "y_score": scores,
            "y_pred": np.asarray(y_pred).reshape(-1),
            "threshold": np.nan if threshold is None else float(threshold),
            "model_sha256": model_sha256,
            "preprocessor_sha256": preprocessor_sha256,
            "split_sha256": split_sha256,
        }
    )
