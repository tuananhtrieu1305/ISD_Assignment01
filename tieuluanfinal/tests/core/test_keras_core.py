"""Run explicitly with -Framework keras; never import PyTorch here."""

import numpy as np
import pytest

from src.common.backend_models import KerasBackend
from src.common.model_core import build_plan, canonical_weights
from src.common.native_training import NativeAdam
from src.common.numpy_engine import NumpyNetwork
from src.common.training_core import Adam, clip_gradients


@pytest.fixture(scope="module", autouse=True)
def force_cpu_process():
    import tensorflow as tf

    tf.config.set_visible_devices([], "GPU")
    tf.config.experimental.enable_tensor_float_32_execution(False)


@pytest.mark.parametrize(
    "family,shape", [("mlp", [4]), ("cnn", [8, 8, 3]), ("rnn", [4, 2]), ("lstm", [4, 2])]
)
def test_keras_cpu_reference(family, shape):
    plan = build_plan(family, shape, 2, tiny=True)
    weights = canonical_weights(plan, 42)
    for name in weights:
        if name.startswith(("dense_", "conv2d_")) and name.endswith("/b"):
            weights[name] += 0.1234
    native = KerasBackend(plan, weights, "cpu")
    reference = NumpyNetwork(plan, weights)
    x = np.random.default_rng(17).normal(size=(2, *shape)).astype("float32")
    y = np.ones((2, 2), dtype="float32")
    np.testing.assert_allclose(native.predict(x), reference.forward(x), rtol=1e-4, atol=1e-5)
    loss, gradient, _ = reference.loss_gradients(x, y, "mse")
    observed, actual = native.loss_gradients(x, y, "mse")
    assert abs(loss - observed) < 1e-5
    assert native.parameter_count == sum(value.size for value in weights.values())
    for name in gradient:
        np.testing.assert_allclose(actual[name], gradient[name], rtol=1e-3, atol=1e-6)
    assert native.trace(x)[-1]["output_shape"] == [2, 2]
    numpy_optimizer = Adam(reference.weights)
    native_optimizer = NativeAdam(native)
    gradient, _ = clip_gradients(gradient)
    numpy_optimizer.step(reference.weights, gradient)
    native_optimizer.step(x, y, "mse")
    for name, value in native_optimizer.weights().items():
        np.testing.assert_allclose(value, reference.weights[name], rtol=1e-4, atol=2e-6)


@pytest.mark.parametrize("task,outputs", [("binary", 1), ("multiclass", 3)])
def test_keras_classification_losses(task, outputs):
    plan = build_plan("mlp", [2], outputs, tiny=True)
    weights = canonical_weights(plan, 42)
    native = KerasBackend(plan, weights, "cpu")
    reference = NumpyNetwork(plan, weights)
    x = np.array([[0.1, 0.2], [0.3, 0.4]], dtype="float32")
    y = np.array([[0.0], [1.0]], dtype="float32") if task == "binary" else np.array([0, 2])
    loss, grad, _ = reference.loss_gradients(x, y, task)
    actual_loss, actual_grad = native.loss_gradients(x, y, task)
    assert abs(loss - actual_loss) < 1e-5
    for name in grad:
        np.testing.assert_allclose(actual_grad[name], grad[name], rtol=1e-3, atol=1e-6)
    result = NativeAdam(native).step(x, y, task, sample_weight=[1.0, 2.0])
    assert np.isfinite(result["loss"])
    with pytest.raises(ValueError):
        NativeAdam(native).step(x, y, "bad")
    with pytest.raises(ValueError):
        NativeAdam(native).step(x, y, task, sample_weight=[-1, 2])
    with pytest.raises(ValueError):
        native.loss_gradients(x, y, "bad")
