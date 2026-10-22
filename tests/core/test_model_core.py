"""TDD model registry/shape/function and NumPy differentiation contracts."""

import copy

import numpy as np
import pytest

from src.common.model_core import (
    ModelRegistry,
    build_plan,
    canonical_weights,
    make_contract,
    render_functions,
    validate_model,
)
from src.common.numpy_engine import NumpyNetwork, loss_and_gradient, numerical_gradient


@pytest.mark.parametrize(
    "family,shape,outputs,layers",
    [("mlp", [4], 2, 6), ("cnn", [8, 8, 3], 3, 7), ("rnn", [3, 2], 3, 6), ("lstm", [3, 2], 3, 6)],
)
def test_plan_contract_counts(family, shape, outputs, layers):
    plan = build_plan(family, shape, outputs)
    weights = canonical_weights(plan, 42)
    contract = make_contract(plan, "scratch", "synthetic_fixture")
    assert len([x for x in contract["layers"] if x["parameter_count"]]) == layers
    assert contract["parameter_count"] == sum(x.size for x in weights.values())
    docs = render_functions(contract)
    assert "F = " in docs["technical"] and "→" in docs["plain"]
    assert len(docs["functions"]) == len(plan["steps"])
    model = NumpyNetwork(plan, weights)
    rng = np.random.default_rng(17)
    output, trace = model.forward(rng.normal(size=(2, *shape)).astype("float32"), trace=True)
    assert list(output.shape) == [2, outputs]
    assert len(trace) == len(plan["steps"])
    for row, step in zip(trace, plan["steps"], strict=True):
        assert row["output_shape"] == [2, *step["output_shape"]]


def test_contract_rejects_forged_shapes_and_layers():
    original = make_contract(build_plan("mlp", [4], 1), "scratch", "synthetic_fixture")
    for kind in ["count", "shape", "functions", "composition", "parameters"]:
        value = copy.deepcopy(original)
        if kind == "count":
            value["layers"][0]["parameter_count"] = 0
        if kind == "shape":
            value["layers"][1]["input_shape"] = ["batch", 999]
        if kind == "functions":
            value["functions"][0]["parameters"] += 1
        if kind == "composition":
            value["composition"] = list(reversed(value["composition"]))
        if kind == "parameters":
            value["parameter_count"] += 1
        with pytest.raises(ValueError):
            validate_model(value)
    registry = ModelRegistry()
    registry.register(original)
    assert registry.get(original["model_id"]) == original
    with pytest.raises(ValueError):
        registry.register(original)
    with pytest.raises(KeyError):
        registry.get("absent")
    with pytest.raises(ValueError):
        build_plan("bad", [4], 1)


@pytest.mark.parametrize(
    "family,shape", [("mlp", [2]), ("cnn", [4, 4, 1]), ("rnn", [3, 2]), ("lstm", [3, 2])]
)
def test_numerical_gradient_tiny(family, shape):
    plan = build_plan(family, shape, 1, tiny=True)
    model = NumpyNetwork(plan, canonical_weights(plan, 17, dtype="float64"))
    # Avoid ReLU's nondifferentiable zero in finite-difference fixtures.
    # This does not change canonical production initialization.
    for name, value in model.weights.items():
        if name.endswith("/b") and not name.startswith(("rnn_", "lstm_")):
            value += 0.1234
    rng = np.random.default_rng(73)
    x = rng.normal(size=(2, *shape))
    y = rng.normal(size=(2, 1))
    loss, grads, dx = model.loss_gradients(x, y, "mse")
    assert np.isfinite(loss) and dx.shape == x.shape
    for name, value in model.weights.items():
        numeric = numerical_gradient(lambda: model.loss_gradients(x, y, "mse")[0], value)
        np.testing.assert_allclose(grads[name], numeric, atol=2e-7, rtol=1e-3, err_msg=name)


@pytest.mark.parametrize("task", ["mse", "binary", "multiclass"])
def test_loss_derivatives(task):
    values = (
        np.array([[0.2, -0.4], [0.8, 0.3]], dtype=float)
        if task == "multiclass"
        else np.array([[0.2], [0.8]], dtype=float)
    )
    target = np.array([0, 1]) if task == "multiclass" else np.array([[0.0], [1.0]])
    loss, gradient = loss_and_gradient(values, target, task)
    np.testing.assert_allclose(
        gradient, numerical_gradient(lambda: loss_and_gradient(values, target, task)[0], values), atol=1e-8
    )
    assert np.isfinite(loss)
