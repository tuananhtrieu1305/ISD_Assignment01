"""No TEST reopening, code drift, missing run or partial-group publication."""

import pytest

from src.ch02_ml.test_gate import EvaluationGate


def test_once_only_and_fail_closed(tmp_path):
    gate = EvaluationGate(tmp_path)
    manifest = {
        "dataset_id": "ch2_cdc_diabetes",
        "split_sha256": "a" * 64,
        "runs": ["run_a", "run_b"],
        "code_sha256": "b" * 64,
    }
    gate.lock(manifest)
    with pytest.raises(ValueError):
        gate.begin("c" * 64)
    gate.begin("b" * 64)
    gate.claim("run_a", "b" * 64)
    with pytest.raises(ValueError):
        gate.claim("run_a", "b" * 64)
    with pytest.raises(ValueError):
        gate.claim("run_b", "c" * 64)
    with pytest.raises(ValueError):
        gate.claim("../escape", "b" * 64)
    with pytest.raises(ValueError):
        gate.begin("b" * 64)
    with pytest.raises(ValueError):
        gate.record("unknown", {"status": "PASS"})
    gate.record("run_a", {"status": "PASS"})
    with pytest.raises(ValueError):
        gate.record("run_a", {"status": "PASS"})
    with pytest.raises(ValueError):
        gate.complete()
    gate.record("run_b", {"status": "PASS"})
    gate.complete()
    assert gate.state()["evaluation_count"] == 1
    with pytest.raises(ValueError):
        gate.begin("b" * 64)
    with pytest.raises(ValueError):
        gate.lock(manifest)


def test_failure_permanently_seals_batch(tmp_path):
    gate = EvaluationGate(tmp_path)
    gate.lock(
        {
            "dataset_id": "ch2_ames_housing",
            "split_sha256": "a" * 64,
            "runs": ["run_a"],
            "code_sha256": "b" * 64,
        }
    )
    gate.begin("b" * 64)
    gate.fail("synthetic failure")
    assert gate.state()["state"] == "failed_sealed"
    with pytest.raises(ValueError):
        gate.begin("b" * 64)
