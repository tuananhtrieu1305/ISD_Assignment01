"""Phase27 RED: CNN optimizer slots must round-trip HWIO, not ndarray.T."""

import numpy as np
import pytest

from src.ch03_cnn.training import CnnKerasTrainer, CnnScratchTrainer, CnnTorchTrainer, probabilities
from src.common.model_core import build_plan, canonical_weights


def fixture():
    plan = build_plan("cnn", [8, 8, 3], 3, tiny=True)
    weights = canonical_weights(plan, 17)
    x = np.random.default_rng(5).uniform(0.1, 0.9, (2, 8, 8, 3)).astype("float32")
    return plan, weights, x, np.asarray([0, 2], dtype="int64"), np.asarray([1, 2], dtype="float32")


@pytest.mark.parametrize("implementation", ["scratch", "pytorch"])
def test_resume_matches_continuous(implementation):
    plan, weights, x, y, sample_weight = fixture()
    cls = CnnScratchTrainer if implementation == "scratch" else CnnTorchTrainer
    a = cls(plan, weights)
    a.step(x, y, "multiclass", sample_weight)
    state = a.export_state()
    b = cls(plan, weights)
    b.restore_state(state)
    a.step(x, y, "multiclass", sample_weight)
    b.step(x, y, "multiclass", sample_weight)
    for key in weights:
        np.testing.assert_allclose(a.weights()[key], b.weights()[key], rtol=1e-6, atol=1e-7)
    assert a.iterations == b.iterations == 2


def test_multiclass_probabilities():
    p = probabilities(np.asarray([[1000, 1001, 1002]], dtype="float32"))
    assert p.dtype == np.float32
    np.testing.assert_allclose(p.sum(axis=1), 1)
    with pytest.raises(ValueError):
        probabilities(np.asarray([[np.nan, 0]]))


def test_torch_step_parity_with_scratch():
    plan, weights, x, y, sample_weight = fixture()
    a, b = CnnScratchTrainer(plan, weights), CnnTorchTrainer(plan, weights)
    np.testing.assert_allclose(a.predict(x), b.predict(x), atol=1e-5, rtol=1e-4)
    la = a.step(x, y, "multiclass", sample_weight)
    lb = b.step(x, y, "multiclass", sample_weight)
    assert abs(la["loss"] - lb["loss"]) < 1e-5
    for key in weights:
        np.testing.assert_allclose(a.weights()[key], b.weights()[key], atol=3e-6, rtol=1e-3)


def test_keras_gpu_resume_and_scratch_parity():
    # Selected explicitly in Keras env; no torch import on this path.
    plan, weights, x, y, sample_weight = fixture()
    a, b = CnnScratchTrainer(plan, weights), CnnKerasTrainer(plan, weights, "gpu")
    np.testing.assert_allclose(a.predict(x), b.predict(x), atol=1e-5, rtol=1e-4)
    a.step(x, y, "multiclass", sample_weight)
    b.step(x, y, "multiclass", sample_weight)
    for key in weights:
        np.testing.assert_allclose(a.weights()[key], b.weights()[key], atol=3e-6, rtol=1e-3)
    c = CnnKerasTrainer(plan, weights, "gpu")
    c.restore_state(b.export_state())
    b.step(x, y, "multiclass", sample_weight)
    c.step(x, y, "multiclass", sample_weight)
    for key in weights:
        np.testing.assert_array_equal(b.weights()[key], c.weights()[key])
    assert c.iterations == 2
