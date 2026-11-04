"""Two-hidden-layer MLP implemented only with NumPy."""

import json
from pathlib import Path

import numpy as np


class NumpyMLP:
    def __init__(
        self,
        input_dim,
        task,
        hidden=(64, 32),
        seed=42,
        learning_rate=0.01,
        l2=0.0,
    ):
        if task not in {"binary", "regression"}:
            raise ValueError("task must be 'binary' or 'regression'")
        self.input_dim = int(input_dim)
        self.task = task
        self.hidden = tuple(int(v) for v in hidden)
        self.seed = int(seed)
        self.learning_rate = float(learning_rate)
        self.l2 = float(l2)
        rng = np.random.default_rng(self.seed)
        h1, h2 = self.hidden
        self.params = {
            "W1": rng.normal(0.0, np.sqrt(2.0 / self.input_dim), (self.input_dim, h1)),
            "b1": np.zeros((1, h1), dtype=float),
            "W2": rng.normal(0.0, np.sqrt(2.0 / h1), (h1, h2)),
            "b2": np.zeros((1, h2), dtype=float),
            "W3": rng.normal(0.0, np.sqrt(2.0 / h2), (h2, 1)),
            "b3": np.zeros((1, 1), dtype=float),
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
        z1 = x @ self.params["W1"] + self.params["b1"]
        h1 = np.maximum(z1, 0.0)
        z2 = h1 @ self.params["W2"] + self.params["b2"]
        h2 = np.maximum(z2, 0.0)
        output = h2 @ self.params["W3"] + self.params["b3"]
        score = self._sigmoid(output) if self.task == "binary" else output
        return score, {"x": x, "z1": z1, "h1": h1, "z2": z2, "h2": h2}

    def _loss(self, score, y, class_weight=None):
        y = np.asarray(y, dtype=float).reshape(-1, 1)
        if self.task == "binary":
            clipped = np.clip(score, 1e-7, 1.0 - 1e-7)
            per_row = -(y * np.log(clipped) + (1.0 - y) * np.log(1.0 - clipped))
            if class_weight is not None:
                weights = np.where(y == 1.0, class_weight[1], class_weight[0])
                data_loss = float(np.sum(per_row * weights) / np.sum(weights))
            else:
                data_loss = float(np.mean(per_row))
        else:
            data_loss = float(np.mean((score - y) ** 2))
        penalty = 0.5 * self.l2 * sum(
            float(np.sum(self.params[key] ** 2)) for key in ("W1", "W2", "W3")
        ) / max(len(y), 1)
        return data_loss + penalty

    def loss_and_gradients(self, x, y, class_weight=None):
        y = np.asarray(y, dtype=float).reshape(-1, 1)
        score, cache = self._forward(x)
        n = len(y)
        if self.task == "binary":
            if class_weight is None:
                delta = (score - y) / n
            else:
                weights = np.where(y == 1.0, class_weight[1], class_weight[0])
                delta = (score - y) * weights / np.sum(weights)
        else:
            delta = 2.0 * (score - y) / n
        gradients = {}
        gradients["W3"] = cache["h2"].T @ delta + self.l2 * self.params["W3"] / n
        gradients["b3"] = np.sum(delta, axis=0, keepdims=True)
        delta2 = (delta @ self.params["W3"].T) * (cache["z2"] > 0.0)
        gradients["W2"] = cache["h1"].T @ delta2 + self.l2 * self.params["W2"] / n
        gradients["b2"] = np.sum(delta2, axis=0, keepdims=True)
        delta1 = (delta2 @ self.params["W2"].T) * (cache["z1"] > 0.0)
        gradients["W1"] = cache["x"].T @ delta1 + self.l2 * self.params["W1"] / n
        gradients["b1"] = np.sum(delta1, axis=0, keepdims=True)
        return self._loss(score, y, class_weight=class_weight), gradients

    def fit(
        self,
        x_train,
        y_train,
        x_val,
        y_val,
        epochs=100,
        batch_size=512,
        patience=10,
        min_delta=1e-5,
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
        step = 0
        best_val = np.inf
        best_params = {key: value.copy() for key, value in self.params.items()}
        wait = 0
        history = {"train_loss": [], "val_loss": []}
        for _ in range(int(epochs)):
            order = rng.permutation(len(x_train))
            for start in range(0, len(x_train), int(batch_size)):
                batch_indices = order[start : start + int(batch_size)]
                if len(batch_indices) == 0:
                    continue
                _, gradients = self.loss_and_gradients(
                    x_train[batch_indices], y_train[batch_indices], class_weight=class_weight
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
            train_score, _ = self._forward(x_train)
            val_score, _ = self._forward(x_val)
            train_loss = self._loss(train_score, y_train, class_weight=class_weight)
            val_loss = self._loss(val_score, y_val)
            history["train_loss"].append(train_loss)
            history["val_loss"].append(val_loss)
            if val_loss < best_val - float(min_delta):
                best_val = val_loss
                best_params = {key: value.copy() for key, value in self.params.items()}
                wait = 0
            else:
                wait += 1
                if wait >= int(patience):
                    break
        self.params = best_params
        return history

    def predict_score(self, x):
        score, _ = self._forward(x)
        return score.reshape(-1)

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = json.dumps(
            {
                "input_dim": self.input_dim,
                "task": self.task,
                "hidden": list(self.hidden),
                "seed": self.seed,
                "learning_rate": self.learning_rate,
                "l2": self.l2,
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
