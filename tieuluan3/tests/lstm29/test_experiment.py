"""Synthetic end-to-end validation run; TEST is structurally absent."""

import json
from typing import ClassVar

import numpy as np
import pytest

from src.ch04_rnn_lstm.phase29 import experiment, protocol
from src.common.artifact_core import write_once
from src.common.model_core import build_plan


@pytest.fixture
def synthetic_run(tmp_path, monkeypatch):
    monkeypatch.setattr(protocol, "ROOT", tmp_path)
    for name in ("ROOT", "BASE", "MODELS", "METRICS", "PREDICTIONS"):
        monkeypatch.setattr(
            experiment, name, tmp_path / "artifacts" / name.lower() if name != "ROOT" else tmp_path
        )
    plan = build_plan("lstm", [5, 2], 3, tiny=True)
    prep = tmp_path / "data/preprocessing.json"
    write_once(prep, {"synthetic": True})
    prep_ref = protocol.ref(prep)

    class Adapter:
        def inverse_target(self, values):
            return np.asarray(values, "float64") * 2 + 10

    class Data:
        train_ids: ClassVar = ["a", "b", "c", "d"]
        validation_ids: ClassVar = ["e", "f", "g", "h"]
        horizons: ClassVar = [1, 3, 6]
        adapter = Adapter()
        rows: ClassVar = {key: {"series": "S", "target_times": ["2000-01-01"] * 3} for key in "abcdefgh"}
        view = None

        def contract(self):
            return {"preprocessing": prep_ref}

        def batch(self, ids):
            positions = np.asarray([(ord(key) - ord("a")) % 4 for key in ids])
            rng = np.random.default_rng(22)
            x = rng.normal(size=(4, 5, 2)).astype("float32")
            y = rng.normal(size=(4, 3)).astype("float32")
            return x[positions], y[positions]

        def targets(self, ids):
            return self.adapter.inverse_target(self.batch(ids)[1])

        def series(self, ids):
            return ["S"] * len(ids)

        def baseline(self, ids, method):
            return self.adapter.inverse_target(np.repeat(self.batch(ids)[0][:, -1, :1], 3, axis=1))

    data = Data()
    data.view = data
    data_path = tmp_path / "artifacts/data.json"
    write_once(data_path, data.contract())
    config = {
        "dataset_id": "ch4_gold_pink_sheet",
        "plan": plan,
        "task": "mse",
        "fold": None,
        "code": {"git_commit": "0" * 40, "dirty_tree_sha256": "a" * 64},
        "environment_sha256": "a" * 64,
        "protocol_sha256": "a" * 64,
        "provenance": {
            key: "a" * 64
            for key in (
                "adapter_sha256",
                "dataset_sha256",
                "split_sha256",
                "subset_sha256",
                "preprocessing_sha256",
            )
        },
        "adapter": prep_ref,
        "data_contract": protocol.ref(data_path),
        "unit": "USD/troy ounce",
        "training": {
            "patience": 6,
            "min_delta": 1e-5,
            "max_epochs": 2,
            "batch_size": 2,
            "wall_time_limit_minutes": 2,
        },
        "canonical_initial_weights_sha256": experiment.canonical_sha256(
            {k: v.tolist() for k, v in experiment.canonical_weights(plan, 17).items()}
        ),
    }
    config_path = tmp_path / "experiments/config.json"
    write_once(config_path, config)
    monkeypatch.setattr(experiment, "WindowData", lambda *args: data)
    return tmp_path, config_path, data


@pytest.mark.parametrize("method", ["scratch"])
def test_validation_run_checkpoint_resume_predictions_and_reuse(synthetic_run, monkeypatch, method):
    root, config_path, _ = synthetic_run
    run = "synthetic_" + method
    folder = experiment.BASE / "runs" / run
    contract = folder / "model_contract.json"
    write_once(contract, {"synthetic": True})
    entry = {
        "run_id": run,
        "dataset_id": "ch4_gold_pink_sheet",
        "fold": None,
        "seed": 17,
        "method": method,
        "config": protocol.ref(config_path),
        "model_contract": protocol.ref(contract),
        "comparison_group_sha256": "b" * 64,
    }
    monkeypatch.setattr(experiment, "check_sources", lambda: {"runs": [entry]})
    result = experiment.train_run(run)
    assert result["status"] == "PASS"
    selected = json.loads((folder / "selection.json").read_text())
    assert selected["test_evaluation_executed"] is False
    assert selected["selection_split"] == "validation"
    assert experiment.train_run(run)["status"] == "reused"
    if method == "scratch":
        resumed = experiment.load_progress(run, entry["config"]["sha256"])
        assert len(resumed["history"]) == 2
        with pytest.raises(ValueError):
            experiment.load_progress(run, "c" * 64)
    assert not list(root.rglob("*test_seal*"))


def test_unknown_trainer_and_invalid_metric_horizon():
    with pytest.raises(ValueError):
        experiment.make_trainer("invalid", {}, {})
    values = {
        "rmse": {"value": 2, "undefined_reason": None},
        "by_horizon": {"6": {"mae": {"value": 1, "undefined_reason": None}}},
    }
    assert experiment.metric_rows(values, "kW")[-1]["horizon"] == 6
