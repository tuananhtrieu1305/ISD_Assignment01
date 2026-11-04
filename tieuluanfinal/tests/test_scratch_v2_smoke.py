"""Migration smoke checks that need NumPy but no TensorFlow/PyTorch installation."""

import numpy as np
import pytest

from term_paper.src.scratch.cnn import NumpyCNN
from term_paper.src.scratch.mlp import NumpyMLP
from term_paper.src.scratch.rnn import NumpyRNN


@pytest.mark.parametrize("family", ("mlp", "cnn", "rnn"))
def test_migrated_scratch_forward_backward_and_checkpoint_roundtrip(family, tmp_path):
    rng = np.random.default_rng(42)
    if family == "mlp":
        model = NumpyMLP(4, task="binary", hidden=(8, 4))
        inputs = rng.normal(size=(6, 4))
        targets = np.array([0, 1, 0, 1, 0, 1], dtype=float)
        predict = lambda candidate: candidate.predict_score(inputs)
    elif family == "cnn":
        model = NumpyCNN((8, 8, 1), 3, filters=(2, 2))
        inputs = rng.normal(size=(6, 8, 8, 1))
        targets = np.array([0, 1, 2, 0, 1, 2])
        predict = lambda candidate: candidate.predict_proba(inputs)
    else:
        model = NumpyRNN(2, hidden_size=4)
        inputs = rng.normal(size=(6, 5, 2))
        targets = np.array([0, 1, 0, 1, 0, 1], dtype=float)
        predict = lambda candidate: candidate.predict_score(inputs)

    loss, gradients = model.loss_and_gradients(inputs, targets)
    assert np.isfinite(loss)
    assert gradients and all(np.isfinite(value).all() for value in gradients.values())
    expected = predict(model)
    path = tmp_path / f"{family}.npz"
    model.save(path)
    actual = predict(type(model).load(path))
    assert np.isfinite(actual).all()
    np.testing.assert_allclose(actual, expected, atol=1e-7, rtol=0)
