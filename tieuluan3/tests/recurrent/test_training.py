"""Manual BPTT, recurrent Adam slot layout, independent Keras GPU and resume."""

import copy
from typing import ClassVar

import numpy as np
import pytest

from src.ch02_ml.training import ScratchTrainer
from src.ch04_rnn_lstm.training import RnnKerasTrainer, RnnTorchTrainer, fit_windows
from src.common.model_core import build_plan, canonical_weights
from src.common.numpy_engine import NumpyNetwork


def fixture():
    plan = build_plan("rnn", [5, 2], 3, tiny=True)
    weights = canonical_weights(plan, 17)
    rng = np.random.default_rng(22)
    return (
        plan,
        weights,
        rng.normal(size=(4, 5, 2)).astype("float32"),
        rng.normal(size=(4, 3)).astype("float32"),
    )


def assert_state_equal(a, b, tolerance=1e-5):
    assert a["iterations"] == b["iterations"]
    for field in ("weights", "m", "v"):
        for key in a[field]:
            np.testing.assert_allclose(a[field][key], b[field][key], rtol=tolerance, atol=1e-6)


def test_torch_recurrent_slots_canonical_and_resume():
    plan, weights, x, y = fixture()
    trainer = RnnTorchTrainer(plan, weights, "cpu")
    trainer.step(x, y, "mse", np.ones(4, "float32"))
    state = trainer.export_state()
    for name, param, _, key in trainer.model.parameter_pairs():
        expected = trainer.optimizer.optimizer.state[param]["exp_avg"].detach().cpu().numpy()
        np.testing.assert_array_equal(state["m"][name], expected.T if key in {"w", "u"} else expected)
    resumed = RnnTorchTrainer(plan, weights, "cpu")
    resumed.restore_state(state)
    for t in (trainer, resumed):
        t.step(x, y, "mse", np.ones(4, "float32"))
    assert_state_equal(trainer.export_state(), resumed.export_state())


def test_keras_gpu_recurrent_step_resume_and_canonical_adam():
    plan, weights, x, y = fixture()
    trainer = RnnKerasTrainer(plan, weights, "gpu")
    scratch = ScratchTrainer(plan, weights)
    for t in (trainer, scratch):
        t.step(x, y, "mse", np.ones(4, "float32"))
    for key in weights:
        np.testing.assert_allclose(trainer.weights()[key], scratch.weights()[key], rtol=1e-4, atol=3e-6)
    state = trainer.export_state()
    resumed = RnnKerasTrainer(plan, weights, "gpu")
    resumed.restore_state(state)
    for t in (trainer, resumed):
        t.step(x, y, "mse", np.ones(4, "float32"))
    assert_state_equal(trainer.export_state(), resumed.export_state())
    assert "GPU" in trainer.model.device and trainer.model.keras.backend.backend() == "tensorflow"


def test_manual_bptt_numeric_gradient_tiny_sequence():
    plan, weights, x, y = fixture()
    weights = {k: v.astype("float64") for k, v in weights.items()}
    model = NumpyNetwork(plan, weights)
    x, y = x.astype("float64"), y.astype("float64")
    _, grads, dx = model.loss_gradients(x, y, "mse")
    for key in weights:
        position = tuple(0 for _ in weights[key].shape)
        old = model.weights[key][position]
        values = []
        for delta in (1e-5, -1e-5):
            model.weights[key][position] = old + delta
            values.append(np.mean((model.forward(x) - y) ** 2))
        model.weights[key][position] = old
        np.testing.assert_allclose(grads[key][position], (values[0] - values[1]) / 2e-5, atol=1e-7, rtol=1e-3)
    assert dx.shape == x.shape and np.isfinite(dx).all()


def test_fit_windows_resume_matches_uninterrupted():
    plan, weights, x, y = fixture()

    class Data:
        train_ids: ClassVar = ["a", "b", "c", "d"]
        validation_ids: ClassVar = ["e", "f", "g", "h"]

        def batch(self, ids):
            positions = [(ord(k) - ord("a")) % 4 for k in ids]
            return x[positions], y[positions]

    data = Data()
    budget = {
        "patience": 6,
        "min_delta": 1e-5,
        "max_epochs": 3,
        "batch_size": 2,
        "wall_time_limit_minutes": 2,
    }
    saved = []
    complete = fit_windows(ScratchTrainer(plan, weights), data, seed=17, budget=budget)
    fit_windows(
        ScratchTrainer(plan, weights),
        data,
        seed=17,
        budget={**budget, "max_epochs": 1},
        progress=lambda state: saved.append(copy.deepcopy(state)),
    )
    resumed = fit_windows(ScratchTrainer(plan, weights), data, seed=17, budget=budget, resume=saved[-1])
    assert resumed["history"] == complete["history"]
    for key in weights:
        np.testing.assert_array_equal(resumed["weights"][key], complete["weights"][key])
    with pytest.raises(TimeoutError):
        fit_windows(
            ScratchTrainer(plan, weights), data, seed=17, budget={**budget, "wall_time_limit_minutes": 0}
        )
