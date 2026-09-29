"""Deterministic AAPL sequence preprocessing shared by both frameworks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.config import (
    EXPECTED_STOCK_SHA256,
    PREPROCESSING_MODEL_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
    RAW_STOCK_PATH,
    SPLIT_RATIOS,
    STOCK_FEATURES,
    STOCK_REQUIRED_COLUMNS,
    STOCK_SEQUENCE_LENGTH,
)
from src.preprocessing_utils import (
    artifact_record,
    chronological_split_indices,
    fit_feature_scaler,
    iso_date,
    save_joblib_atomic,
    save_npz_atomic,
    sha256_file,
    transform_sequences,
)


def load_stock_data(path: Path = RAW_STOCK_PATH) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load and validate the locked local AAPL CSV without network access."""

    stock = pd.read_csv(path)
    if tuple(stock.columns) != STOCK_REQUIRED_COLUMNS:
        raise ValueError(f"unexpected stock schema: {stock.columns.tolist()}")

    raw_rows = int(len(stock))
    stock["Date"] = pd.to_datetime(stock["Date"], errors="coerce")
    numeric_columns = list(STOCK_REQUIRED_COLUMNS[1:])
    for column in numeric_columns:
        stock[column] = pd.to_numeric(stock[column], errors="coerce")

    integrity = {
        "raw_rows": raw_rows,
        "missing_values": {column: int(count) for column, count in stock.isna().sum().items()},
        "duplicate_dates": int(stock["Date"].duplicated().sum()),
        "chronological_before_sort": bool(stock["Date"].is_monotonic_increasing),
    }
    if stock.isna().any().any():
        raise ValueError("stock data contains missing or invalid values")
    if stock["Date"].duplicated().any():
        raise ValueError("stock data contains duplicate dates")
    if stock[["Open", "High", "Low", "Close", "Adj Close"]].le(0).any().any():
        raise ValueError("stock data contains non-positive prices")
    if stock["Volume"].le(0).any():
        raise ValueError("stock data contains non-positive volume")

    invalid_high = stock["High"] < stock[["Open", "Low", "Close"]].max(axis=1)
    invalid_low = stock["Low"] > stock[["Open", "High", "Close"]].min(axis=1)
    if invalid_high.any() or invalid_low.any():
        raise ValueError("stock data contains inconsistent OHLC bounds")

    stock = stock.sort_values("Date", kind="stable").reset_index(drop=True)
    if not stock["Date"].is_monotonic_increasing:
        raise AssertionError("stock dates are not chronological after sorting")
    integrity.update(
        {
            "rows_after_validation": int(len(stock)),
            "nonpositive_price_rows": 0,
            "invalid_high_rows": 0,
            "invalid_low_rows": 0,
            "nonpositive_volume_rows": 0,
            "date_min": stock["Date"].min().date().isoformat(),
            "date_max": stock["Date"].max().date().isoformat(),
        }
    )
    return stock, integrity


def build_stock_sequences(
    stock: pd.DataFrame,
    *,
    sequence_length: int = STOCK_SEQUENCE_LENGTH,
) -> dict[str, np.ndarray]:
    """Create previous-N-trading-day inputs and following-day Close targets."""

    if sequence_length <= 0:
        raise ValueError("sequence_length must be positive")
    missing = sorted({"Date", *STOCK_FEATURES} - set(stock.columns))
    if missing:
        raise ValueError(f"stock data is missing columns: {missing}")

    data = stock.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="raise")
    data = data.sort_values("Date", kind="stable").reset_index(drop=True)
    if data["Date"].duplicated().any():
        raise ValueError("stock dates must be unique")
    if len(data) <= sequence_length:
        raise ValueError("stock data is too short for the requested sequence length")

    values = data.loc[:, list(STOCK_FEATURES)].to_numpy(dtype=np.float32)
    windows = np.lib.stride_tricks.sliding_window_view(
        values, window_shape=sequence_length, axis=0
    )[:-1].transpose(0, 2, 1).copy()
    close_position = STOCK_FEATURES.index("Close")
    targets = values[sequence_length:, close_position].copy()
    target_dates = data["Date"].iloc[sequence_length:].to_numpy(dtype="datetime64[D]")
    naive_last_close = values[sequence_length - 1 : -1, close_position].copy()

    if not (len(windows) == len(targets) == len(target_dates) == len(naive_last_close)):
        raise AssertionError("stock windows and targets are misaligned")
    return {
        "X": windows,
        "y": targets,
        "target_date": target_dates,
        "naive_last_close": naive_last_close,
    }


