"""One tiny synthetic selected model -> sealed once-only evaluation, never real TEST."""

from typing import ClassVar

import pytest

from src.ch04_rnn_lstm.phase29 import experiment, joint_evaluation, protocol
from src.ch04_rnn_lstm.phase29.joint_gate import JointGate
from src.common.artifact_core import write_once
from src.common.contracts import read_json
from tests.lstm29 import test_experiment as frozen_fixtures


@pytest.fixture
def selected_fixture(tmp_path, monkeypatch):
    return frozen_fixtures.synthetic_run.__wrapped__(tmp_path, monkeypatch)


@pytest.mark.parametrize("mutate", [False, True])
def test_synthetic_joint_worker_saves_one_pass_predictions_and_never_updates_weights(
    selected_fixture, monkeypatch, mutate
):
    root, config_path, data = selected_fixture
    run = "synthetic_lstm_joint"
    folder = experiment.BASE / "runs" / run
    contract = folder / "model_contract.json"
    write_once(contract, {"synthetic": True})
    entry = {
        "run_id": run,
        "dataset_id": "ch4_gold_pink_sheet",
        "fold": None,
        "seed": 17,
        "method": "scratch",
        "config": protocol.ref(config_path),
        "model_contract": protocol.ref(contract),
        "comparison_group_sha256": "b" * 64,
    }
    monkeypatch.setattr(experiment, "check_sources", lambda: {"runs": [entry]})
    experiment.train_run(run)
    selected_ref = protocol.ref(folder / "selection.json")
    selected = read_json(protocol.checked(selected_ref))
    member = {**entry, "family": "lstm", "owner_phase": 29, "selection": selected_ref}
    before = protocol.ref(protocol.checked(selected["checkpoint"]))
    gate = JointGate(root / "synthetic_seal")
    gate.lock(
        {
            "phase": 29,
            "dataset_id": "ch4_gold_pink_sheet",
            "evidence_kind": "synthetic_fixture",
            "evaluator_sha256": "a" * 64,
            "pretest_verification_sha256": "b" * 64,
            "families_locked": ["rnn", "lstm"],
            "approved_run_ids": [run],
            "members": [member],
        }
    )
    gate.begin("a" * 64)
    gate.materialize("a" * 64)
    calls = []

    class Cache:
        ids: ClassVar = ["synthetic_test_a", "synthetic_test_b"]
        horizons = data.horizons
        metadata: ClassVar = {
            "dataset_id": entry["dataset_id"],
            "input_shape": [5, 2],
            "preprocessing": data.contract()["preprocessing"],
        }
        rows: ClassVar = {
            key: {"series": "S", "target_times": ["2000-01-01"] * 3}
            for key in ("synthetic_test_a", "synthetic_test_b")
        }

        def batch(self, ids):
            calls.extend(ids)
            return data.batch(["a" if k.endswith("a") else "b" for k in ids])

        def targets(self, ids):
            return data.targets(["a" if k.endswith("a") else "b" for k in ids])

        def series(self, ids):
            return ["S"] * len(ids)

    for name in ("METRICS", "PREDICTIONS", "BASE"):
        monkeypatch.setattr(joint_evaluation, name, root / "artifacts" / "joint" / name.lower())
    monkeypatch.setattr(joint_evaluation, "TensorAdapter", lambda state: data.adapter)
    original = experiment.make_trainer

    def inference_only(method, plan, weights):
        trainer = original(method, plan, weights)
        trainer.step = lambda *args: pytest.fail("TEST must never update weights")
        if mutate:
            predict = trainer.predict

            def invalid_prediction(x):
                result = predict(x)
                changed = trainer.weights()
                changed[next(iter(changed))] += 0.1
                trainer.assign(changed)
                return result

            trainer.predict = invalid_prediction
        return trainer

    monkeypatch.setattr(
        joint_evaluation,
        "make_native",
        lambda member, config, weights: inference_only(member["method"], config["plan"], weights),
    )
    if mutate:
        with pytest.raises(ValueError, match="weights|optimizer"):
            joint_evaluation.evaluate_member(gate, "a" * 64, run, Cache())
        assert not (gate.root / (run + ".result.json")).exists()
        return
    result = joint_evaluation.evaluate_member(gate, "a" * 64, run, Cache())
    assert result["status"] == "PASS" and calls == Cache.ids
    metric = read_json(protocol.checked(result["metrics"]))
    assert metric["split"] == "test" and metric["evidence_kind"] == "synthetic_fixture"
    assert metric["test_seal_id"] and metric["family"] == "lstm"
    assert protocol.ref(protocol.checked(selected["checkpoint"])) == before
    gate.complete("a" * 64)
    assert gate.state()["evaluation_count"] == 1
    with pytest.raises(ValueError):
        joint_evaluation.evaluate_member(gate, "a" * 64, run, Cache())
