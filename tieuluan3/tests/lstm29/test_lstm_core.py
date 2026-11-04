"""Phase29 synthetic LSTM gate/BPTT/parity/resume tests, never holdout data."""

import copy

import numpy as np
import pytest

from src.ch02_ml.training import ScratchTrainer
from src.ch04_rnn_lstm.phase29.diagnostics import gate_diagnostics
from src.ch04_rnn_lstm.phase29.training import LstmKerasTrainer, LstmTorchTrainer
from src.ch04_rnn_lstm.training import fit_windows
from src.common.model_core import build_plan, canonical_weights, make_contract
from src.common.numpy_engine import NumpyNetwork
from src.common.parity import gradient_parity


def fixture():
    plan = build_plan("lstm", [5, 2], 3, tiny=True)
    weights = canonical_weights(plan, 17)
    rng = np.random.default_rng(22)
    return (
        plan,
        weights,
        rng.normal(size=(4, 5, 2)).astype("float32"),
        rng.normal(size=(4, 3)).astype("float32"),
    )


def test_all_lstm_gates_bptt_numerical_weight_and_input_gradients():
    plan, weights, x, y = fixture()
    # Positive hidden Dense bias avoids dead ReLUs and checks every gate, not only one element.
    weights = {k: v.astype("float64") for k, v in weights.items()}
    for step in plan["steps"]:
        if step["kind"] == "dense":
            weights[step["id"] + "/b"][:] = 0.2
    model = NumpyNetwork(plan, weights)
    x, y = x.astype("float64"), y.astype("float64")
    _, gradients, dx = model.loss_gradients(x, y, "mse")
    eps = 1e-5
    for key, array in model.weights.items():
        numerical = np.zeros_like(array)
        for pos in np.ndindex(array.shape):
            original = array[pos]
            array[pos] = original + eps
            plus = np.mean((model.forward(x) - y) ** 2)
            array[pos] = original - eps
            minus = np.mean((model.forward(x) - y) ** 2)
            array[pos] = original
            numerical[pos] = (plus - minus) / (2 * eps)
        np.testing.assert_allclose(gradients[key], numerical, atol=1e-8, rtol=1e-3)
    for pos in ((0, 0, 0), (1, 2, 1), (3, 4, 0)):
        original = x[pos]
        x[pos] = original + eps
        plus = np.mean((model.forward(x) - y) ** 2)
        x[pos] = original - eps
        minus = np.mean((model.forward(x) - y) ** 2)
        x[pos] = original
        np.testing.assert_allclose(dx[pos], (plus - minus) / (2 * eps), atol=1e-8, rtol=1e-3)


def test_torch_lstm_canonical_adam_and_resume():
    plan, weights, x, y = fixture()
    trainer = LstmTorchTrainer(plan, weights, "cpu")
    scratch = ScratchTrainer(plan, weights)
    gradient_parity(
        NumpyNetwork(plan, weights).loss_gradients(x, y, "mse")[1],
        trainer.model.loss_gradients(x, y, "mse")[1],
    )
    for t in (trainer, scratch):
        t.step(x, y, "mse", np.ones(4, "float32"))
    for key in weights:
        np.testing.assert_allclose(trainer.weights()[key], scratch.weights()[key], rtol=1e-4, atol=3e-6)
    state = trainer.export_state()
    resumed = LstmTorchTrainer(plan, weights, "cpu")
    resumed.restore_state(state)
    for t in (trainer, resumed):
        t.step(x, y, "mse", np.ones(4, "float32"))
    for field in ("weights", "m", "v"):
        for key in state[field]:
            np.testing.assert_allclose(
                trainer.export_state()[field][key], resumed.export_state()[field][key], atol=1e-6, rtol=1e-5
            )
    assert trainer.iterations == resumed.iterations == 2
    assert all(
        not trainer.model.ops[s["id"]].bias_hh_l0.requires_grad for s in plan["steps"] if s["kind"] == "lstm"
    )


