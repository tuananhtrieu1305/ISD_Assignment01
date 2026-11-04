"""Small matched CNN implemented from first principles with NumPy.

Inputs use channels-last layout: ``(N, H, W, C)`` for Conv2D and
``(N, L, C)`` for Conv1D.  The network is intentionally fixed to two
same-padded convolutions, one max-pool, global average pooling and a dense
softmax head so its parameterization can be matched exactly in Keras/PyTorch.
"""

import json
from pathlib import Path

import numpy as np


def _conv2d_forward(x, weight, bias):
    kernel_h, kernel_w = weight.shape[:2]
    if kernel_h % 2 == 0 or kernel_w % 2 == 0:
        raise ValueError("same padding requires odd kernels")
    pad_h, pad_w = kernel_h // 2, kernel_w // 2
    padded = np.pad(x, ((0, 0), (pad_h, pad_h), (pad_w, pad_w), (0, 0)))
    windows = np.lib.stride_tricks.sliding_window_view(
        padded, (kernel_h, kernel_w), axis=(1, 2)
    ).transpose(0, 1, 2, 4, 5, 3)
    output = np.tensordot(windows, weight, axes=([3, 4, 5], [0, 1, 2])) + bias
    return output, (x.shape, padded, windows, weight)


def _conv2d_backward(gradient, cache):
    input_shape, padded, windows, weight = cache
    kernel_h, kernel_w = weight.shape[:2]
    grad_weight = np.einsum("nhwklc,nhwo->klco", windows, gradient)
    grad_bias = gradient.sum(axis=(0, 1, 2))
    grad_padded = np.zeros_like(padded)
    height, width = gradient.shape[1:3]
    for row in range(kernel_h):
        for column in range(kernel_w):
            grad_padded[:, row : row + height, column : column + width, :] += np.einsum(
                "nhwo,co->nhwc", gradient, weight[row, column]
            )
    pad_h, pad_w = kernel_h // 2, kernel_w // 2
    grad_input = grad_padded[
        :, pad_h : pad_h + input_shape[1], pad_w : pad_w + input_shape[2], :
    ]
    return grad_input, grad_weight, grad_bias


def _conv1d_forward(x, weight, bias):
    kernel = weight.shape[0]
    if kernel % 2 == 0:
        raise ValueError("same padding requires an odd kernel")
    pad = kernel // 2
    padded = np.pad(x, ((0, 0), (pad, pad), (0, 0)))
    windows = np.lib.stride_tricks.sliding_window_view(padded, kernel, axis=1).transpose(
        0, 1, 3, 2
    )
    output = np.tensordot(windows, weight, axes=([2, 3], [0, 1])) + bias
    return output, (x.shape, padded, windows, weight)


def _conv1d_backward(gradient, cache):
    input_shape, padded, windows, weight = cache
    kernel = weight.shape[0]
    grad_weight = np.einsum("nlkc,nlo->kco", windows, gradient)
    grad_bias = gradient.sum(axis=(0, 1))
    grad_padded = np.zeros_like(padded)
    length = gradient.shape[1]
    for offset in range(kernel):
        grad_padded[:, offset : offset + length, :] += np.einsum(
            "nlo,co->nlc", gradient, weight[offset]
        )
    pad = kernel // 2
    return grad_padded[:, pad : pad + input_shape[1], :], grad_weight, grad_bias


def _max_pool2d_forward(x):
    output_h, output_w = x.shape[1] // 2, x.shape[2] // 2
    cropped = x[:, : output_h * 2, : output_w * 2, :]
    blocks = cropped.reshape(x.shape[0], output_h, 2, output_w, 2, x.shape[3])
    output = blocks.max(axis=(2, 4))
    mask = blocks == output[:, :, None, :, None, :]
    return output, (x.shape, mask, mask.sum(axis=(2, 4), keepdims=True))


