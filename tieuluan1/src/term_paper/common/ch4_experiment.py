"""Artifact helpers for the matched Chapter 4 RNN experiment."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


def artifact_suffix(seed):
    return "" if int(seed) == 42 else f"_seed{int(seed)}"


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_prediction_frame(dataset_id, framework, keys, y_true, prediction, seed, task,
                           threshold, model_sha256, preprocessor_sha256, split_sha256,
                           baseline=None):
    y_true = np.asarray(y_true).reshape(-1)
    prediction = np.asarray(prediction).reshape(-1)
    if len(y_true) != len(prediction) or len(keys) != len(y_true):
        raise ValueError("keys, targets and predictions must align")
    frame = pd.DataFrame({
        "chapter": 4, "dataset_id": dataset_id, "framework": framework,
        "seed": int(seed), "split": "test", "sample_key": np.asarray(keys).astype(str),
        "y_true": y_true, "score_or_prediction": prediction,
        "model_sha256": model_sha256, "preprocessor_sha256": preprocessor_sha256,
        "split_sha256": split_sha256,
    })
    if task == "binary":
        frame["threshold"] = float(threshold)
        frame["y_pred"] = (prediction >= float(threshold)).astype(int)
    elif task == "regression":
        frame["y_pred"] = prediction
        if baseline is not None:
            frame["naive_last_close"] = np.asarray(baseline, dtype=float)
    else:
        raise ValueError(task)
    return frame