def test_keras_lstm_gpu_graph_resume_and_adam():
    plan, weights, x, y = fixture()
    trainer = LstmKerasTrainer(plan, weights, "gpu")
    reference = ScratchTrainer(plan, weights)
    gradient_parity(
        NumpyNetwork(plan, weights).loss_gradients(x, y, "mse")[1],
        trainer.model.loss_gradients(x, y, "mse")[1],
    )
    for t in (trainer, reference):
        t.step(x, y, "mse", np.ones(4, "float32"))
    for key in weights:
        np.testing.assert_allclose(trainer.weights()[key], reference.weights()[key], rtol=1e-4, atol=3e-6)
    resumed = LstmKerasTrainer(plan, weights, "gpu")
    resumed.restore_state(trainer.export_state())
    for t in (trainer, resumed):
        t.step(x, y, "mse", np.ones(4, "float32"))
    for field in ("weights", "m", "v"):
        for key in weights:
            np.testing.assert_allclose(
                trainer.export_state()[field][key], resumed.export_state()[field][key], atol=1e-6, rtol=1e-5
            )
    assert trainer.model.keras.backend.backend() == "tensorflow" and "GPU" in trainer.model.device
    with pytest.raises(ValueError):
        trainer.step(x * np.nan, y, "mse", np.ones(4, "float32"))


def test_gate_diagnostics_reset_range_and_carry_equations():
    plan, weights, x, y = fixture()
    result = gate_diagnostics(plan, weights, x, y)
    assert result["input_split"] == "train" and len(result["layers"]) == 3
    assert result["state_reset_per_window"] is True
    for layer in result["layers"]:
        assert layer["carry_equation_max_absolute_error"] < 1e-7
        assert layer["hidden_equation_max_absolute_error"] < 1e-7
        for name in ("input", "forget", "output"):
            assert 0 <= layer["gates"][name]["min"] <= layer["gates"][name]["max"] <= 1
            assert len(layer["gates"][name]["mean_by_time"]) == 5
        assert -1 <= layer["gates"]["candidate"]["min"] <= layer["gates"]["candidate"]["max"] <= 1
    network = NumpyNetwork(plan, weights)
    np.testing.assert_array_equal(network.forward(x), network.forward(x))
    np.testing.assert_allclose(network.forward(x)[:1], network.forward(x[:1]), atol=1e-7, rtol=1e-6)
    with pytest.raises(ValueError):
        gate_diagnostics(build_plan("rnn", [5, 2], 3, tiny=True), {}, x, y)


def test_lstm_fit_resume_matches_uninterrupted():
    plan, weights, x, y = fixture()

    class Data:
        train_ids = tuple("abcd")
        validation_ids = tuple("efgh")

        def batch(self, ids):
            positions = [(ord(k) - ord("a")) % 4 for k in ids]
            return x[positions], y[positions]

    budget = {
        "patience": 6,
        "min_delta": 1e-5,
        "max_epochs": 3,
        "batch_size": 2,
        "wall_time_limit_minutes": 2,
    }
    states = []
    complete = fit_windows(ScratchTrainer(plan, weights), Data(), seed=17, budget=budget)
    fit_windows(
        ScratchTrainer(plan, weights),
        Data(),
        seed=17,
        budget={**budget, "max_epochs": 1},
        progress=lambda s: states.append(copy.deepcopy(s)),
    )
    resumed = fit_windows(ScratchTrainer(plan, weights), Data(), seed=17, budget=budget, resume=states[-1])
    assert complete["history"] == resumed["history"]
    for key in weights:
        np.testing.assert_array_equal(complete["weights"][key], resumed["weights"][key])


@pytest.mark.parametrize("width,context", [(4, 24), (51, 12), (14, 168)])
def test_real_lstm_architecture_has_six_learnable_layers(width, context):
    plan = build_plan("lstm", [context, width], 3)
    contract = make_contract(plan, "scratch", "synthetic_fixture")
    assert len([s for s in plan["steps"] if s["kind"] in {"lstm", "dense"}]) == 6
    assert contract["family"] == "lstm"
    for step in plan["steps"]:
        if step["kind"] == "lstm":
            bias = canonical_weights(plan, 17)[step["id"] + "/b"]
            np.testing.assert_array_equal(bias[32:64], 1)


@pytest.mark.parametrize("trainer", [LstmTorchTrainer, LstmKerasTrainer])
def test_lstm_trainer_rejects_wrong_family_before_backend_import(trainer):
    with pytest.raises(ValueError, match="LSTM"):
        trainer(build_plan("rnn", [5, 2], 3, tiny=True), {})
