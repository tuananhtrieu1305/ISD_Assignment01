"""Split identity and leakage checks for Chapter 3."""

import hashlib


def validate_split_keys(split_keys):
    required = {"train", "val", "test"}
    if set(split_keys) != required:
        raise ValueError(f"split keys must be exactly {sorted(required)}")
    normalized = {name: [str(value) for value in values] for name, values in split_keys.items()}
    for name, values in normalized.items():
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate keys within {name}")
    for left, right in (("train", "val"), ("train", "test"), ("val", "test")):
        if set(normalized[left]).intersection(normalized[right]):
            raise ValueError(f"split overlap between {left} and {right}")


def split_digest(split_keys):
    validate_split_keys(split_keys)
    digest = hashlib.sha256()
    for split in ("train", "val", "test"):
        digest.update(f"[{split}]\n".encode("utf-8"))
        for key in split_keys[split]:
            digest.update(f"{key}\n".encode("utf-8"))
    return digest.hexdigest()
