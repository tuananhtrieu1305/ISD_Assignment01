"""Behavioral and integration tests for the shared preprocessing pipeline."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

import src.customer_pipeline as customer_module
import src.run_preprocessing as runner_module
import src.stock_pipeline as stock_module
from src.config import (
    CUSTOMER_FEATURES,
    CUSTOMER_SEQUENCE_LENGTH,
    EXPECTED_CUSTOMER_SHA256,
    EXPECTED_STOCK_SHA256,
    PREPROCESSING_METADATA_PATH,
    PROCESSED_DIR,
    RAW_CUSTOMER_PATH,
    RAW_STOCK_PATH,
    STOCK_FEATURES,
    STOCK_SEQUENCE_LENGTH,
)
from src.customer_pipeline import (
    aggregate_customer_weeks,
    build_customer_sequences,
    clean_customer_transactions,
)
from src.preprocessing_utils import (
    chronological_split_indices,
    fit_feature_scaler,
    sha256_file,
    transform_sequences,
)
from src.reproducibility import set_global_seed
from src.stock_pipeline import build_stock_sequences


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPLIT_NAMES = ("train", "val", "test")


def _weekly_rows() -> pd.DataFrame:
    start = pd.Timestamp("2020-01-06")
    active_offsets = [0, 2, 3, 7, 9]
    rows = []
    for offset in active_offsets:
        rows.append(
            {
                "CustomerID": 101,
                "WeekStart": start + pd.Timedelta(weeks=offset),
                "total_spent": float(10 + offset),
                "total_quantity": float(1 + offset),
                "order_count": 1.0,
                "unique_products": 1.0,
                "active_flag": 1.0,
            }
        )
    return pd.DataFrame(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_customer_cleaning_and_weekly_order_definition() -> None:
    raw = pd.DataFrame(
        [
            ["100", "A", "item", 2, "2020-01-06", 3.0, 1.0, "UK"],
            ["100", "B", "item", 1, "2020-01-06", 4.0, 1.0, "UK"],
            ["100", "B", "item", 1, "2020-01-06", 4.0, 1.0, "UK"],
            ["C101", "A", "return", -1, "2020-01-07", 3.0, 1.0, "UK"],
            ["102", "C", "free", 1, "2020-01-08", 0.0, 1.0, "UK"],
            ["103", "D", "unknown", 1, "2020-01-09", 2.0, None, "UK"],
        ],
        columns=[
            "Invoice",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "Price",
            "Customer ID",
            "Country",
        ],
    )

    clean, counts = clean_customer_transactions(raw)
    weekly = aggregate_customer_weeks(clean)

    assert counts["raw_rows"] == 6
    assert counts["exact_duplicates_removed"] == 1
    assert len(clean) == 2
    assert clean["Revenue"].sum() == 10.0
    assert weekly.loc[0, "order_count"] == 1
    assert weekly.loc[0, "unique_products"] == 2
    assert weekly.loc[0, "active_flag"] == 1


def test_customer_target_is_next_week_and_customer_id_is_metadata() -> None:
    weekly = _weekly_rows()
    start = weekly["WeekStart"].min()
    result = build_customer_sequences(
        weekly,
        sequence_length=3,
        first_full_week=start,
        last_full_week=start + pd.Timedelta(weeks=9),
    )

    assert result["X"].shape == (7, 3, 5)
    np.testing.assert_array_equal(result["X"][0, :, 4], [1.0, 0.0, 1.0])
    assert result["target_week"][0] == np.datetime64("2020-01-27")
    assert result["y"][0] == 1
    assert result["customer_id"][0] == 101
    assert "CustomerID" not in CUSTOMER_FEATURES


def test_stock_target_is_following_trading_day() -> None:
    dates = pd.bdate_range("2024-01-02", periods=35)
    stock = pd.DataFrame(
        {
            "Date": dates,
            "Open": np.arange(35, dtype=float) + 10,
            "High": np.arange(35, dtype=float) + 11,
            "Low": np.arange(35, dtype=float) + 9,
            "Close": np.arange(35, dtype=float) + 10.5,
            "Volume": np.arange(35, dtype=float) + 1_000,
        }
    )

    result = build_stock_sequences(stock, sequence_length=30)

    assert result["X"].shape == (5, 30, 5)
    np.testing.assert_array_equal(result["X"][0, :, 3], stock["Close"].iloc[:30])
    assert result["y"][0] == stock["Close"].iloc[30]
    assert result["target_date"][0] == dates[30].to_datetime64()
    assert result["naive_last_close"][0] == stock["Close"].iloc[29]


def test_chronological_split_keeps_timestamp_groups_disjoint() -> None:
    timestamps = np.repeat(pd.date_range("2023-01-02", periods=20, freq="W-MON"), 7)
    split = chronological_split_indices(timestamps)
    train_times = timestamps[split["train"]]
    val_times = timestamps[split["val"]]
    test_times = timestamps[split["test"]]

    assert train_times.max() < val_times.min()
    assert val_times.max() < test_times.min()
    assert set(train_times).isdisjoint(set(val_times))
    assert set(val_times).isdisjoint(set(test_times))
    actual = np.array([len(split[name]) for name in SPLIT_NAMES]) / len(timestamps)
    np.testing.assert_allclose(actual, [0.70, 0.15, 0.15], atol=0.06)


def test_feature_scaler_uses_train_tensor_only() -> None:
    train = np.arange(2 * 3 * 2, dtype=np.float64).reshape(2, 3, 2)
    validation = np.full((1, 3, 2), 10_000.0)

    scaler = fit_feature_scaler(train)
    transformed_train = transform_sequences(scaler, train)
    transformed_validation = transform_sequences(scaler, validation)

    np.testing.assert_allclose(scaler.mean_, train.reshape(-1, 2).mean(axis=0))
    assert not np.allclose(scaler.mean_, np.vstack([train.reshape(-1, 2), validation.reshape(-1, 2)]).mean(axis=0))
    np.testing.assert_allclose(transformed_train.reshape(-1, 2).mean(axis=0), 0.0, atol=1e-6)
    assert transformed_validation.mean() > 100


def test_sequence_generation_is_deterministic() -> None:
    weekly = _weekly_rows()
    start = weekly["WeekStart"].min()
    kwargs = {
        "sequence_length": 3,
        "first_full_week": start,
        "last_full_week": start + pd.Timedelta(weeks=9),
    }

    first = build_customer_sequences(weekly, **kwargs)
    second = build_customer_sequences(weekly.sample(frac=1, random_state=42), **kwargs)

    for key in ("X", "y", "customer_id", "target_week"):
        np.testing.assert_array_equal(first[key], second[key])


def test_global_seed_repeats_python_and_numpy_streams() -> None:
    set_global_seed(42)
    first = (random.random(), np.random.random(4))
    set_global_seed(42)
    second = (random.random(), np.random.random(4))

    assert first[0] == second[0]
    np.testing.assert_array_equal(first[1], second[1])


def test_customer_preparation_runs_end_to_end_on_small_fixture(
    tmp_path: Path,
    monkeypatch,
) -> None:
    weeks = pd.date_range("2020-01-06", periods=24, freq="W-MON")
    rows = []
    for customer_id, active_offsets in (
        (101, range(0, 24, 2)),
        (202, [0, *range(1, 23, 2), 23]),
    ):
        for offset in active_offsets:
            rows.append(
                [
                    f"{customer_id}-{offset}",
                    f"SKU-{offset % 3}",
                    "fixture item",
                    1 + offset % 2,
                    weeks[offset] + pd.Timedelta(hours=10),
                    2.5,
                    float(customer_id),
                    "UK",
                ]
            )
    raw = pd.DataFrame(
        rows,
        columns=[
            "Invoice",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "Price",
            "Customer ID",
            "Country",
        ],
    )
    fixture_root = tmp_path / "project"
    raw_path = fixture_root / "datasets" / "customer" / "fixture.xlsx"
    processed_dir = fixture_root / "datasets" / "processed"
    scaler_dir = fixture_root / "models" / "preprocessing"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_bytes(b"read-only fixture placeholder")

    real_sha = sha256_file

    def fixture_sha(path: Path) -> str:
        if Path(path) == raw_path:
            return EXPECTED_CUSTOMER_SHA256
        return real_sha(Path(path))

    monkeypatch.setattr(customer_module, "PROJECT_ROOT", fixture_root)
    monkeypatch.setattr(customer_module, "sha256_file", fixture_sha)
    monkeypatch.setattr(
        customer_module,
        "load_customer_workbook",
        lambda path: (raw.copy(), {"sheet_names": ["fixture"], "sheets": []}),
    )

    metadata = customer_module.prepare_customer_data(
        raw_path=raw_path,
        processed_dir=processed_dir,
        scaler_dir=scaler_dir,
    )

    assert metadata["cleaning_counts"]["cleaned_rows"] == len(raw)
    assert metadata["class_weight"]["fit_scope"] == "TRAIN y only"
    for split_name in SPLIT_NAMES:
        with np.load(processed_dir / f"customer_{split_name}.npz") as artifact:
            assert artifact["X"].shape[1:] == (8, 5)


def test_stock_preparation_runs_end_to_end_on_small_fixture(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fixture_root = tmp_path / "project"
    raw_path = fixture_root / "datasets" / "stock" / "fixture.csv"
    processed_dir = fixture_root / "datasets" / "processed"
    scaler_dir = fixture_root / "models" / "preprocessing"
    raw_path.parent.mkdir(parents=True)
    dates = pd.bdate_range("2020-01-02", periods=100)
    base = np.arange(100, dtype=float) + 50
    pd.DataFrame(
        {
            "Date": dates,
            "Open": base,
            "High": base + 2,
            "Low": base - 2,
            "Close": base + 0.5,
            "Adj Close": base + 0.25,
            "Volume": np.arange(100) + 1_000,
        }
    ).to_csv(raw_path, index=False)

    real_sha = sha256_file

    def fixture_sha(path: Path) -> str:
        if Path(path) == raw_path:
            return EXPECTED_STOCK_SHA256
        return real_sha(Path(path))

    monkeypatch.setattr(stock_module, "PROJECT_ROOT", fixture_root)
    monkeypatch.setattr(stock_module, "sha256_file", fixture_sha)

    metadata = stock_module.prepare_stock_data(
        raw_path=raw_path,
        processed_dir=processed_dir,
        scaler_dir=scaler_dir,
    )

    assert metadata["integrity"]["raw_rows"] == 100
    assert metadata["target_scaler"]["fit_scope"] == "TRAIN y only"
    for split_name in SPLIT_NAMES:
        with np.load(processed_dir / f"stock_{split_name}.npz") as artifact:
            assert artifact["X"].shape[1:] == (30, 5)
            assert len(artifact["y_scaled"]) == len(artifact["y"])


def test_runner_writes_one_combined_metadata_file(tmp_path: Path, monkeypatch) -> None:
    fixture_root = tmp_path / "project"
    customer_path = fixture_root / "datasets" / "customer" / "raw.xlsx"
    stock_path = fixture_root / "datasets" / "stock" / "raw.csv"
    metadata_path = fixture_root / "results" / "metrics" / "preprocessing.json"
    customer_path.parent.mkdir(parents=True)
    stock_path.parent.mkdir(parents=True)

    monkeypatch.setattr(runner_module, "PROJECT_ROOT", fixture_root)
    monkeypatch.setattr(runner_module, "RAW_CUSTOMER_PATH", customer_path)
    monkeypatch.setattr(runner_module, "RAW_STOCK_PATH", stock_path)
    monkeypatch.setattr(runner_module, "PREPROCESSING_METADATA_PATH", metadata_path)
    monkeypatch.setattr(runner_module, "ensure_output_directories", lambda: None)
    monkeypatch.setattr(runner_module, "prepare_customer_data", lambda: {"task": "customer"})
    monkeypatch.setattr(runner_module, "prepare_stock_data", lambda: {"task": "stock"})

    metadata = runner_module.run_all_preprocessing()
    saved = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert metadata["generator"] == "src.run_preprocessing"
    assert saved["seed"] == 42
    assert saved["customer"]["task"] == "customer"
    assert saved["stock"]["task"] == "stock"


def test_locked_raw_files_remain_unchanged() -> None:
    assert sha256_file(RAW_CUSTOMER_PATH) == EXPECTED_CUSTOMER_SHA256
    assert sha256_file(RAW_STOCK_PATH) == EXPECTED_STOCK_SHA256
    assert _sha256(RAW_CUSTOMER_PATH) == EXPECTED_CUSTOMER_SHA256
    assert _sha256(RAW_STOCK_PATH) == EXPECTED_STOCK_SHA256


def test_saved_artifacts_are_loadable_and_match_contract() -> None:
    expected = {
        "customer": (CUSTOMER_SEQUENCE_LENGTH, len(CUSTOMER_FEATURES)),
        "stock": (STOCK_SEQUENCE_LENGTH, len(STOCK_FEATURES)),
    }
    for task, (sequence_length, feature_count) in expected.items():
        for split_name in SPLIT_NAMES:
            path = PROCESSED_DIR / f"{task}_{split_name}.npz"
            assert path.is_file()
            with np.load(path, allow_pickle=False) as artifact:
                assert artifact["X"].ndim == 3
                assert artifact["X"].shape[1:] == (sequence_length, feature_count)
                assert len(artifact["X"]) == len(artifact["y"])
                if task == "customer":
                    assert len(artifact["customer_id"]) == len(artifact["y"])
                    assert len(artifact["target_week"]) == len(artifact["y"])
                else:
                    assert len(artifact["target_date"]) == len(artifact["y"])
                    assert len(artifact["y_scaled"]) == len(artifact["y"])


def test_saved_splits_are_strictly_chronological_without_overlap() -> None:
    for task, timestamp_key in (("customer", "target_week"), ("stock", "target_date")):
        timestamps = {}
        for split_name in SPLIT_NAMES:
            with np.load(PROCESSED_DIR / f"{task}_{split_name}.npz", allow_pickle=False) as artifact:
                timestamps[split_name] = artifact[timestamp_key].copy()

        assert timestamps["train"].max() < timestamps["val"].min()
        assert timestamps["val"].max() < timestamps["test"].min()
        assert set(timestamps["train"]).isdisjoint(set(timestamps["val"]))
        assert set(timestamps["val"]).isdisjoint(set(timestamps["test"]))


def test_saved_scalers_match_train_scope_and_metadata() -> None:
    metadata = json.loads(PREPROCESSING_METADATA_PATH.read_text(encoding="utf-8"))
    scaler_dir = PROJECT_ROOT / "models" / "preprocessing"

    for task, sequence_length in (("customer", 8), ("stock", 30)):
        with np.load(PROCESSED_DIR / f"{task}_train.npz", allow_pickle=False) as artifact:
            train_x = artifact["X"]
            np.testing.assert_allclose(
                train_x.reshape(-1, train_x.shape[-1]).mean(axis=0, dtype=np.float64),
                0.0,
                atol=1e-6,
            )
            expected_seen = len(train_x) * sequence_length

        scaler = joblib.load(scaler_dir / f"{task}_feature_scaler.joblib")
        assert int(scaler.n_samples_seen_) == expected_seen
        assert metadata[task]["feature_scaler"]["fit_scope"] == "flattened TRAIN X only"
        assert metadata[task]["feature_scaler"]["n_samples_seen"] == expected_seen

    stock_target_scaler = joblib.load(scaler_dir / "stock_target_scaler.joblib")
    with np.load(PROCESSED_DIR / "stock_train.npz", allow_pickle=False) as artifact:
        np.testing.assert_allclose(artifact["y_scaled"].mean(), 0.0, atol=1e-6)
        assert int(stock_target_scaler.n_samples_seen_) == len(artifact["y"])


def test_metadata_describes_artifacts_and_train_only_class_statistics() -> None:
    metadata = json.loads(PREPROCESSING_METADATA_PATH.read_text(encoding="utf-8"))

    assert metadata["seed"] == 42
    assert metadata["customer"]["feature_names"] == list(CUSTOMER_FEATURES)
    assert metadata["stock"]["feature_names"] == list(STOCK_FEATURES)
    assert metadata["customer"]["class_weight"]["fit_scope"] == "TRAIN y only"
    assert metadata["stock"]["target_scaler"]["fit_scope"] == "TRAIN y only"
    for task in ("customer", "stock"):
        for split_name in SPLIT_NAMES:
            artifact_info = metadata[task]["artifacts"][split_name]
            artifact_path = PROJECT_ROOT / artifact_info["path"]
            assert artifact_path.is_file()
            assert sha256_file(artifact_path) == artifact_info["sha256"]
