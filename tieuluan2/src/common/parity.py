"""Declared per-tensor symmetric relative L2 gradient error (locked limit 1e-3)."""

import numpy as np


def gradient_parity(reference, actual, tolerance=1e-3):
    if not reference or set(reference) != set(actual) or tolerance <= 0:
        raise ValueError("Gradient keys/tolerance mismatch")
    results = {}
    maximum = 0.0
    for name, value in reference.items():
        other = actual[name]
        if value.shape != other.shape or not np.isfinite(value).all() or not np.isfinite(other).all():
            raise ValueError("Gradient shape/value mismatch")
        left = value.astype(np.float64).ravel()
        right = other.astype(np.float64).ravel()
        error = float(np.linalg.norm(left - right) / max(np.linalg.norm(left) + np.linalg.norm(right), 1e-12))
        results[name] = error
        maximum = max(maximum, float(np.max(np.abs(left - right))))
        if error > tolerance:
            raise ValueError(f"Gradient relative L2 error {name}: {error} > {tolerance}")
    return {
        "definition": "norm(g_ref-g_actual)/(norm(g_ref)+norm(g_actual)), denominator floor 1e-12; per tensor",
        "tolerance": tolerance,
        "max_relative_l2_error": max(results.values()),
        "per_tensor_relative_l2_error": results,
        "max_abs_error": maximum,
    }