def prepare_stock_data(
    raw_path: Path = RAW_STOCK_PATH,
    processed_dir: Path = PROCESSED_DIR,
    scaler_dir: Path = PREPROCESSING_MODEL_DIR,
) -> dict[str, Any]:
    """Run the complete stock preprocessing stage and save shared artifacts."""

    source = Path(raw_path)
    source_hash_before = sha256_file(source)
    if source_hash_before != EXPECTED_STOCK_SHA256:
        raise ValueError("locked stock CSV checksum does not match PROJECT_SPEC state")

    stock, integrity = load_stock_data(source)
    sequences = build_stock_sequences(stock, sequence_length=STOCK_SEQUENCE_LENGTH)
    del stock

    split_indices = chronological_split_indices(sequences["target_date"])
    split_payloads: dict[str, dict[str, np.ndarray]] = {}
    for split_name, indices in split_indices.items():
        order = np.argsort(sequences["target_date"][indices], kind="stable")
        ordered_indices = indices[order]
        split_payloads[split_name] = {
            key: value[ordered_indices] for key, value in sequences.items()
        }
    del sequences

    feature_scaler = fit_feature_scaler(split_payloads["train"]["X"])
    target_scaler = StandardScaler()
    target_scaler.fit(split_payloads["train"]["y"].reshape(-1, 1))

    feature_scaler_path = Path(scaler_dir) / "stock_feature_scaler.joblib"
    target_scaler_path = Path(scaler_dir) / "stock_target_scaler.joblib"
    save_joblib_atomic(feature_scaler_path, feature_scaler)
    save_joblib_atomic(target_scaler_path, target_scaler)

    artifact_paths: dict[str, Path] = {}
    for split_name in ("train", "val", "test"):
        payload = split_payloads[split_name]
        artifact_path = Path(processed_dir) / f"stock_{split_name}.npz"
        y_scaled = target_scaler.transform(payload["y"].reshape(-1, 1)).reshape(-1)
        save_npz_atomic(
            artifact_path,
            X=transform_sequences(feature_scaler, payload["X"]),
            y=payload["y"].astype(np.float32, copy=False),
            y_scaled=y_scaled.astype(np.float32, copy=False),
            target_date=payload["target_date"].astype("datetime64[D]", copy=False),
            naive_last_close=payload["naive_last_close"].astype(np.float32, copy=False),
        )
        artifact_paths[split_name] = artifact_path

    source_hash_after = sha256_file(source)
    if source_hash_after != source_hash_before:
        raise AssertionError("raw stock CSV changed during preprocessing")

    total_samples = sum(len(payload["y"]) for payload in split_payloads.values())
    split_metadata: dict[str, Any] = {}
    for split_name in ("train", "val", "test"):
        payload = split_payloads[split_name]
        split_metadata[split_name] = {
            "X_shape": [
                int(len(payload["y"])),
                STOCK_SEQUENCE_LENGTH,
                len(STOCK_FEATURES),
            ],
            "y_shape": [int(len(payload["y"]))],
            "target_date_min": iso_date(payload["target_date"].min()),
            "target_date_max": iso_date(payload["target_date"].max()),
            "sample_ratio": float(len(payload["y"]) / total_samples),
            "target_range_raw_close": {
                "min": float(payload["y"].min()),
                "max": float(payload["y"].max()),
            },
        }

    return {
        "raw_source": {
            "path": source.relative_to(PROJECT_ROOT).as_posix(),
            "sha256_before": source_hash_before,
            "sha256_after": source_hash_after,
        },
        "integrity": integrity,
        "feature_names": list(STOCK_FEATURES),
        "sequence_length": STOCK_SEQUENCE_LENGTH,
        "target_definition": "unadjusted Close of the immediately following trading day",
        "task": "regression",
        "split_strategy": {
            "basis": "target_date",
            "ratios_requested": dict(SPLIT_RATIOS),
            "boundary_rule": "nearest cumulative sample count without splitting a target_date",
            "context_rule": "validation/test inputs may use immediately preceding known history",
        },
        "splits": split_metadata,
        "feature_scaler": {
            "type": "sklearn.preprocessing.StandardScaler",
            "fit_scope": "flattened TRAIN X only",
            "n_samples_seen": int(feature_scaler.n_samples_seen_),
            "mean": feature_scaler.mean_.tolist(),
            "scale": feature_scaler.scale_.tolist(),
            **artifact_record(feature_scaler_path, PROJECT_ROOT),
        },
        "target_scaler": {
            "type": "sklearn.preprocessing.StandardScaler",
            "fit_scope": "TRAIN y only",
            "n_samples_seen": int(target_scaler.n_samples_seen_),
            "mean": target_scaler.mean_.tolist(),
            "scale": target_scaler.scale_.tolist(),
            **artifact_record(target_scaler_path, PROJECT_ROOT),
        },
        "artifacts": {
            name: artifact_record(path, PROJECT_ROOT) for name, path in artifact_paths.items()
        },
    }
