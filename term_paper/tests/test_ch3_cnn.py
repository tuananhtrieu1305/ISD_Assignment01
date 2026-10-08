import tempfile
import unittest
from pathlib import Path

import numpy as np

from term_paper.src.keras_impl.cnn import KerasCNN
from term_paper.src.pytorch_impl.cnn import TorchCNN
from term_paper.src.scratch.cnn import NumpyCNN


def image_toy(seed=42):
    """Three easy image classes: vertical, horizontal and diagonal bars."""
    rng = np.random.default_rng(seed)
    images = []
    labels = []
    for label in range(3):
        for _ in range(18):
            image = rng.normal(0.0, 0.03, size=(8, 8, 1))
            if label == 0:
                image[:, 1:3, 0] += 1.0
            elif label == 1:
                image[5:7, :, 0] += 1.0
            else:
                image[np.arange(8), np.arange(8), 0] += 1.0
            images.append(image)
            labels.append(label)
    order = rng.permutation(len(images))
    x = np.asarray(images, dtype=np.float32)[order]
    y = np.asarray(labels, dtype=np.int64)[order]
    return x[:42], y[:42], x[42:], y[42:]


def sequence_toy(seed=42):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(15, 9, 1)).astype(np.float32)
    y = np.argmax(
        np.stack([x[:, :3].mean((1, 2)), x[:, 3:6].mean((1, 2)), x[:, 6:].mean((1, 2))], axis=1),
        axis=1,
    ).astype(np.int64)
    return x, y


class NumpyCNNTests(unittest.TestCase):
    def test_conv2d_forward_shape_probability_and_parameter_count(self):
        model = NumpyCNN((8, 8, 1), 3, mode="2d", filters=(4, 5), seed=42)
        score = model.predict_proba(np.zeros((7, 8, 8, 1), dtype=np.float32))
        self.assertEqual(score.shape, (7, 3))
        self.assertTrue(np.isfinite(score).all())
        np.testing.assert_allclose(score.sum(axis=1), 1.0, atol=1e-7)
        self.assertEqual(model.parameter_count, (3 * 3 * 1 * 4 + 4) + (3 * 3 * 4 * 5 + 5) + (5 * 3 + 3))

    def test_conv1d_forward_shape_probability(self):
        x, _ = sequence_toy()
        model = NumpyCNN((9, 1), 3, mode="1d", filters=(4, 5), seed=42)
        score = model.predict_proba(x)
        self.assertEqual(score.shape, (15, 3))
        np.testing.assert_allclose(score.sum(axis=1), 1.0, atol=1e-7)

    def test_conv2d_numerical_gradient_matches_backpropagation(self):
        x, y, _, _ = image_toy()
        model = NumpyCNN((8, 8, 1), 3, mode="2d", filters=(2, 2), seed=42)
        loss, gradients = model.loss_and_gradients(x[:3], y[:3])
        self.assertTrue(np.isfinite(loss))
        key, index, epsilon = "W1", (1, 1, 0, 0), 1e-5
        original = float(model.params[key][index])
        model.params[key][index] = original + epsilon
        plus, _ = model.loss_and_gradients(x[:3], y[:3])
        model.params[key][index] = original - epsilon
        minus, _ = model.loss_and_gradients(x[:3], y[:3])
        model.params[key][index] = original
        numerical = (plus - minus) / (2 * epsilon)
        self.assertAlmostEqual(float(gradients[key][index]), float(numerical), places=4)

    def test_conv1d_numerical_gradient_matches_backpropagation(self):
        x, y = sequence_toy()
        model = NumpyCNN((9, 1), 3, mode="1d", filters=(2, 2), seed=42)
        _, gradients = model.loss_and_gradients(x[:4], y[:4])
        key, index, epsilon = "W2", (1, 0, 1), 1e-5
        original = float(model.params[key][index])
        model.params[key][index] = original + epsilon
        plus, _ = model.loss_and_gradients(x[:4], y[:4])
        model.params[key][index] = original - epsilon
        minus, _ = model.loss_and_gradients(x[:4], y[:4])
        model.params[key][index] = original
        numerical = (plus - minus) / (2 * epsilon)
        self.assertAlmostEqual(float(gradients[key][index]), float(numerical), places=4)

    def test_toy_loss_decreases_and_model_overfits(self):
        x_train, y_train, x_val, y_val = image_toy()
        model = NumpyCNN(
            (8, 8, 1), 3, mode="2d", filters=(4, 6), seed=42, learning_rate=0.02
        )
        history = model.fit(
            x_train, y_train, x_val, y_val, epochs=80, batch_size=14, patience=20
        )
        self.assertLess(history["train_loss"][-1], history["train_loss"][0])
        self.assertGreaterEqual(np.mean(model.predict(x_train) == y_train), 0.95)

    def test_save_load_prediction_parity(self):
        x_train, y_train, x_val, y_val = image_toy()
        model = NumpyCNN((8, 8, 1), 3, mode="2d", filters=(3, 4), seed=42)
        model.fit(x_train, y_train, x_val, y_val, epochs=4, batch_size=14, patience=2)
        expected = model.predict_proba(x_val)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cnn.npz"
            model.save(path)
            actual = NumpyCNN.load(path).predict_proba(x_val)
        np.testing.assert_allclose(expected, actual, atol=1e-7, rtol=0)


class FrameworkCNNTests(unittest.TestCase):
    def _exercise(self, model_class, suffix):
        x_train, y_train, x_val, y_val = image_toy()
        model = model_class(
            (8, 8, 1), 3, mode="2d", filters=(4, 5), seed=42, learning_rate=0.01
        )
        history = model.fit(
            x_train, y_train, x_val, y_val, epochs=12, batch_size=14, patience=5
        )
        score = model.predict_proba(x_val)
        self.assertEqual(score.shape, (12, 3))
        self.assertTrue(np.isfinite(score).all())
        self.assertLess(history["train_loss"][-1], history["train_loss"][0])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"cnn{suffix}"
            model.save(path)
            loaded = model_class.load(path)
            np.testing.assert_allclose(score, loaded.predict_proba(x_val), atol=1e-6, rtol=0)

    def test_keras_train_infer_and_save_load(self):
        self._exercise(KerasCNN, ".keras")

    def test_pytorch_train_infer_and_save_load(self):
        self._exercise(TorchCNN, ".pt")

    def test_parameter_count_matches_for_2d_and_1d(self):
        for input_shape, mode in [((8, 8, 1), "2d"), ((9, 1), "1d")]:
            models = [
                NumpyCNN(input_shape, 3, mode=mode, filters=(4, 5), seed=42),
                KerasCNN(input_shape, 3, mode=mode, filters=(4, 5), seed=42),
                TorchCNN(input_shape, 3, mode=mode, filters=(4, 5), seed=42),
            ]
            counts = [model.parameter_count for model in models]
            self.assertEqual(counts, [counts[0]] * 3)


if __name__ == "__main__":
    unittest.main()
