"""Auditor-only regression; no training or TEST model forwards."""

import numpy as np

from scripts.verify_phase26_roundtrip_v1 import recompute_typed
from src.ch02_ml.diagnostics import calibration


def test_ece_restores_float32_probability_dtype_without_relaxing_tolerance():
    y = np.array([0.0, 1.0, 0.0, 1.0])
    p = np.array([0.12345678, 0.81234567, 0.33333334, 0.9876543], dtype="float32")
    rows = [{"target": float(a), "prediction": [float(1 - b), float(b)]} for a, b in zip(y, p, strict=True)]
    expected = calibration(y, p)
    actual = {row["name"]: row["value"] for row in recompute_typed(rows, "binary", "float32")}
    assert actual["ece"] == expected["ece"]
    assert actual["brier"] == expected["brier"]


def test_float64_baseline_preserves_float64_calibration():
    y = np.array([0.0, 1.0])
    p = np.array([0.123456789012, 0.812345678901])
    rows = [{"target": float(a), "prediction": [float(1 - b), float(b)]} for a, b in zip(y, p, strict=True)]
    actual = {row["name"]: row["value"] for row in recompute_typed(rows, "binary", "float64")}
    assert actual["ece"] == calibration(y, p)["ece"]
