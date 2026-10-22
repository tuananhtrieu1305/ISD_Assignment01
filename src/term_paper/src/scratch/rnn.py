"""Many-to-one Vanilla RNN implemented with NumPy and explicit BPTT."""

import json
from pathlib import Path

import numpy as np


def clip_gradients(gradients, max_norm):
    """Return globally norm-clipped copies and the original global norm."""
    total = float(np.sqrt(sum(np.sum(value**2) for value in gradients.values())))
    scale = min(1.0, float(max_norm) / (total + 1e-12))
    return {key: value * scale for key, value in gradients.items()}, total


class NumpyRNN:
    def __init__(
        self,
        input_size,
        hidden_size=32,
        task="binary",
        seed=42,
        learning_rate=0.003,
        gradient_clip_norm=1.0,
    ):
        if task not in {"binary", "regression"}:
            raise ValueError("task must be 'binary' or 'regression'")
        self.input_size = int(input_size)
        self.hidden_size = int(hidden_size)
        self.task = task
        self.seed = int(seed)
        self.learning_rate = float(learning_rate)
        self.gradient_clip_norm = float(gradient_clip_norm)
        rng = np.random.default_rng(self.seed)
        self.params = {
            "Wxh": rng.normal(
                0.0, np.sqrt(1.0 / self.input_size), (self.input_size, self.hidden_size)
            ),
            "Whh": rng.normal(
                0.0, np.sqrt(1.0 / self.hidden_size), (self.hidden_size, self.hidden_size)
            ),
            "bh": np.zeros((1, self.hidden_size), dtype=float),
            "Why": rng.normal(0.0, np.sqrt(1.0 / self.hidden_size), (self.hidden_size, 1)),
            "by": np.zeros((1, 1), dtype=float),
        }

    @property
    def parameter_count(self):
        return int(sum(value.size for value in self.params.values()))

    @staticmethod
    def _sigmoid(logits):
        logits = np.clip(logits, -40.0, 40.0)
        return 1.0 / (1.0 + np.exp(-logits))

    def _forward(self, x):
        x = np.asarray(x, dtype=float)
        if x.ndim != 3 or x.shape[2] != self.input_size:
            raise ValueError("x must have shape (batch, sequence, input_size)")
        hidden = np.zeros((len(x), self.hidden_size), dtype=float)
        states = [hidden]
        for step in range(x.shape[1]):
            hidden = np.tanh(
                x[:, step, :] @ self.params["Wxh"]
                + hidden @ self.params["Whh"]
                + self.params["bh"]
            )
            states.append(hidden)
        output = hidden @ self.params["Why"] + self.params["by"]
        score = self._sigmoid(output) if self.task == "binary" else output
        return score, {"x": x, "states": states}

    @staticmethod
    def _row_weights(y, class_weight):
        if class_weight is None:
            return np.ones_like(y, dtype=float)
        return np.where(y == 1.0, float(class_weight[1]), float(class_weight[0]))

    def _loss(self, score, y, class_weight=None):
        y = np.asarray(y, dtype=float).reshape(-1, 1)
        if self.task == "binary":
            losses = -(y * np.log(np.clip(score, 1e-12, 1.0)) + (1.0 - y) * np.log(np.clip(1.0 - score, 1e-12, 1.0)))
            weights = self._row_weights(y, class_weight)
            return float(np.sum(losses * weights) / np.sum(weights))
        return float(np.mean((score - y) ** 2))

    def loss_and_gradients(self, x, y, class_weight=None, clip_norm=None):
        y = np.asarray(y, dtype=float).reshape(-1, 1)
        score, cache = self._forward(x)
        if self.task == "binary":
            weights = self._row_weights(y, class_weight)
            grad_output = (score - y) * weights / np.sum(weights)
        else:
            grad_output = 2.0 * (score - y) / len(y)
        states = cache["states"]
        gradients = {
            "Wxh": np.zeros_like(self.params["Wxh"]),
            "Whh": np.zeros_like(self.params["Whh"]),
            "bh": np.zeros_like(self.params["bh"]),
            "Why": states[-1].T @ grad_output,
            "by": grad_output.sum(axis=0, keepdims=True),
        }
        grad_hidden = grad_output @ self.params["Why"].T
        for step in range(cache["x"].shape[1] - 1, -1, -1):
            current = states[step + 1]
            previous = states[step]
            grad_pre_activation = grad_hidden * (1.0 - current**2)
            gradients["Wxh"] += cache["x"][:, step, :].T @ grad_pre_activation
            gradients["Whh"] += previous.T @ grad_pre_activation
            gradients["bh"] += grad_pre_activation.sum(axis=0, keepdims=True)
            grad_hidden = grad_pre_activation @ self.params["Whh"].T
        if clip_norm is not None:
            gradients, _ = clip_gradients(gradients, clip_norm)
        return self._loss(score, y, class_weight=class_weight), gradients

    def _dataset_loss(self, x, y, batch_size, class_weight=None):
        y = np.asarray(y, dtype=float).reshape(-1, 1)
        numerator = 0.0
        denominator = 0.0
        for start in range(0, len(y), int(batch_size)):
            batch_y = y[start : start + int(batch_size)]
            score, _ = self._forward(x[start : start + int(batch_size)])
            if self.task == "binary":
                weights = self._row_weights(batch_y, class_weight)
                losses = -(
                    batch_y * np.log(np.clip(score, 1e-12, 1.0))
                    + (1.0 - batch_y) * np.log(np.clip(1.0 - score, 1e-12, 1.0))
                )
                numerator += float(np.sum(losses * weights))
                denominator += float(np.sum(weights))
            else:
                numerator += float(np.sum((score - batch_y) ** 2))
                denominator += len(batch_y)
        return numerator / denominator

    def fit(
        self,
        x_train,
        y_train,
        x_val,
        y_val,
        epochs=30,
        batch_size=512,
        patience=5,
        min_delta=1e-4,
        class_weight=None,
    ):
        x_train = np.asarray(x_train, dtype=float)
        y_train = np.asarray(y_train, dtype=float).reshape(-1)
        x_val = np.asarray(x_val, dtype=float)
        y_val = np.asarray(y_val, dtype=float).reshape(-1)
        rng = np.random.default_rng(self.seed)
        first = {key: np.zeros_like(value) for key, value in self.params.items()}
        second = {key: np.zeros_like(value) for key, value in self.params.items()}
        beta1, beta2, epsilon = 0.9, 0.999, 1e-8
        step_count, wait, best_epoch = 0, 0, 0
        best_val = np.inf
        best_params = {key: value.copy() for key, value in self.params.items()}
        history = {"train_loss": [], "val_loss": []}
        for epoch in range(int(epochs)):
            order = rng.permutation(len(x_train))
            for start in range(0, len(order), int(batch_size)):
                indices = order[start : start + int(batch_size)]
                _, gradients = self.loss_and_gradients(
                    x_train[indices],
                    y_train[indices],
                    class_weight=class_weight,
                    clip_norm=self.gradient_clip_norm,
                )
                step_count += 1
                for key in self.params:
                    first[key] = beta1 * first[key] + (1.0 - beta1) * gradients[key]
                    second[key] = beta2 * second[key] + (1.0 - beta2) * gradients[key] ** 2
                    first_hat = first[key] / (1.0 - beta1**step_count)
                    second_hat = second[key] / (1.0 - beta2**step_count)
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

    def predict_score(self, x, batch_size=2048):
        x = np.asarray(x, dtype=float)
        outputs = []
        for start in range(0, len(x), int(batch_size)):
            outputs.append(self._forward(x[start : start + int(batch_size)])[0].reshape(-1))
        return np.concatenate(outputs) if outputs else np.empty(0)

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = json.dumps(
            {
                "input_size": self.input_size,
                "hidden_size": self.hidden_size,
                "task": self.task,
                "seed": self.seed,
                "learning_rate": self.learning_rate,
                "gradient_clip_norm": self.gradient_clip_norm,
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
