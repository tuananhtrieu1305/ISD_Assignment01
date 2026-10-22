import numpy as np
import pytest

from src.common.backend_models import TorchBackend
from src.common.model_core import build_plan, canonical_weights
from src.common.native_training import NativeAdam
from src.common.numpy_engine import NumpyNetwork
from src.common.training_core import Adam, clip_gradients


def test_checkpoint_minimum_is_separate_from_patience_min_delta():
    from src.common.training_core import EarlyStopping

    stop = EarlyStopping(patience=2, min_delta=1e-5)
    assert stop.observe(1.0, 0) == (True, False)
    assert stop.observe(0.999999, 1) == (True, False)
    assert stop.observe(0.999998, 2) == (True, True)
    assert stop.best_epoch == 2


def test_native_update_matches_canonical_adam():
    plan = build_plan("rnn", [3, 2], 2, tiny=True)
    weights = canonical_weights(plan, 73)
    for name in weights:
        if name.startswith("dense_") and name.endswith("/b"):
            weights[name] += 0.1
    numpy = NumpyNetwork(plan, weights)
    native = TorchBackend(plan, weights, "cpu")
    optimizer = Adam(numpy.weights)
    native_optimizer = NativeAdam(native)
    x = np.random.default_rng(42).normal(size=(2, 3, 2)).astype("float32")
    y = np.ones((2, 2), dtype="float32")
    for _ in range(3):
        loss, grad, _ = numpy.loss_gradients(x, y, "mse")
        grad, _ = clip_gradients(grad)
        optimizer.step(numpy.weights, grad)
        observed = native_optimizer.step(x, y, "mse")
        assert abs(observed["loss"] - loss) < 1e-5
        actual = native_optimizer.weights()
        for name in actual:
            np.testing.assert_allclose(actual[name], numpy.weights[name], atol=2e-6, rtol=1e-4)
    with pytest.raises(ValueError):
        native_optimizer.step(x, y, "bad")
