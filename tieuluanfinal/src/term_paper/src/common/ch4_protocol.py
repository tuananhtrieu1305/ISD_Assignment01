"""Split validation and stable identifiers for the Chapter 4 benchmark."""

import hashlib

import numpy as np


SPLITS = ("train", "val", "test")


def split_digest(keys):
    digest = hashlib.sha256()
    for split in SPLITS:
        digest.update(split.encode("utf-8"))
        for key in np.asarray(keys[split]).astype(str):
            digest.update(key.encode("utf-8"))
            digest.update(b"\0")
    return digest.hexdigest()


def validate_temporal_splits(dates):
    for split in SPLITS:
        values = np.asarray(dates[split]).astype("datetime64[D]")
        if len(values) == 0 or np.any(values[1:] < values[:-1]):
            raise ValueError(f"{split} dates must be non-empty and sorted")
    if np.max(dates["train"]) >= np.min(dates["val"]):
        raise ValueError("train and validation periods overlap")
    if np.max(dates["val"]) >= np.min(dates["test"]):
        raise ValueError("validation and test periods overlap")


def validate_split_keys(keys):
    sets = {split: set(np.asarray(keys[split]).astype(str)) for split in SPLITS}
    if any(len(sets[split]) != len(keys[split]) for split in SPLITS):
        raise ValueError("sample keys must be unique within each split")
    if sets["train"] & sets["val"] or sets["train"] & sets["test"] or sets["val"] & sets["test"]:
        raise ValueError("sample keys overlap across splits")
