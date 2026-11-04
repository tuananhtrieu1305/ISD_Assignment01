"""Canonical Phase25 tensors. Apply frozen train statistics; never fit here.

Order is numeric input columns followed by categorical input columns/vocabulary.
The ordered names are persisted explicitly, independently of JSON object order.
"""

from __future__ import annotations

import copy

import numpy as np
import pandas as pd


class TensorAdapter:
    def __init__(self, state):
        self.state = copy.deepcopy(state)
        if "target_transform" in self.state and "name" not in self.state["target_transform"]:
            self.state["target_transform"]["name"] = "standardize"
        state = self.state
        names = state["input_columns"]
        numeric, categorical = state["numeric"], state["categorical"]
        if (
            state.get("fit_scope") != "train_only"
            or len(set(names)) != len(names)
            or set(numeric) & set(categorical)
            or set(names) != set(numeric) | set(categorical)
        ):
            raise ValueError("Invalid train-only feature schema")
        for rule in numeric.values():
            if not all(np.isfinite(rule[k]) for k in ("median", "mean", "std")) or rule["std"] <= 0:
                raise ValueError("Invalid frozen numeric statistics")
        for values in categorical.values():
            if not values or len(set(values)) != len(values) or not all(isinstance(v, str) for v in values):
                raise ValueError("Invalid category vocabulary")
        self.numeric_names = [n for n in names if n in numeric]
        self.categorical_names = [n for n in names if n in categorical]
        self.output_feature_names = self.numeric_names + [
            f"{name}={category}" for name in self.categorical_names for category in categorical[name]
        ]
        if (
            len(set(self.output_feature_names)) != len(self.output_feature_names)
            or len(self.output_feature_names) != state["output_width"]
        ):
            raise ValueError("Feature output width/name mismatch")
        labels = state.get("class_names", {})
        if labels and set(labels) != {str(i) for i in range(len(labels))}:
            raise ValueError("Class IDs must be contiguous from zero")
        self.class_names = [str(labels[str(i)]) for i in range(len(labels))]
        transform = state.get("target_transform", {"name": "identity"})
        if transform["name"] not in {"identity", "standardize"}:
            raise ValueError("Unsupported frozen target transform")
        if transform["name"] == "standardize" and (
            not np.isfinite([transform["mean"], transform["std"]]).all() or transform["std"] <= 0
        ):
            raise ValueError("Invalid target statistics")

    def to_dict(self):
        return {
            "adapter_version": "phase25.1",
            "state": copy.deepcopy(self.state),
            "output_feature_names": list(self.output_feature_names),
            "class_names": list(self.class_names),
        }

    @classmethod
    def from_dict(cls, document):
        adapter = cls(document["state"])
        if (
            document["adapter_version"] != "phase25.1"
            or document["output_feature_names"] != adapter.output_feature_names
            or document["class_names"] != adapter.class_names
        ):
            raise ValueError("Serialized adapter order/mapping mismatch")
        return adapter

    def transform(self, frame):
        if len(frame.columns) != len(set(frame.columns)) or set(frame.columns) != set(
            self.state["input_columns"]
        ):
            raise ValueError("Feature schema mismatch; IDs/targets must be excluded")
        columns = []
        for name in self.numeric_names:
            rule = self.state["numeric"][name]
            value = (
                pd.to_numeric(frame[name], errors="raise")
                .replace([np.inf, -np.inf], np.nan)
                .fillna(rule["median"])
            )
            columns.append(((value.to_numpy(dtype=float) - rule["mean"]) / rule["std"])[:, None])
        for name in self.categorical_names:
            value = frame[name].fillna("__missing__").astype(str).to_numpy()
            columns.append(value[:, None] == np.asarray(self.state["categorical"][name])[None, :])
        result = np.ascontiguousarray(np.concatenate(columns, axis=1), dtype=np.float32)
        if not np.isfinite(result).all():
            raise ValueError("Nonfinite input tensor")
        return result

    def target(self, values, *, inverse=False):
        result = np.asarray(values, dtype=np.float64)
        if not np.isfinite(result).all():
            raise ValueError("Missing/nonfinite labels must not be imputed")
        rule = self.state.get("target_transform", {"name": "identity"})
        if rule["name"] == "standardize":
            result = result * rule["std"] + rule["mean"] if inverse else (result - rule["mean"]) / rule["std"]
        return result if inverse else result.astype(np.float32)

    def inverse_target(self, values):
        return self.target(values, inverse=True)

    def encode_labels(self, values):
        mapping = {name: i for i, name in enumerate(self.class_names)}
        if not mapping or any(value not in mapping for value in values):
            raise ValueError("Unknown class label")
        return np.asarray([mapping[value] for value in values], dtype=np.int64)


def image_batch(images, implementation):
    images = np.asarray(images)
    if images.ndim != 4 or images.shape[-1] != 3 or images.dtype != np.uint8:
        raise ValueError("Images must be uint8 NHWC RGB; resize/decode through frozen source loader")
    if implementation not in {"scratch", "keras", "pytorch"}:
        raise ValueError("Unknown implementation")
    result = images.astype(np.float32) / 255
    if implementation == "pytorch":
        result = result.transpose(0, 3, 1, 2)
    return np.ascontiguousarray(result)


def select_rows(source_ids, selected_ids):
    if len(set(source_ids)) != len(source_ids) or len(set(selected_ids)) != len(selected_ids):
        raise ValueError("Duplicate IDs cannot be aligned")
    index = {value: i for i, value in enumerate(source_ids)}
    if any(value not in index for value in selected_ids):
        raise ValueError("Unknown selected ID")
    return [index[value] for value in selected_ids]


def window_batch(frame, windows, adapter):
    """Only materialize requested windows; source indices must match Phase24 cache."""
    features = adapter.state["input_columns"]
    x, y = [], []
    for row in windows:
        start, end = row["start_index"], row["origin_index"]
        targets = row["target_indices"]
        if start < 0 or end < start or not targets or min(targets) <= end or max(targets) >= len(frame):
            raise ValueError("Noncausal/out-of-range window")
        context = frame.iloc[start : end + 1]
        future = frame.iloc[targets]
        if not (context.series.eq(row["series"]).all() and future.series.eq(row["series"]).all()):
            raise ValueError("Window crosses series")
        x.append(adapter.transform(context[features]))
        y.append(adapter.target(future.target.to_numpy()))
    if not x:
        raise ValueError("Empty window batch")
    return np.stack(x), np.stack(y)
