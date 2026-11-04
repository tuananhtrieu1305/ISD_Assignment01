"""Validation rules for the measured Phase 21 environment reports."""

from __future__ import annotations

GIB = 1024**3
SHARED_PACKAGES = ("numpy", "pandas", "scipy", "scikit-learn", "joblib", "pillow", "keras", "h5py")


def assess_storage(available_bytes: int, minimum_gib: int = 20) -> dict:
    if available_bytes < 0 or minimum_gib < 0:
        raise ValueError("Storage values cannot be negative")
    required = minimum_gib * GIB
    return {
        "ready": available_bytes >= required,
        "available_bytes": available_bytes,
        "required_bytes": required,
    }


def validate_smoke(report: dict) -> list[str]:
    errors = []
    if report.get("status") != "PASS":
        errors.append("Worker did not complete successfully")
    if report.get("python_minor") != "3.11":
        errors.append("Python minor must be 3.11")
    expected = report.get("device")
    if expected not in {"gpu", "cpu"}:
        errors.append("Unknown requested device")
    checks = {check.get("name"): check for check in report.get("checks", [])}
    for name in ("matmul", "cnn", "rnn", "lstm"):
        check = checks.get(name, {})
        if not check.get("passed"):
            errors.append(f"Missing or failed real workload: {name}")
        actual = str(check.get("actual_device", "")).lower()
        on_gpu = "cuda" in actual or "gpu" in actual
        if expected == "gpu" and not on_gpu:
            errors.append(f"{name} did not execute on GPU")
        if expected == "cpu" and (on_gpu or "cpu" not in actual):
            errors.append(f"{name} did not execute on CPU")
        if name != "matmul" and not check.get("gradients_finite"):
            errors.append(f"{name} has missing or non-finite gradients")
    peak = report.get("peak_vram_bytes")
    if not isinstance(peak, int) or peak < 0 or peak >= 8 * GIB:
        errors.append("Missing VRAM measurement or VRAM budget exceeded")
    elif expected == "gpu" and peak == 0:
        errors.append("GPU workload must allocate measurable VRAM")
    return errors


def compare_shared_packages(left: dict, right: dict) -> list[str]:
    return [name for name, version in left.items() if right.get(name) != version]