def _max_pool2d_backward(gradient, cache):
    input_shape, mask, ties = cache
    expanded = gradient[:, :, None, :, None, :] * mask / ties
    cropped_gradient = expanded.reshape(
        input_shape[0], (input_shape[1] // 2) * 2, (input_shape[2] // 2) * 2, input_shape[3]
    )
    output = np.zeros(input_shape, dtype=gradient.dtype)
    output[:, : cropped_gradient.shape[1], : cropped_gradient.shape[2], :] = cropped_gradient
    return output


def _max_pool1d_forward(x):
    output_l = x.shape[1] // 2
    cropped = x[:, : output_l * 2, :]
    blocks = cropped.reshape(x.shape[0], output_l, 2, x.shape[2])
    output = blocks.max(axis=2)
    mask = blocks == output[:, :, None, :]
    return output, (x.shape, mask, mask.sum(axis=2, keepdims=True))


def _max_pool1d_backward(gradient, cache):
    input_shape, mask, ties = cache
    cropped_gradient = (gradient[:, :, None, :] * mask / ties).reshape(
        input_shape[0], (input_shape[1] // 2) * 2, input_shape[2]
    )
    output = np.zeros(input_shape, dtype=gradient.dtype)
    output[:, : cropped_gradient.shape[1], :] = cropped_gradient
    return output


class NumpyCNN:
    """Two-convolution multiclass CNN with manual forward/backward and Adam."""

    def __init__(
        self,
        input_shape,
        num_classes,
        mode="2d",
        filters=(8, 16),
        kernel_size=3,
        seed=42,
        learning_rate=0.01,
    ):
        if mode not in {"1d", "2d"}:
            raise ValueError("mode must be '1d' or '2d'")
        expected_rank = 3 if mode == "2d" else 2
        if len(input_shape) != expected_rank:
            raise ValueError(f"{mode} input_shape must have rank {expected_rank}")
        self.input_shape = tuple(int(value) for value in input_shape)
        self.num_classes = int(num_classes)
        self.mode = mode
        self.filters = tuple(int(value) for value in filters)
        self.kernel_size = int(kernel_size)
        self.seed = int(seed)
        self.learning_rate = float(learning_rate)
        rng = np.random.default_rng(self.seed)
        channels = self.input_shape[-1]
        first, second = self.filters
        if self.mode == "2d":
            first_shape = (self.kernel_size, self.kernel_size, channels, first)
            second_shape = (self.kernel_size, self.kernel_size, first, second)
            first_fan = self.kernel_size * self.kernel_size * channels
            second_fan = self.kernel_size * self.kernel_size * first
        else:
            first_shape = (self.kernel_size, channels, first)
            second_shape = (self.kernel_size, first, second)
            first_fan = self.kernel_size * channels
            second_fan = self.kernel_size * first
        self.params = {
            "W1": rng.normal(0.0, np.sqrt(2.0 / first_fan), first_shape),
            "b1": np.zeros(first, dtype=float),
            "W2": rng.normal(0.0, np.sqrt(2.0 / second_fan), second_shape),
            "b2": np.zeros(second, dtype=float),
            "W3": rng.normal(0.0, np.sqrt(2.0 / second), (second, self.num_classes)),
            "b3": np.zeros(self.num_classes, dtype=float),
        }

    @property
    def parameter_count(self):
        return int(sum(value.size for value in self.params.values()))

    @staticmethod
    def _softmax(logits):
        shifted = logits - logits.max(axis=1, keepdims=True)
        exponential = np.exp(shifted)
        return exponential / exponential.sum(axis=1, keepdims=True)

    def _forward(self, x):
        x = np.asarray(x, dtype=float)
        if self.mode == "2d":
            z1, conv1_cache = _conv2d_forward(x, self.params["W1"], self.params["b1"])
            a1 = np.maximum(z1, 0.0)
            pooled, pool_cache = _max_pool2d_forward(a1)
            z2, conv2_cache = _conv2d_forward(
                pooled, self.params["W2"], self.params["b2"]
            )
            a2 = np.maximum(z2, 0.0)
            features = a2.mean(axis=(1, 2))
            spatial_size = a2.shape[1] * a2.shape[2]
        else:
            z1, conv1_cache = _conv1d_forward(x, self.params["W1"], self.params["b1"])
            a1 = np.maximum(z1, 0.0)
            pooled, pool_cache = _max_pool1d_forward(a1)
            z2, conv2_cache = _conv1d_forward(
                pooled, self.params["W2"], self.params["b2"]
            )
            a2 = np.maximum(z2, 0.0)
            features = a2.mean(axis=1)
            spatial_size = a2.shape[1]
        logits = features @ self.params["W3"] + self.params["b3"]
        probabilities = self._softmax(logits)
        cache = {
            "z1": z1,
            "pool": pool_cache,
            "z2": z2,
            "a2": a2,
            "features": features,
            "conv1": conv1_cache,
            "conv2": conv2_cache,
            "spatial_size": spatial_size,
        }
        return probabilities, cache

    @staticmethod
    def _row_weights(y, class_weight):
        if class_weight is None:
            return np.ones(len(y), dtype=float)
        return np.asarray([float(class_weight[int(label)]) for label in y], dtype=float)

    def _loss_from_probabilities(self, probabilities, y, class_weight=None):
        y = np.asarray(y, dtype=int).reshape(-1)
        weights = self._row_weights(y, class_weight)
        losses = -np.log(np.clip(probabilities[np.arange(len(y)), y], 1e-12, 1.0))
        return float(np.sum(losses * weights) / np.sum(weights))

    def loss_and_gradients(self, x, y, class_weight=None):
        y = np.asarray(y, dtype=int).reshape(-1)
        probabilities, cache = self._forward(x)
        weights = self._row_weights(y, class_weight)
        grad_logits = probabilities.copy()
        grad_logits[np.arange(len(y)), y] -= 1.0
        grad_logits *= weights[:, None] / np.sum(weights)
        gradients = {
            "W3": cache["features"].T @ grad_logits,
            "b3": grad_logits.sum(axis=0),
        }
        grad_features = grad_logits @ self.params["W3"].T
        if self.mode == "2d":
            grad_a2 = grad_features[:, None, None, :] / cache["spatial_size"]
        else:
            grad_a2 = grad_features[:, None, :] / cache["spatial_size"]
        grad_z2 = grad_a2 * (cache["z2"] > 0.0)
        if self.mode == "2d":
            grad_pool, gradients["W2"], gradients["b2"] = _conv2d_backward(
                grad_z2, cache["conv2"]
            )
            grad_a1 = _max_pool2d_backward(grad_pool, cache["pool"])
            grad_z1 = grad_a1 * (cache["z1"] > 0.0)
            _, gradients["W1"], gradients["b1"] = _conv2d_backward(
                grad_z1, cache["conv1"]
            )
        else:
            grad_pool, gradients["W2"], gradients["b2"] = _conv1d_backward(
                grad_z2, cache["conv2"]
            )
            grad_a1 = _max_pool1d_backward(grad_pool, cache["pool"])
            grad_z1 = grad_a1 * (cache["z1"] > 0.0)
            _, gradients["W1"], gradients["b1"] = _conv1d_backward(
                grad_z1, cache["conv1"]
            )
        return self._loss_from_probabilities(probabilities, y, class_weight), gradients

    def _dataset_loss(self, x, y, batch_size, class_weight=None):
        y = np.asarray(y, dtype=int).reshape(-1)
        numerator = 0.0
        denominator = 0.0
        for start in range(0, len(y), int(batch_size)):
            batch_y = y[start : start + int(batch_size)]
            probabilities, _ = self._forward(x[start : start + int(batch_size)])
            weights = self._row_weights(batch_y, class_weight)
            losses = -np.log(
                np.clip(probabilities[np.arange(len(batch_y)), batch_y], 1e-12, 1.0)
            )
            numerator += float(np.sum(losses * weights))
            denominator += float(np.sum(weights))
        return numerator / denominator

    def fit(
        self,
        x_train,
        y_train,
        x_val,
        y_val,
        epochs=20,
        batch_size=64,
        patience=4,
        min_delta=1e-5,
        class_weight=None,
    ):
        x_train = np.asarray(x_train, dtype=float)
        y_train = np.asarray(y_train, dtype=int).reshape(-1)
        x_val = np.asarray(x_val, dtype=float)
        y_val = np.asarray(y_val, dtype=int).reshape(-1)
        rng = np.random.default_rng(self.seed)
        first = {key: np.zeros_like(value) for key, value in self.params.items()}
        second = {key: np.zeros_like(value) for key, value in self.params.items()}
        beta1, beta2, epsilon = 0.9, 0.999, 1e-8
        step, wait, best_epoch = 0, 0, 0
        best_val = np.inf
        best_params = {key: value.copy() for key, value in self.params.items()}
        history = {"train_loss": [], "val_loss": []}
        for epoch in range(int(epochs)):
            order = rng.permutation(len(x_train))
            for start in range(0, len(order), int(batch_size)):
                indices = order[start : start + int(batch_size)]
                _, gradients = self.loss_and_gradients(
                    x_train[indices], y_train[indices], class_weight=class_weight
                )
                step += 1
                for key in self.params:
                    first[key] = beta1 * first[key] + (1.0 - beta1) * gradients[key]
                    second[key] = beta2 * second[key] + (1.0 - beta2) * gradients[key] ** 2
                    first_hat = first[key] / (1.0 - beta1**step)
                    second_hat = second[key] / (1.0 - beta2**step)
                    self.params[key] -= self.learning_rate * first_hat / (
                        np.sqrt(second_hat) + epsilon
                    )
            train_loss = self._dataset_loss(
                x_train, y_train, batch_size, class_weight=class_weight
            )
            val_loss = self._dataset_loss(x_val, y_val, batch_size)
            history["train_loss"].append(float(train_loss))
            history["val_loss"].append(float(val_loss))
            if val_loss < best_val - float(min_delta):
                best_val = val_loss
                best_epoch = epoch + 1
                best_params = {key: value.copy() for key, value in self.params.items()}
                wait = 0
            else:
                wait += 1
                if wait >= int(patience):
                    break
        self.params = best_params
        history["best_epoch"] = best_epoch
        return history

    def predict_proba(self, x, batch_size=128):
        x = np.asarray(x, dtype=float)
        outputs = []
        for start in range(0, len(x), int(batch_size)):
            outputs.append(self._forward(x[start : start + int(batch_size)])[0])
        return np.vstack(outputs) if outputs else np.empty((0, self.num_classes))

    def predict(self, x, batch_size=128):
        return np.argmax(self.predict_proba(x, batch_size=batch_size), axis=1)

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = json.dumps(
            {
                "input_shape": list(self.input_shape),
                "num_classes": self.num_classes,
                "mode": self.mode,
                "filters": list(self.filters),
                "kernel_size": self.kernel_size,
                "seed": self.seed,
                "learning_rate": self.learning_rate,
            }
        )
        np.savez(path, metadata=np.array(metadata), **self.params)

    @classmethod
    def load(cls, path):
        with np.load(Path(path), allow_pickle=False) as data:
            metadata = json.loads(str(data["metadata"].item()))
            model = cls(**metadata)
            model.params = {key: data[key].copy() for key in model.params}
        return model
