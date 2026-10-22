import pytest

from src.ch02_ml import workflow
from src.ch02_ml.test_gate import EvaluationGate
from src.common.artifact_core import write_once


def gate_for(path):
    gate = EvaluationGate(path)
    gate.lock(
        {
            "evidence_kind": "synthetic_fixture",
            "dataset_id": "ch2_ames_housing",
            "split_sha256": "a" * 64,
            "runs": ["run_a", "run_b"],
            "code_sha256": "b" * 64,
        }
    )
    gate.begin("b" * 64)
    return gate


def test_unclaimed_resume_and_consumed_crash(tmp_path):
    gate = gate_for(tmp_path)
    assert workflow.pending_test_runs(gate) == ["run_a", "run_b"]
    gate.claim("run_a", "b" * 64)
    with pytest.raises(ValueError, match="permanently sealed"):
        workflow.pending_test_runs(gate)
    assert gate.state()["state"] == "failed_sealed"
    with pytest.raises(ValueError):
        workflow.pending_test_runs(gate)


def test_completed_results_and_reference_integrity(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "ROOT", tmp_path)
    gate = gate_for(tmp_path / "gate")
    write_once(tmp_path / "dummy.json", {"synthetic": True})
    record = {"path": "dummy.json", "sha256": workflow.sha256_file(tmp_path / "dummy.json")}
    for run in ("run_a", "run_b"):
        gate.claim(run, "b" * 64)
        gate.record(run, {"status": "PASS", "metrics": record, "predictions": record, "details": record})
    assert workflow.pending_test_runs(gate) == []
    gate.complete()
    assert workflow.pending_test_runs(gate) == []
    with pytest.raises(ValueError):
        workflow.checked_reference({**record, "sha256": "0" * 64})
    with pytest.raises(ValueError):
        workflow.selections({"runs": [], "expected_run_ids": []})
