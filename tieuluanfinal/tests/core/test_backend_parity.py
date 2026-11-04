"""Torch adapter must match NumPy canonical IO/HWIO/i-f-g-o weights."""

import numpy as np
import pytest

from src.common.backend_models import TorchBackend
from src.common.model_core import build_plan, canonical_weights
from src.common.numpy_engine import NumpyNetwork


@pytest.mark.parametrize(
    "family,shape", [("mlp", [4]), ("cnn", [8, 8, 3]), ("rnn", [3, 2]), ("lstm", [3, 2])]
)
def test_torch_cpu_forward_gradient_and_count(family, shape):
    plan = build_plan(family, shape, 2)
    weights = canonical_weights(plan, 42)
    rng = np.random.default_rng(73)
    x = rng.normal(size=(2, *shape)).astype("float32")
    y = rng.normal(size=(2, 2)).astype("float32")
    numpy = NumpyNetwork(plan, weights)
    backend = TorchBackend(plan, weights, "cpu")
    expected = numpy.forward(x)
    np.testing.assert_allclose(backend.predict(x), expected, rtol=1e-4, atol=1e-5)
    nloss, ngrad, _ = numpy.loss_gradients(x, y, "mse")
    loss, grad = backend.loss_gradients(x, y, "mse")
    assert abs(nloss - loss) < 1e-5
    assert backend.parameter_count == sum(v.size for v in weights.values())
    for key in grad:
        np.testing.assert_allclose(grad[key], ngrad[key], rtol=1e-3, atol=1e-6, err_msg=key)
    backend.assign(weights)
    np.testing.assert_allclose(backend.predict(x), expected, rtol=1e-4, atol=1e-5)
    assert backend.trace(x)[-1]["output_shape"] == [2, 2]
