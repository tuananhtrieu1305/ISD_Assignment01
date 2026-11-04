import tempfile
import unittest
from pathlib import Path

import numpy as np

from term_paper.src.keras_impl.rnn import KerasRNN
from term_paper.src.pytorch_impl.rnn import TorchRNN
from term_paper.src.scratch.rnn import NumpyRNN, clip_gradients


def binary_sequence_toy(seed=42):
    rng = np.random.default_rng(seed)
    negative = rng.normal(-0.8, 0.15, size=(48, 5, 2))
    positive = rng.normal(0.8, 0.15, size=(48, 5, 2))
    x = np.concatenate([negative, positive]).astype(np.float32)
    y = np.concatenate([np.zeros(48), np.ones(48)]).astype(np.float32)
    order = rng.permutation(len(x))
    return x[order[:72]], y[order[:72]], x[order[72:]], y[order[72:]]


def regression_sequence_toy(seed=42):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(96, 4, 2)).astype(np.float32)
    y = (0.8 * x[:, -1, 0] - 0.4 * x[:, -2, 1]).astype(np.float32)
    return x[:72], y[:72], x[72:], y[72:]


class GradientClipTests(unittest.TestCase):
    def test_global_norm_is_clipped_without_changing_direction(self):
        gradients = {
            "a": np.asarray([3.0, 4.0]),
            "b": np.asarray([0.0, 12.0]),
        }
        clipped, original_norm = clip_gradients(gradients, max_norm=1.0)
        self.assertAlmostEqual(original_norm, 13.0)
        final_norm = np.sqrt(sum(np.sum(value**2) for value in clipped.values()))
        self.assertLessEqual(final_norm, 1.000001)
        np.testing.assert_allclose(clipped["a"] / clipped["a"][0], gradients["a"] / 3.0)


class NumpyRNNTests(unittest.TestCase):
    def test_forward_shape_and_probability_range(self):
        x_train, _, _, _ = binary_sequence_toy()
        model = NumpyRNN(2, hidden_size=6, task="binary", seed=42)
        score = model.predict_score(x_train[:7])
        self.assertEqual(score.shape, (7,))
        self.assertTrue(np.isfinite(score).all())
        self.assertTrue(((score >= 0.0) & (score <= 1.0)).all())

    def test_parameter_count_formula(self):
        model = NumpyRNN(5, hidden_size=32, task="binary", seed=42)
        self.assertEqual(model.parameter_count, (5 * 32) + (32 * 32) + 32 + 32 + 1)

    def test_bptt_numerical_gradient_matches(self):
        x_train, y_train, _, _ = binary_sequence_toy()
        model = NumpyRNN(2, hidden_size=4, task="binary", seed=42)
        _, gradients = model.loss_and_gradients(x_train[:5], y_train[:5])
        key, index, epsilon = "Whh", (1, 2), 1e-5
        original = float(model.params[key][index])
        model.params[key][index] = original + epsilon
        plus, _ = model.loss_and_gradients(x_train[:5], y_train[:5])
        model.params[key][index] = original - epsilon
        minus, _ = model.loss_and_gradients(x_train[:5], y_train[:5])
        model.params[key][index] = original
        numerical = (plus - minus) / (2 * epsilon)
        self.assertAlmostEqual(float(gradients[key][index]), float(numerical), places=4)

    def test_bptt_gradient_clipping_applies_to_computed_gradients(self):
        x_train, y_train, _, _ = binary_sequence_toy()
        model = NumpyRNN(2, hidden_size=5, task="binary", seed=42)
        _, gradients = model.loss_and_gradients(
            x_train * 100.0, y_train, clip_norm=0.05
        )
        norm = np.sqrt(sum(np.sum(value**2) for value in gradients.values()))
        self.assertLessEqual(norm, 0.050001)

    def test_toy_binary_overfit(self):
        x_train, y_train, x_val, y_val = binary_sequence_toy()
        model = NumpyRNN(2, hidden_size=8, task="binary", seed=42, learning_rate=0.01)
        history = model.fit(
            x_train, y_train, x_val, y_val, epochs=60, batch_size=16, patience=15
        )
        self.assertLess(history["train_loss"][-1], history["train_loss"][0])
        self.assertGreater(np.mean((model.predict_score(x_train) >= 0.5) == y_train), 0.95)

    def test_regression_loss_decreases(self):
        x_train, y_train, x_val, y_val = regression_sequence_toy()
        model = NumpyRNN(2, hidden_size=10, task="regression", seed=42, learning_rate=0.01)
        history = model.fit(
            x_train, y_train, x_val, y_val, epochs=100, batch_size=16, patience=20
        )
        self.assertLess(history["val_loss"][-1], history["val_loss"][0])
        self.assertLess(np.mean((model.predict_score(x_val) - y_val) ** 2), 0.15)

    def test_save_load_prediction_parity(self):
        x_train, y_train, x_val, y_val = binary_sequence_toy()
        model = NumpyRNN(2, hidden_size=6, task="binary", seed=42)
        model.fit(x_train, y_train, x_val, y_val, epochs=10, batch_size=16, patience=4)
        expected = model.predict_score(x_val)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rnn.npz"
            model.save(path)
            actual = NumpyRNN.load(path).predict_score(x_val)
        np.testing.assert_allclose(expected, actual, atol=1e-7, rtol=0)


class FrameworkRNNTests(unittest.TestCase):
    def _exercise(self, model_class, suffix):
        x_train, y_train, x_val, y_val = binary_sequence_toy()
        model = model_class(2, hidden_size=8, task="binary", seed=42, learning_rate=0.01)
        history = model.fit(
            x_train, y_train, x_val, y_val, epochs=25, batch_size=16, patience=8
        )
        score = model.predict_score(x_val)
        self.assertEqual(score.shape, (24,))
        self.assertTrue(np.isfinite(score).all())
        self.assertLess(history["train_loss"][-1], history["train_loss"][0])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"rnn{suffix}"
            model.save(path)
            loaded = model_class.load(path)
            np.testing.assert_allclose(score, loaded.predict_score(x_val), atol=1e-6, rtol=0)

    def test_keras_train_infer_and_save_load(self):
        self._exercise(KerasRNN, ".keras")

    def test_pytorch_train_infer_and_save_load(self):
        self._exercise(TorchRNN, ".pt")

    def test_trainable_parameter_count_matches(self):
        models = [
            NumpyRNN(5, hidden_size=32, task="binary", seed=42),
            KerasRNN(5, hidden_size=32, task="binary", seed=42),
            TorchRNN(5, hidden_size=32, task="binary", seed=42),
        ]
        counts = [model.parameter_count for model in models]
        self.assertEqual(counts, [1249, 1249, 1249])


if __name__ == "__main__":
    unittest.main()
