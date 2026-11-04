"""Synthetic one-shot joint gate; no real holdout reader or forward."""

import copy

import pytest

from src.ch04_rnn_lstm.phase29.joint_gate import JointGate


def manifest():
    return {
        "phase": 29,
        "dataset_id": "ch4_gold_pink_sheet",
        "evidence_kind": "synthetic_fixture",
        "evaluator_sha256": "a" * 64,
        "approved_run_ids": ["synthetic_rnn", "synthetic_lstm"],
        "families_locked": ["rnn", "lstm"],
        "pretest_verification_sha256": "b" * 64,
    }


def test_joint_gate_claim_consumed_before_materialization_and_never_reopened(tmp_path):
    gate = JointGate(tmp_path)
    gate.lock(manifest())
    assert gate.state()["evaluation_count"] == 0
    with pytest.raises(ValueError):
        gate.materialize("a" * 64)
    gate.begin("a" * 64)
    assert gate.state()["evaluation_count"] == 1
    gate.materialize("a" * 64)
    with pytest.raises(ValueError):
        gate.materialize("a" * 64)
    for run in manifest()["approved_run_ids"]:
        gate.claim(run, "a" * 64)
        gate.record(run, {"status": "PASS", "synthetic": True})
        with pytest.raises(ValueError):
            gate.claim(run, "a" * 64)
    gate.complete("a" * 64)
    assert gate.state()["state"] == "evaluated"
    assert gate.state()["evaluation_count"] == 1
    with pytest.raises(ValueError):
        gate.begin("a" * 64)


def test_failed_batch_crash_and_incomplete_batch_are_fail_closed(tmp_path):
    gate = JointGate(tmp_path)
    gate.lock(manifest())
    gate.begin("a" * 64)
    with pytest.raises(ValueError):
        gate.complete("a" * 64)
    gate.fail("synthetic failure")
    assert gate.state()["state"] == "failed_sealed" and gate.state()["evaluation_count"] == 1
    with pytest.raises(ValueError):
        gate.begin("a" * 64)
    with pytest.raises(ValueError):
        gate.claim("synthetic_lstm", "a" * 64)


def test_gate_rejects_wrong_code_unapproved_run_missing_claim_and_tampered_manifest(tmp_path):
    gate = JointGate(tmp_path)
    gate.lock(manifest())
    with pytest.raises(ValueError):
        gate.begin("c" * 64)
    assert gate.state()["evaluation_count"] == 0
    gate.begin("a" * 64)
    with pytest.raises(ValueError):
        gate.claim("../../escape", "a" * 64)
    with pytest.raises(ValueError):
        gate.record("synthetic_rnn", {"status": "PASS"})
    with pytest.raises(ValueError):
        gate.claim("synthetic_rnn", "c" * 64)
    (tmp_path / "manifest.json").write_text("{}")
    with pytest.raises(ValueError):
        gate.claim("synthetic_rnn", "a" * 64)


@pytest.mark.parametrize(
    "field,value",
    [
        ("phase", 28),
        ("dataset_id", "ch5_finqa"),
        ("approved_run_ids", []),
        ("approved_run_ids", ["duplicate", "duplicate"]),
        ("approved_run_ids", ["../escape"]),
        ("families_locked", ["rnn"]),
        ("evaluator_sha256", "bad"),
        ("pretest_verification_sha256", None),
    ],
)
def test_gate_rejects_incomplete_declaration_without_side_effects(tmp_path, field, value):
    obj = copy.deepcopy(manifest())
    obj[field] = value
    gate = JointGate(tmp_path)
    with pytest.raises(ValueError):
        gate.lock(obj)
    assert not (tmp_path / "manifest.json").exists()


def test_duplicate_lock_and_duplicate_result_rejected(tmp_path):
    gate = JointGate(tmp_path)
    gate.lock(manifest())
    with pytest.raises(ValueError):
        gate.lock(manifest())
    gate.begin("a" * 64)
    gate.claim("synthetic_rnn", "a" * 64)
    gate.record("synthetic_rnn", {"status": "PASS"})
    with pytest.raises(ValueError):
        gate.record("synthetic_rnn", {"status": "PASS"})
