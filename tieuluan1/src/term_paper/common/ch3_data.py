"""Reconstruct fixed Chapter 3 benchmark subsets from read-only A05 splits."""

from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from term_paper.src.common.ch3_protocol import split_digest, validate_split_keys


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
A05_ROOT = WORKSPACE_ROOT / "A05"


def stratified_subset(keys, labels, size, seed):
    keys = np.asarray(keys)
    labels = np.asarray(labels, dtype=int)
    if len(keys) != len(labels):
        raise ValueError("keys and labels must have equal length")
    if int(size) > len(keys) or int(size) <= 0:
        raise ValueError("subset size must be within the source split")
    if int(size) == len(keys):
        return np.arange(len(keys), dtype=int)
    selected, _ = train_test_split(
        np.arange(len(keys)),
        train_size=int(size),
        random_state=int(seed),
        stratify=labels,
    )
    return np.asarray(sorted(selected), dtype=int)


def class_weights(labels):
    labels = np.asarray(labels, dtype=int).reshape(-1)
    classes, counts = np.unique(labels, return_counts=True)
    total = len(labels)
    return {
        int(label): float(total / (len(classes) * count))
        for label, count in zip(classes, counts)
    }


def _load_eurosat_images(relative_paths):
    images = []
    for relative in relative_paths:
        # Path accepts forward slashes on Windows; rebuilding from parts keeps this portable.
        path = A05_ROOT.joinpath(*Path(str(relative)).parts)
        with Image.open(path) as image:
            array = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
        if array.shape != (64, 64, 3):
            raise ValueError(f"unexpected EuroSAT shape {array.shape}: {path}")
        images.append(array)
    return np.asarray(images, dtype=np.float32)


def prepare_eurosat_benchmark(subset_sizes, seed=42):
    arrays = {}
    keys = {}
    labels = {}
    class_names = None
    for offset, split in enumerate(("train", "val", "test")):
        frame = pd.read_csv(A05_ROOT / "results" / "splits" / f"eurosat_{split}.csv")
        chosen = stratified_subset(
            frame["relative_path"].to_numpy(),
            frame["label"].to_numpy(),
            int(subset_sizes[split]),
            int(seed) + offset,
        )
        subset = frame.iloc[chosen].reset_index(drop=True)
        keys[split] = subset["relative_path"].astype(str).to_numpy()
        labels[split] = subset["label"].to_numpy(dtype=np.int64)
        arrays[split] = _load_eurosat_images(keys[split])
        if class_names is None:
            class_names = (
                frame[["label", "class_name"]]
                .drop_duplicates()
                .sort_values("label")["class_name"]
                .astype(str)
                .tolist()
            )
    validate_split_keys(keys)
    return {
        "dataset_id": "ch3_eurosat",
        "mode": "2d",
        "input_shape": (64, 64, 3),
        "num_classes": 10,
        "class_names": class_names,
        "x_train": arrays["train"],
        "x_val": arrays["val"],
        "x_test": arrays["test"],
        "y_train": labels["train"],
        "y_val": labels["val"],
        "y_test": labels["test"],
        "keys": keys,
        "class_weight": None,
        "preprocessor": {"scale": "divide_by_255", "fit_scope": "none"},
        "split_sha256": split_digest(keys),
    }


def prepare_diabetes_benchmark(subset_sizes, seed=42):
    raw = pd.read_csv(
        A05_ROOT / "datasets" / "diabetes" / "diabetes_012_health_indicators_BRFSS2015.csv"
    )
    target = "Diabetes_012"
    feature_names = [column for column in raw.columns if column != target]
    selected_rows = {}
    keys = {}
    labels = {}
    for offset, split in enumerate(("train", "val", "test")):
        frame = pd.read_csv(A05_ROOT / "results" / "splits" / f"diabetes_{split}.csv")
        chosen = stratified_subset(
            frame["row_index"].to_numpy(),
            frame[target].to_numpy(dtype=int),
            int(subset_sizes[split]),
            int(seed) + offset,
        )
        subset = frame.iloc[chosen].reset_index(drop=True)
        row_indices = subset["row_index"].to_numpy(dtype=int)
        selected_rows[split] = raw.iloc[row_indices][feature_names].to_numpy(dtype=np.float32)
        keys[split] = np.asarray([f"row-{value}" for value in row_indices])
        labels[split] = subset[target].to_numpy(dtype=np.int64)
    validate_split_keys(keys)
    scaler = StandardScaler().fit(selected_rows["train"])
    arrays = {
        split: scaler.transform(selected_rows[split]).astype(np.float32)[..., None]
        for split in ("train", "val", "test")
    }
    return {
        "dataset_id": "ch3_diabetes_012",
        "mode": "1d",
        "input_shape": (len(feature_names), 1),
        "num_classes": 3,
        "class_names": ["No diabetes", "Prediabetes", "Diabetes"],
        "feature_names": feature_names,
        "x_train": arrays["train"],
        "x_val": arrays["val"],
        "x_test": arrays["test"],
        "y_train": labels["train"],
        "y_val": labels["val"],
        "y_test": labels["test"],
        "keys": keys,
        "class_weight": class_weights(labels["train"]),
        "preprocessor": scaler,
        "split_sha256": split_digest(keys),
    }
