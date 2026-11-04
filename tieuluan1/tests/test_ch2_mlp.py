import tempfile
import unittest
from pathlib import Path

import numpy as np

from term_paper.src.keras_impl.mlp import KerasMLP
from term_paper.src.pytorch_impl.mlp import TorchMLP
from term_paper.src.scratch.mlp import NumpyMLP


def binary_toy(seed=42):
    rng = np.random.default_rng(seed)
    negative = rng.normal(loc=-1.0, scale=0.35, size=(48, 4))
    positive = rng.normal(loc=1.0, scale=0.35, size=(48, 4))
    x = np.vstack([negative, positive]).astype(np.float32)
    y = np.concatenate([np.zeros(48), np.ones(48)]).astype(np.float32)
    order = rng.permutation(len(x))
    return x[order[:72]], y[order[:72]], x[order[72:]], y[order[72:]]


def regression_toy(seed=42):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(96, 3)).astype(np.float32)
    y = (1.5 * x[:, 0] - 0.7 * x[:, 1] + 0.2 * x[:, 2]).astype(np.float32)
    return x[:72], y[:72], x[72:], y[72:]


class NumpyMLPTests(unittest.TestCase):
    def test_forward_shape_and_probability_range(self):
        x_train, _, _, _ = binary_toy()
        model = NumpyMLP(4, task="binary", hidden=(8, 4), seed=42)
        score = model.predict_score(x_train[:7])
        self.assertEqual(score.shape, (7,))
        self.assertTrue(np.isfinite(score).all())
        self.assertTrue(((score >= 0.0) & (score <= 1.0)).all())

    def test_binary_loss_decreases_on_toy_data(self):
        x_train, y_train, x_val, y_val = binary_toy()
        model = NumpyMLP(4, task="binary", hidden=(8, 4), seed=42, learning_rate=0.01)
        history = model.fit(
            x_train,
            y_train,
            x_val,
            y_val,
            epochs=80,
            batch_size=16,
            patience=20,
        )
        self.assertLess(history["train_loss"][-1], history["train_loss"][0])
        self.assertGreater(np.mean((model.predict_score(x_val) >= 0.5) == y_val), 0.9)

    def test_regression_loss_decreases_on_toy_data(self):
        x_train, y_train, x_val, y_val = regression_toy()
        model = NumpyMLP(3, task="regression", hidden=(8, 4), seed=42, learning_rate=0.01)
        history = model.fit(
            x_train,
            y_train,
            x_val,
            y_val,
            epochs=120,
            batch_size=16,
            patience=25,
        )
        self.assertLess(history["val_loss"][-1], history["val_loss"][0])
        self.assertLess(np.mean((model.predict_score(x_val) - y_val) ** 2), 0.08)

    def test_numerical_gradient_matches_backpropagation(self):
        x_train, y_train, _, _ = binary_toy()
        model = NumpyMLP(4, task="binary", hidden=(5, 3), seed=42, learning_rate=0.01)
        _, gradients = model.loss_and_gradients(x_train[:8], y_train[:8])
        key = "W3"
        index = (1, 0)
        original = float(model.params[key][index])
        epsilon = 1e-5
        model.params[key][index] = original + epsilon
        loss_plus, _ = model.loss_and_gradients(x_train[:8], y_train[:8])
        model.params[key][index] = original - epsilon
        loss_minus, _ = model.loss_and_gradients(x_train[:8], y_train[:8])
        model.params[key][index] = original
        numerical = (loss_plus - loss_minus) / (2 * epsilon)
        self.assertAlmostEqual(float(gradients[key][index]), float(numerical), places=4)

    def test_save_load_prediction_parity(self):
        x_train, y_train, x_val, y_val = binary_toy()
        model = NumpyMLP(4, task="binary", hidden=(8, 4), seed=42)
        model.fit(x_train, y_train, x_val, y_val, epochs=20, batch_size=16, patience=5)
        expected = model.predict_score(x_val)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.npz"
            model.save(path)
            actual = NumpyMLP.load(path).predict_score(x_val)
        np.testing.assert_allclose(expected, actual, atol=1e-7, rtol=0)


class FrameworkMLPTests(unittest.TestCase):
    def _exercise_binary_model(self, model_class, suffix):
        x_train, y_train, x_val, y_val = binary_toy()
        model = model_class(4, task="binary", hidden=(8, 4), seed=42, learning_rate=0.01)
        history = model.fit(
            x_train,
            y_train,
            x_val,
            y_val,
            epochs=30,
            batch_size=16,
            patience=10,
        )
        score = model.predict_score(x_val)
        self.assertEqual(score.shape, (24,))
        self.assertTrue(np.isfinite(score).all())
        self.assertLess(history["val_loss"][-1], history["val_loss"][0])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"model{suffix}"
            model.save(path)
            loaded = model_class.load(path)
            np.testing.assert_allclose(score, loaded.predict_score(x_val), atol=1e-6, rtol=0)

    def test_keras_train_infer_and_save_load(self):
        self._exercise_binary_model(KerasMLP, ".keras")

    def test_pytorch_train_infer_and_save_load(self):
        self._exercise_binary_model(TorchMLP, ".pt")

    def test_parameter_count_matches_across_frameworks(self):
        models = [
            NumpyMLP(6, task="binary", hidden=(8, 4), seed=42),
            KerasMLP(6, task="binary", hidden=(8, 4), seed=42),
            TorchMLP(6, task="binary", hidden=(8, 4), seed=42),
        ]
        counts = [model.parameter_count for model in models]
        self.assertEqual(counts, [counts[0]] * 3)
        self.assertEqual(counts[0], (6 * 8 + 8) + (8 * 4 + 4) + (4 * 1 + 1))


if __name__ == "__main__":
    unittest.main()

