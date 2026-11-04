"""Shared synthetic checks, executed separately in the two locked environments."""

import numpy as np

from src.ch02_ml.training import ScratchTrainer
from src.common.model_core import build_plan, canonical_weights


def check_native(factory, device, task):
    plan = build_plan("mlp", [2], 1, tiny=True)
    weights = canonical_weights(plan, 17)
    rng = np.random.default_rng(42)
    x = rng.normal(size=(8, 2)).astype("float32")
    y = (x[:, :1] > 0).astype("float32") if task == "binary" else x[:, :1]
    sample_weight = np.arange(1, 9, dtype="float32")
    reference = ScratchTrainer(plan, weights)
    native = factory(plan, weights, device)
    for _ in range(3):
        a = reference.step(x, y, task, sample_weight)
        b = native.step(x, y, task, sample_weight)
        np.testing.assert_allclose(a["loss"], b["loss"], rtol=1e-4, atol=1e-6)
    for key, value in reference.weights().items():
        np.testing.assert_allclose(value, native.weights()[key], rtol=1e-4, atol=2e-6)
    resumed = factory(plan, weights, device)
    resumed.restore_state(native.export_state())
    for trainer in (native, resumed):
        trainer.step(x, y, task, sample_weight)
    for key, value in native.weights().items():
        np.testing.assert_array_equal(value, resumed.weights()[key])
    assert resumed.iterations == native.iterations == 4
    return native
