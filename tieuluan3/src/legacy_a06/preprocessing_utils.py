"""Shared, framework-neutral preprocessing utilities."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.config import SPLIT_RATIOS


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest without modifying ``path``."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def chronological_split_indices(
    timestamps: np.ndarray | pd.Series | pd.Index,
    ratios: Mapping[str, float] = SPLIT_RATIOS,
) -> dict[str, np.ndarray]:
    """Split by timestamp groups while approximating sample-count ratios.

    All samples sharing a target timestamp remain in the same split. Boundaries
    are chosen deterministically at the cumulative sample counts nearest 70%
    and 85%, subject to leaving at least one distinct timestamp per split.
    """

    values = pd.to_datetime(np.asarray(timestamps), errors="coerce").to_numpy(
        dtype="datetime64[ns]"
    )
    if values.ndim != 1 or len(values) == 0:
        raise ValueError("timestamps must be a non-empty one-dimensional array")
    if np.isnat(values).any():
        raise ValueError("timestamps contain NaT")

    ratio_values = np.array([ratios[name] for name in ("train", "val", "test")])
    if np.any(ratio_values <= 0) or not np.isclose(ratio_values.sum(), 1.0):
        raise ValueError("train/val/test ratios must be positive and sum to 1")

    unique_times, counts = np.unique(values, return_counts=True)
    if len(unique_times) < 3:
        raise ValueError("at least three distinct target timestamps are required")

    cumulative = np.cumsum(counts)
    train_candidates = np.arange(0, len(unique_times) - 2)
    train_goal = ratios["train"] * len(values)
    train_end_position = train_candidates[
        np.argmin(np.abs(cumulative[train_candidates] - train_goal))
    ]

    validation_candidates = np.arange(train_end_position + 1, len(unique_times) - 1)
    validation_goal = (ratios["train"] + ratios["val"]) * len(values)
    validation_end_position = validation_candidates[
        np.argmin(np.abs(cumulative[validation_candidates] - validation_goal))
    ]

    train_cutoff = unique_times[train_end_position]
    validation_cutoff = unique_times[validation_end_position]
    result = {
        "train": np.flatnonzero(values <= train_cutoff),
        "val": np.flatnonzero((values > train_cutoff) & (values <= validation_cutoff)),
        "test": np.flatnonzero(values > validation_cutoff),
    }
    if any(len(indices) == 0 for indices in result.values()):
        raise AssertionError("chronological split unexpectedly produced an empty split")
    return result


def fit_feature_scaler(train_x: np.ndarray) -> StandardScaler:
    """Fit a StandardScaler only on flattened TRAIN sequence observations."""

    train_array = np.asarray(train_x)
    if train_array.ndim != 3 or train_array.shape[-1] == 0:
        raise ValueError("train_x must have shape (samples, sequence_length, features)")
    if len(train_array) == 0 or not np.isfinite(train_array).all():
        raise ValueError("train_x must be non-empty and finite")
    scaler = StandardScaler()
    scaler.fit(train_array.reshape(-1, train_array.shape[-1]))
    return scaler


def transform_sequences(scaler: StandardScaler, sequences: np.ndarray) -> np.ndarray:
    """Apply a fitted feature scaler and restore the 3-D sequence shape."""

    values = np.asarray(sequences)
    if values.ndim != 3:
        raise ValueError("sequences must be three-dimensional")
    transformed = scaler.transform(values.reshape(-1, values.shape[-1]))
    return transformed.reshape(values.shape).astype(np.float32, copy=False)


def save_npz_atomic(path: Path, **arrays: np.ndarray) -> None:
    """Write a compressed NPZ then atomically replace the destination."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(temporary, destination)


def save_joblib_atomic(path: Path, value: Any) -> None:
    """Persist a Python object without leaving a partial final file."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    joblib.dump(value, temporary)
    os.replace(temporary, destination)


def write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    """Write sorted UTF-8 JSON with an atomic final replacement."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, destination)


def artifact_record(path: Path, project_root: Path) -> dict[str, Any]:
    """Describe a saved artifact with a project-relative path and checksum."""

    artifact = Path(path)
    return {
        "path": artifact.relative_to(project_root).as_posix(),
        "bytes": artifact.stat().st_size,
        "sha256": sha256_file(artifact),
    }


def iso_date(value: np.datetime64 | pd.Timestamp) -> str:
    """Serialize a date-like value as YYYY-MM-DD."""

    return pd.Timestamp(value).date().isoformat()
