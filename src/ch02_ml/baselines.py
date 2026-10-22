"""Classical baselines exported as numeric data, never executable pickle."""

from __future__ import annotations

import numpy as np
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge

from src.common.numpy_engine import sigmoid


def fit_baseline(name, x, y, task, *, seed, settings=None, class_weights=None):
    settings = settings or {"n_estimators": 200, "max_depth": 12, "min_samples_leaf": 5, "n_jobs": 2}
    if task not in {"mse", "binary"}:
        raise ValueError("Unknown task")
    if name == "majority" and task == "binary":
        model = DummyClassifier(strategy="most_frequent")
    elif name == "median" and task == "mse":
        model = DummyRegressor(strategy="median")
    elif name == "logistic_regression" and task == "binary":
        model = LogisticRegression(
            C=1.0,
            max_iter=1000,
            solver="lbfgs",
            class_weight={int(k): v for k, v in class_weights.items()} if class_weights else None,
            random_state=seed,
        )
    elif name == "ridge" and task == "mse":
        model = Ridge(alpha=1.0)
    elif name == "random_forest":
        options = {**settings, "random_state": seed}
        if task == "binary":
            options["class_weight"] = {int(k): v for k, v in class_weights.items()} if class_weights else None
        model = (RandomForestClassifier if task == "binary" else RandomForestRegressor)(**options)
    else:
        raise ValueError("Unsupported baseline/task")
    model.fit(x, np.asarray(y).reshape(-1))
    metadata = {"format": "phase26_data_only.1", "name": name, "task": task, "input_width": x.shape[1]}
    arrays = {}
    if name in {"majority", "median"}:
        arrays["constant"] = np.asarray(
            [model.classes_[np.argmax(model.class_prior_)]]
            if task == "binary"
            else model.constant_.reshape(-1)
        )
    elif name in {"logistic_regression", "ridge"}:
        arrays["coef"] = np.asarray(model.coef_).reshape(1, -1)
        arrays["intercept"] = np.asarray(model.intercept_).reshape(1)
    else:
        metadata["tree_count"] = len(model.estimators_)
        for i, estimator in enumerate(model.estimators_):
            tree = estimator.tree_
            for field in ("children_left", "children_right", "feature", "threshold", "value"):
                arrays[f"tree_{i:03d}/{field}"] = np.asarray(getattr(tree, field)).copy()
    return model, PortableBaseline(metadata, arrays)


class PortableBaseline:
    def __init__(self, metadata, arrays):
        self.metadata = dict(metadata)
        self.arrays = {k: np.asarray(v) for k, v in arrays.items()}
        if metadata["format"] != "phase26_data_only.1":
            raise ValueError("Unknown baseline checkpoint format")

    def predict(self, x):
        x = np.asarray(x, dtype=np.float32)
        if x.ndim != 2 or x.shape[1] != self.metadata["input_width"] or not np.isfinite(x).all():
            raise ValueError("Invalid baseline features")
        name = self.metadata["name"]
        classification = self.metadata["task"] == "binary"
        if name in {"majority", "median"}:
            value = self.arrays["constant"][0]
            return np.tile([1 - value, value], (len(x), 1)) if classification else np.full((len(x), 1), value)
        if name in {"logistic_regression", "ridge"}:
            value = x @ self.arrays["coef"].T + self.arrays["intercept"]
            if classification:
                p = sigmoid(value.reshape(-1))
                return np.column_stack([1 - p, p])
            return value
        result = np.zeros((len(x), 2 if classification else 1), dtype=float)
        for i in range(self.metadata["tree_count"]):
            prefix = f"tree_{i:03d}/"
            left = self.arrays[prefix + "children_left"]
            right = self.arrays[prefix + "children_right"]
            feature = self.arrays[prefix + "feature"]
            threshold = self.arrays[prefix + "threshold"]
            values = self.arrays[prefix + "value"]
            nodes = np.zeros(len(x), dtype=int)
            active = left[nodes] >= 0
            while active.any():
                rows = np.flatnonzero(active)
                current = nodes[rows]
                nodes[rows] = np.where(
                    x[rows, feature[current]] <= threshold[current], left[current], right[current]
                )
                active = left[nodes] >= 0
            leaf = values[nodes, 0]
            if classification:
                leaf = leaf / leaf.sum(axis=1, keepdims=True)
            result += leaf
        return result / self.metadata["tree_count"]
