"""Synthetic joint evaluator ledger: matched main members and fail-closed pending jobs."""

import pytest

from src.ch04_rnn_lstm.phase29 import joint_evaluation
from src.ch04_rnn_lstm.phase29.joint_gate import JointGate


def matrix(family, baselines=False):
    result = []
    for dataset in joint_evaluation.DATASETS:
        for fold in (None, 1, 2, 3):
            for seed in (17, 42, 73):
                for method in ("scratch", "keras", "pytorch"):
                    result.append(
                        {
                            "run_id": f"{dataset}_{family}_{method}_{seed}_{fold}",
                            "dataset_id": dataset,
                            "fold": fold,
                            "method": method,
                            "seed": seed,
                        }
                    )
            if baselines:
                for method in ("last_value", "seasonal_naive"):
                    result.append(
                        {
                            "run_id": f"{dataset}_{method}_{fold}",
                            "dataset_id": dataset,
                            "fold": fold,
                            "method": method,
                            "seed": 42,
                        }
                    )
    return {"runs": result}


def test_exact_main_joint_members_and_preserved_baselines():
    members = joint_evaluation.approved_members(matrix("rnn", True), matrix("lstm"))
    assert len(members) == 60
    assert all(m["fold"] is None for m in members)
    for dataset in joint_evaluation.DATASETS:
        rows = [m for m in members if m["dataset_id"] == dataset]
        assert len(rows) == 20
        assert sum(m["family"] == "rnn" for m in rows) == 9
        assert sum(m["family"] == "lstm" for m in rows) == 9
        assert sum(m["family"] == "classical" for m in rows) == 2


@pytest.mark.parametrize("fault", ["duplicate", "missing", "wrong_seed", "unknown_method", "unknown_dataset"])
def test_member_matrix_rejects_invalid_or_partial_declaration(fault):
    rnn, lstm = matrix("rnn", True), matrix("lstm")
    if fault == "duplicate":
        lstm["runs"].append(lstm["runs"][0].copy())
    elif fault == "missing":
        lstm["runs"].pop(0)
    elif fault == "wrong_seed":
        lstm["runs"][0]["seed"] = 999
    elif fault == "unknown_method":
        lstm["runs"][0]["method"] = "other"
    else:
        lstm["runs"][0]["dataset_id"] = "ch5_finqa"
    with pytest.raises(ValueError):
        joint_evaluation.approved_members(rnn, lstm)


def test_interrupted_claim_is_not_an_invitation_to_repeat_test(tmp_path):
    gate = JointGate(tmp_path)
    gate.lock(
        {
            "phase": 29,
            "dataset_id": "ch4_gold_pink_sheet",
            "evidence_kind": "synthetic_fixture",
            "evaluator_sha256": "a" * 64,
            "approved_run_ids": ["synthetic_a", "synthetic_b"],
            "families_locked": ["rnn", "lstm"],
            "pretest_verification_sha256": "b" * 64,
        }
    )
    gate.begin("a" * 64)
    assert joint_evaluation.pending(gate, "a" * 64) == ["synthetic_a", "synthetic_b"]
    gate.claim("synthetic_a", "a" * 64)
    with pytest.raises(ValueError, match="Interrupted"):
        joint_evaluation.pending(gate, "a" * 64)
    gate.record("synthetic_a", {"status": "PASS"})
    assert joint_evaluation.pending(gate, "a" * 64) == ["synthetic_b"]
    gate.claim("synthetic_b", "a" * 64)
    gate.record("synthetic_b", {"status": "PASS"})
    gate.complete("a" * 64)
    assert joint_evaluation.pending(gate, "a" * 64) == []
