"""Load read-only A06 arrays and construct the fixed Chapter 4 benchmark."""

from pathlib import Path

import joblib
import numpy as np
from sklearn.model_selection import train_test_split

from term_paper.src.common.ch4_protocol import (
    split_digest,
    validate_split_keys,
    validate_temporal_splits,
)


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
A06_ROOT = WORKSPACE_ROOT / "A06"
PROCESSED_ROOT = A06_ROOT / "datasets" / "processed"


def stratified_subset(labels, size, seed):
    labels = np.asarray(labels, dtype=int).reshape(-1)
    if int(size) <= 0 or int(size) > len(labels):
        raise ValueError("subset size must be within source split")
    if int(size) == len(labels):
        return np.arange(len(labels), dtype=int)
    selected, _ = train_test_split(
        np.arange(len(labels)), train_size=int(size), random_state=int(seed), stratify=labels
    )
    return np.asarray(sorted(selected), dtype=int)


def class_weights(labels):
    labels = np.asarray(labels, dtype=int).reshape(-1)
    classes, counts = np.unique(labels, return_counts=True)
    total = len(labels)
    return {int(label): float(total / (len(classes) * count)) for label, count in zip(classes, counts)}


def _customer_key(customer_id, target_week):
    return np.asarray([
        f"customer-{int(customer)}__week-{np.datetime_as_string(week, unit='D')}"
        for customer, week in zip(customer_id, target_week)
    ])


def prepare_customer_benchmark(subset_sizes, seed=42):
    result = {}
    keys, dates = {}, {}
    for offset, split in enumerate(("train", "val", "test")):
        source = np.load(PROCESSED_ROOT / f"customer_{split}.npz", allow_pickle=False)
        chosen = stratified_subset(source["y"], int(subset_sizes[split]), int(seed) + offset)
        result[f"x_{split}"] = source["X"][chosen].astype(np.float32)
        result[f"y_{split}"] = source["y"][chosen].astype(np.float32)
        dates[split] = source["target_week"][chosen].astype("datetime64[D]")
        keys[split] = _customer_key(source["customer_id"][chosen], dates[split])
    validate_temporal_splits(dates)
    validate_split_keys(keys)
    result.update({
        "dataset_id": "ch4_online_retail_customer_week",
        "task": "binary", "input_size": 5, "sequence_length": 8,
        "keys": keys, "dates": dates,
        "class_weight": class_weights(result["y_train"]),
        "preprocessor_path": A06_ROOT / "models" / "preprocessing" / "customer_feature_scaler.joblib",
        "split_sha256": split_digest(keys),
        "source": "A06/datasets/processed/customer_{train,val,test}.npz",
    })
    return result


def prepare_stock_benchmark():
    result = {}
    keys, dates = {}, {}
    for split in ("train", "val", "test"):
        source = np.load(PROCESSED_ROOT / f"stock_{split}.npz", allow_pickle=False)
        result[f"x_{split}"] = source["X"].astype(np.float32)
        result[f"y_{split}"] = source["y_scaled"].astype(np.float32)
        result[f"y_{split}_real"] = source["y"].astype(np.float32)
        result[f"naive_{split}"] = source["naive_last_close"].astype(np.float32)
        dates[split] = source["target_date"].astype("datetime64[D]")
        keys[split] = np.asarray([np.datetime_as_string(value, unit="D") for value in dates[split]])
    validate_temporal_splits(dates)
    validate_split_keys(keys)
    scaler_path = A06_ROOT / "models" / "preprocessing" / "stock_target_scaler.joblib"
    result.update({
        "dataset_id": "ch4_aapl_next_close", "task": "regression",
        "input_size": 5, "sequence_length": 30, "keys": keys, "dates": dates,
        "class_weight": None,
        "preprocessor_path": scaler_path,
        "feature_scaler_path": A06_ROOT / "models" / "preprocessing" / "stock_feature_scaler.joblib",
        "target_scaler": joblib.load(scaler_path),
        "split_sha256": split_digest(keys),
        "source": "A06/datasets/processed/stock_{train,val,test}.npz",
    })
    return result
