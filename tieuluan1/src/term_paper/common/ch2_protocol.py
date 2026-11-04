"""Protocol checks shared by Chapter 2 data and experiment scripts."""

import hashlib
import json

import numpy as np


SPLIT_ORDER = ("train", "val", "test")


def validate_split_keys(split_keys, expected_total=None):
    missing = [name for name in SPLIT_ORDER if name not in split_keys]
    if missing:
        raise ValueError(f"Missing split keys: {missing}")
    normalized = {
        name: np.asarray(split_keys[name]).astype(str).reshape(-1) for name in SPLIT_ORDER
    }
    for name, values in normalized.items():
        if len(values) != len(set(values.tolist())):
            raise ValueError(f"Duplicate sample key inside {name}")
    seen = set()
    for name in SPLIT_ORDER:
        current = set(normalized[name].tolist())
        overlap = seen.intersection(current)
        if overlap:
            raise ValueError(f"Split overlap found in {name}: {sorted(overlap)[:3]}")
        seen.update(current)
    if expected_total is not None and len(seen) != int(expected_total):
        raise ValueError(f"Expected {expected_total} unique keys, found {len(seen)}")
    return normalized


def split_key_digest(split_keys):
    normalized = validate_split_keys(split_keys)
    payload = {
        name: normalized[name].tolist()
        for name in SPLIT_ORDER
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

