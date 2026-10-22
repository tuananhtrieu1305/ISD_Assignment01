"""Synthetic journal and strict schema tests for the approved continuation only."""

import copy
import json

import pytest

from src.ch04_rnn_lstm.phase29 import protocol
from src.ch04_rnn_lstm.phase29_revision.recovery import (
    ContinuationGate,
    build_orphan_record,
    create_gate,
    validate_recovery_test,
)
from src.common.artifact_core import write_once
from src.common.contracts import canonical_sha256, read_json


@pytest.fixture
def journal(tmp_path, monkeypatch):
    monkeypatch.setattr(protocol, "ROOT", tmp_path)
    old, new = tmp_path / "old", tmp_path / "new"
    write_once(old / "manifest.json", {"dataset_id": "ch4_household_power"})
    write_once(
        old / "seal.json",
        {
            "state": "failed_sealed",
            "evaluation_count": 1,
            "manifest_sha256": canonical_sha256(read_json(old / "manifest.json")),
        },
    )
    manifest = {
        "evaluator_sha256": "a" * 64,
        "dataset_id": "ch4_household_power",
        "original_seal": protocol.ref(old / "seal.json"),
        "original_manifest": protocol.ref(old / "manifest.json"),
        "approved_run_ids": ["future_run"],
        "evidence_kind": "synthetic_fixture",
    }
    create_gate(new, manifest)
    return ContinuationGate(new), old, new, manifest


def test_continuation_keeps_failed_seal_and_does_not_increment_batch_count(journal):
    gate, old, _, _ = journal
    before = protocol.ref(old / "seal.json")
    gate.begin("a" * 64)
    gate.claim("future_run", "a" * 64)
    gate.record("future_run", {"status": "PASS", "run_id": "future_run"})
    gate.complete("a" * 64)
    assert gate.state()["state"] == "evaluated"
    assert gate.state()["evaluation_count"] == 1 and gate.state()["additional_test_batches"] == 0
    assert protocol.ref(old / "seal.json") == before
    with pytest.raises(ValueError):
        gate.claim("future_run", "a" * 64)


@pytest.mark.parametrize(
    "fault", ["unknown", "old_claim", "duplicate", "materialize", "code", "incomplete", "tamper"]
)
def test_fail_closed_continuation(journal, fault):
    gate, old, new, manifest = journal
    gate.begin("a" * 64)
    if fault == "unknown":
        action = lambda: gate.claim("not_approved", "a" * 64)
    elif fault == "old_claim":
        (old / "future_run.claimed").touch()
        action = lambda: gate.claim("future_run", "a" * 64)
    elif fault == "duplicate":
        gate.claim("future_run", "a" * 64)
        action = lambda: gate.claim("future_run", "a" * 64)
    elif fault == "materialize":
        action = lambda: gate.materialize("a" * 64)
    elif fault == "code":
        action = lambda: gate.claim("future_run", "b" * 64)
    elif fault == "incomplete":
        action = lambda: gate.complete("a" * 64)
    else:
        write_once(new / "unrelated.json", {})
        manifest["approved_run_ids"] = ["changed"]
        (new / "manifest.json").write_text(json.dumps(manifest))
        action = lambda: gate.claim("future_run", "a" * 64)
    with pytest.raises(ValueError):
        action()


def test_failed_continuation_cannot_restart_and_keeps_original_bytes(journal):
    gate, old, _, _ = journal
    before = protocol.ref(old / "seal.json")
    gate.begin("a" * 64)
    gate.fail("synthetic failure")
    assert gate.state()["state"] == "failed_sealed"
    with pytest.raises(ValueError):
        gate.begin("a" * 64)
    assert protocol.ref(old / "seal.json") == before


def test_consumed_partial_claim_cannot_finish_or_retry(journal):
    gate, _, _, _ = journal
    gate.begin("a" * 64)
    gate.claim("future_run", "a" * 64)
    with pytest.raises(ValueError, match="Interrupted"):
        gate.complete("a" * 64)


def test_result_without_claim_or_failure_is_rejected(journal):
    gate, _, _, _ = journal
    gate.begin("a" * 64)
    with pytest.raises(ValueError):
        gate.record("future_run", {"run_id": "future_run", "status": "PASS"})


def test_measured_continuation_verifies_result_artifacts(tmp_path, monkeypatch):
    gate, _old, _new, manifest = journal.__wrapped__(tmp_path, monkeypatch)
    manifest["evidence_kind"] = "measured"
    other = tmp_path / "measured"
    create_gate(other, manifest)
    gate = ContinuationGate(other)
    artifact = tmp_path / "fixture.json"
    write_once(artifact, {"evidence_kind": "synthetic_fixture"})
    gate.begin("a" * 64)
    gate.claim("future_run", "a" * 64)
    result = {
        "status": "PASS",
        "run_id": "future_run",
        **{k: protocol.ref(artifact) for k in ("metrics", "details", "predictions", "checkpoint")},
    }
    gate.record("future_run", result)
    gate.complete("a" * 64)
    assert gate.state()["state"] == "evaluated"


def orphan_fixture():
    selected = read_json(
        protocol.BASE.parent / "phase28/runs/ch4_household_power_rnn_pytorch_s17_main/selection.json"
    )
    original = read_json(protocol.checked(selected["validation_metrics"]))
    details = {
        "metrics": {"rmse": {"value": 1.0, "undefined_reason": None}},
        "optimizer_updates": 0,
        "test_forward_passes_per_window": 1,
        "evaluator_sha256": "b" * 64,
        "training_selection": {"path": "synthetic.json", "sha256": "c" * 64},
    }
    return selected, original, details


def test_orphan_finalization_is_schema_only_and_keeps_null_cost():
    selected, original, details = orphan_fixture()
    metric, revised = build_orphan_record(
        original,
        details,
        selected,
        {"path": "artifacts/synthetic_predictions.gz", "sha256": "d" * 64},
        {"path": "artifacts/synthetic_details.json", "sha256": "e" * 64},
        "a" * 64,
        "2026-10-20T00:00:00+00:00",
        "synthetic_test_seal",
        "kW",
    )
    validate_recovery_test(metric)
    assert metric["split"] == "test" and metric["efficiency"] == original["efficiency"]
    assert all(
        metric["efficiency"][k] is None for k in ("train_seconds", "peak_ram_bytes", "peak_vram_bytes")
    )
    assert revised["schema_recovery_only"] and revised["inference_evaluator_sha256"] == "b" * 64


@pytest.mark.parametrize(
    "field,value",
    [
        ("run_id", "different_run"),
        ("split", "validation"),
        ("implementation", "scratch"),
        ("device", "cpu"),
        ("cost", 0),
        ("warning", None),
    ],
)
def test_test_recovery_schema_only_accepts_exact_orphan_and_null_telemetry(field, value):
    selected, original, details = orphan_fixture()
    metric, _ = build_orphan_record(
        original,
        details,
        selected,
        {"path": "artifacts/synthetic_predictions.gz", "sha256": "d" * 64},
        {"path": "artifacts/synthetic_details.json", "sha256": "e" * 64},
        "a" * 64,
        "2026-10-20T00:00:00+00:00",
        "synthetic_test_seal",
        "kW",
    )
    metric = copy.deepcopy(metric)
    if field == "cost":
        metric["efficiency"]["train_seconds"] = value
    elif field == "warning":
        metric["warnings"] = []
    else:
        metric[field] = value
    with pytest.raises(ValueError):
        validate_recovery_test(metric)
