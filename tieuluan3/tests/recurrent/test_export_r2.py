"""Strict export recovery: never widen tolerance or resume optimizer updates."""

import copy

import numpy as np
import pytest

from src.ch04_rnn_lstm import export_r2


def test_strict_cpu_reference_keeps_original_gpu_failure_visible():
    portable = np.array([[0.120684266]], dtype="float32")
    native_cpu = np.array([[0.120684080]], dtype="float32")
    fused_gpu = np.array([[0.120659098]], dtype="float32")
    result = export_r2.compare_outputs(portable, native_cpu, fused_gpu)
    assert result["cpu_reference"]["status"] == "PASS"
    assert result["original_gpu_cpu_gate"]["status"] == "FAIL"
    assert result["rtol"] == 1e-4 and result["atol"] == 1e-5
    with pytest.raises(AssertionError):
        export_r2.compare_outputs(portable, fused_gpu, fused_gpu)


@pytest.mark.parametrize("bad", [np.nan, np.inf])
def test_export_rejects_nonfinite_and_mismatched_shapes(bad):
    x = np.zeros((2, 3), "float32")
    with pytest.raises(ValueError):
        export_r2.compare_outputs(x, np.full_like(x, bad), x)
    with pytest.raises(ValueError):
        export_r2.compare_outputs(x, x[:1], x)


def test_completed_progress_is_not_an_invitation_to_train_again():
    weights = {"w": np.array([2.0], "float32")}
    budget = {"max_epochs": 40, "patience": 6}
    progress = {"history": [{"epoch": i} for i in range(11)],
                "early_stopping": {"bad_epochs": 6, "best_epoch": 4},
                "best_weights": weights}
    assert export_r2.completed_progress(progress, budget, weights) == 4
    active = copy.deepcopy(progress)
    active["early_stopping"]["bad_epochs"] = 5
    with pytest.raises(ValueError):
        export_r2.completed_progress(active, budget, weights)
    with pytest.raises(ValueError):
        export_r2.completed_progress(progress, budget, {"w": np.array([3.0], "float32")})
    with pytest.raises(ValueError):
        export_r2.completed_progress(None, budget, weights)


def test_recovery_schema_only_allows_null_original_training_telemetry():
    from src.common.contracts import ROOT, read_json
    release = read_json(ROOT / "artifacts/manifests/phase28/release.json")
    entry = next(e for e in release["runs"] if e["method"] == "pytorch")
    original = read_json(ROOT / "artifacts/metrics/phase28/validation" / (entry["run_id"] + ".json"))
    document = copy.deepcopy(original)
    document["run_id"] = export_r2.ORPHAN
    document["schema_version"] = export_r2.RECOVERY_VERSION
    for key in export_r2.MISSING_TELEMETRY:
        document["efficiency"][key] = None
    document["warnings"].append(export_r2.LOST_TELEMETRY_WARNING)
    export_r2.validate_run(document)
    with pytest.raises(ValueError):
        bad = copy.deepcopy(document)
        bad["efficiency"]["train_seconds"] = 0
        export_r2.validate_run(bad)
    with pytest.raises(ValueError):
        bad = copy.deepcopy(document)
        bad["run_id"] = "other_run"
        export_r2.validate_run(bad)
    export_r2.validate_run(original)


def test_unrelated_assertion_never_enters_crash_finalizer():
    try:
        raise AssertionError("not the frozen export stage")
    except AssertionError as failure:
        assert export_r2.export_failure_context(failure) is None
