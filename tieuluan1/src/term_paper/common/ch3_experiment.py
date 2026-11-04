"""Artifact helpers for the Chapter 3 matched CNN experiment."""

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


def build_prediction_frame(
    dataset_id,
    framework,
    keys,
    y_true,
    probabilities,
    model_sha256,
    preprocessor_sha256,
    split_sha256,
    seed=42,
):
    probabilities = np.asarray(probabilities, dtype=float)
    y_true = np.asarray(y_true, dtype=int).reshape(-1)
    if probabilities.ndim != 2 or len(probabilities) != len(y_true):
        raise ValueError("probabilities must be a 2D array aligned with y_true")
    frame = pd.DataFrame(
        {
            "chapter": 3,
            "dataset_id": dataset_id,
            "framework": framework,
            "seed": int(seed),
            "split": "test",
            "sample_key": np.asarray(keys).astype(str),
            "y_true": y_true,
            "y_pred": np.argmax(probabilities, axis=1),
            "model_sha256": model_sha256,
            "preprocessor_sha256": preprocessor_sha256,
            "split_sha256": split_sha256,
        }
    )
    for class_index in range(probabilities.shape[1]):
        frame[f"prob_{class_index}"] = probabilities[:, class_index]
    return frame
