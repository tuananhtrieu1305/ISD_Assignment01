"""Synthetic trainer and resumability tests precede real-data training."""

import numpy as np
import pytest

from src.ch02_ml.training import ScratchTrainer, fit, predict_batches, task_outputs
from src.common.model_core import build_plan, canonical_weights


def fixture_data():
    rng = np.random.default_rng(42)
    x = rng.normal(size=(40, 2)).astype("float32")
    y = (x[:, 0:1] > 0.1).astype("float32")
    return x, y


def test_scratch_training_resume_equivalence():
    plan = build_plan("mlp", [2], 1, tiny=True)
    weights = canonical_weights(plan, 17)
    x, y = fixture_data()
    first = ScratchTrainer(plan, weights)
    second = ScratchTrainer(plan, weights)
    first.step(x[:8], y[:8], "binary", np.ones(8, dtype="float32"))
    state = first.export_state()
    second.restore_state(state)
    for trainer in (first, second):
        trainer.step(x[8:16], y[8:16], "binary", np.ones(8, dtype="float32"))
    for name, value in first.weights().items():
        np.testing.assert_array_equal(value, second.weights()[name])
    assert first.iterations == 2
    with pytest.raises(ValueError):
        second.restore_state({})


def test_generic_fit_has_history_and_best_checkpoint_not_test():
    x, y = fixture_data()
    plan = build_plan("mlp", [2], 1, tiny=True)
    trainer = ScratchTrainer(plan, canonical_weights(plan, 42))
    config = {
        "max_epochs": 3,
        "patience": 2,
        "min_delta": 1e-5,
        "batch_size": 8,
        "wall_time_limit_minutes": 1,
    }
    result = fit(trainer, x, y, x, y, "binary", seed=42, budget=config, progress=None)
    assert 1 <= len(result["history"]) <= 3
    assert result["best_epoch"] == min(result["history"], key=lambda row: row["validation_loss"])["epoch"]
    assert result["history"][0]["batch_order_sha256"]
    prediction = predict_batches(trainer, x, batch_size=7)
    assert prediction.shape == (40, 1)
    np.testing.assert_allclose(task_outputs(prediction, "binary").sum(axis=1), 1)
    np.testing.assert_array_equal(task_outputs(prediction, "mse"), prediction)
    with pytest.raises(ValueError):
        predict_batches(trainer, x, batch_size=0)


def test_resume_after_early_stop_does_not_train_extra_epochs():
    import copy

    x, y = fixture_data()
    plan = build_plan("mlp", [2], 1, tiny=True)
    budget = {
        "max_epochs": 10,
        "patience": 1,
        "min_delta": 100.0,
        "batch_size": 8,
        "wall_time_limit_minutes": 1,
    }
    snapshots = []
    first = fit(
        ScratchTrainer(plan, canonical_weights(plan, 17)),
        x,
        y,
        x,
        y,
        "binary",
        seed=17,
        budget=budget,
        progress=lambda state: snapshots.append(copy.deepcopy(state)),
    )
    second = fit(
        ScratchTrainer(plan, canonical_weights(plan, 17)),
        x,
        y,
        x,
        y,
        "binary",
        seed=17,
        budget=budget,
        resume=snapshots[-1],
    )
    assert second["history"] == first["history"]
    assert second["optimizer_steps"] == first["optimizer_steps"]


def test_interrupted_fit_matches_uninterrupted():
    import copy

    x, y = fixture_data()
    plan = build_plan("mlp", [2], 1, tiny=True)
    budget = {
        "max_epochs": 3,
        "patience": 6,
        "min_delta": 1e-5,
        "batch_size": 8,
        "wall_time_limit_minutes": 1,
    }
    snapshots = []

    def interrupt(state):
        snapshots.append(copy.deepcopy(state))
        raise InterruptedError("synthetic interruption")

    with pytest.raises(InterruptedError):
        fit(
            ScratchTrainer(plan, canonical_weights(plan, 17)),
            x,
            y,
            x,
            y,
            "binary",
            seed=17,
            budget=budget,
            progress=interrupt,
        )
    resumed = fit(
        ScratchTrainer(plan, canonical_weights(plan, 17)),
        x,
        y,
        x,
        y,
        "binary",
        seed=17,
        budget=budget,
        resume=snapshots[-1],
    )
    full = fit(
        ScratchTrainer(plan, canonical_weights(plan, 17)), x, y, x, y, "binary", seed=17, budget=budget
    )
    assert resumed["history"] == full["history"]
    for key, value in full["weights"].items():
        np.testing.assert_array_equal(value, resumed["weights"][key])


def test_invalid_resume_shape_and_nonfinite_are_rejected():
    import copy

    plan = build_plan("mlp", [2], 1, tiny=True)
    trainer = ScratchTrainer(plan, canonical_weights(plan, 42))
    state = trainer.export_state()
    key = next(iter(state["weights"]))
    bad = copy.deepcopy(state)
    bad["weights"][key] = np.zeros((1,), dtype="float32")
    with pytest.raises(ValueError):
        trainer.restore_state(bad)
    bad = copy.deepcopy(state)
    bad["m"][key].flat[0] = np.nan
    with pytest.raises(ValueError):
        trainer.restore_state(bad)
    bad = copy.deepcopy(state)
    bad["iterations"] = -1
    with pytest.raises(ValueError):
        trainer.restore_state(bad)


def test_empty_predict_invalid_task_and_wall_budget():
    x, y = fixture_data()
    plan = build_plan("mlp", [2], 1, tiny=True)
    trainer = ScratchTrainer(plan, canonical_weights(plan, 42))
    with pytest.raises(ValueError):
        predict_batches(trainer, x[:0])
    with pytest.raises(ValueError):
        task_outputs(x, "bogus")
    with pytest.raises(TimeoutError):
        fit(
            trainer,
            x,
            y,
            x,
            y,
            "binary",
            seed=42,
            budget={
                "patience": 1,
                "min_delta": 0,
                "max_epochs": 2,
                "batch_size": 8,
                "wall_time_limit_minutes": 0,
            },
        )
