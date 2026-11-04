"""CPU/NumPy compatibility only; legacy architecture is NOT V3 depth acceptance."""

import numpy as np
import pytest

from src.term_paper.src.scratch.cnn import NumpyCNN
from src.term_paper.src.scratch.mlp import NumpyMLP
from src.term_paper.src.scratch.rnn import NumpyRNN


@pytest.mark.parametrize("kind", ["mlp", "cnn", "rnn"])
def test_scratch_backward_update_and_checkpoint(kind, tmp_path):
    rng = np.random.default_rng(42)
    if kind == "mlp":
        model = NumpyMLP(4, "binary", hidden=(4, 3))
        x = rng.normal(size=(4, 4))
    elif kind == "cnn":
        model = NumpyCNN((8, 8, 1), 2, filters=(2, 2))
        x = rng.normal(size=(4, 8, 8, 1))
    else:
        model = NumpyRNN(2, hidden_size=3)
        x = rng.normal(size=(4, 5, 2))
    y = np.array([0, 1, 0, 1])
    before = {name: value.copy() for name, value in model.params.items()}
    loss, gradients = model.loss_and_gradients(x, y)
    assert np.isfinite(loss)
    assert gradients.keys() == model.params.keys()
    for name, gradient in gradients.items():
        assert gradient.shape == model.params[name].shape
        assert np.isfinite(gradient).all()
        model.params[name] -= 0.01 * gradient
    assert any(not np.array_equal(before[name], value) for name, value in model.params.items())
    checkpoint = tmp_path / f"{kind}.npz"
    model.save(checkpoint)
    restored = type(model).load(checkpoint)
    np.testing.assert_allclose(model._forward(x)[0], restored._forward(x)[0], rtol=0, atol=0)
