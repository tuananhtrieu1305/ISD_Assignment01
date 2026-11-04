"""PyTorch implementation of the matched Chapter 2 MLP."""

import copy
from pathlib import Path

import numpy as np
import torch
from torch import nn


class TorchMLP:
    def __init__(
        self,
        input_dim,
        task,
        hidden=(64, 32),
        seed=42,
        learning_rate=0.01,
        l2=0.0,
        model=None,
    ):
        if task not in {"binary", "regression"}:
            raise ValueError("task must be 'binary' or 'regression'")
        self.input_dim = int(input_dim)
        self.task = task
        self.hidden = tuple(int(v) for v in hidden)
        self.seed = int(seed)
        self.learning_rate = float(learning_rate)
        self.l2 = float(l2)
        torch.manual_seed(self.seed)
        self.model = model or nn.Sequential(
            nn.Linear(self.input_dim, self.hidden[0]),
            nn.ReLU(),
            nn.Linear(self.hidden[0], self.hidden[1]),
            nn.ReLU(),
            nn.Linear(self.hidden[1], 1),
        )

    @property
    def parameter_count(self):
        return int(sum(parameter.numel() for parameter in self.model.parameters()))

    def _loss(self, output, target, sample_weight=None):
        if self.task == "binary":
            per_row = nn.functional.binary_cross_entropy_with_logits(
                output, target, reduction="none"
            )
        else:
            per_row = (output - target) ** 2
        if sample_weight is not None:
            return torch.sum(per_row * sample_weight) / torch.sum(sample_weight)
        return torch.mean(per_row)

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
        x_train_tensor = torch.as_tensor(np.asarray(x_train), dtype=torch.float32)
        y_train_tensor = torch.as_tensor(np.asarray(y_train), dtype=torch.float32).reshape(-1, 1)
        x_val_tensor = torch.as_tensor(np.asarray(x_val), dtype=torch.float32)
        y_val_tensor = torch.as_tensor(np.asarray(y_val), dtype=torch.float32).reshape(-1, 1)
        optimizer = torch.optim.Adam(
            self.model.parameters(), lr=self.learning_rate, weight_decay=self.l2
        )
        generator = torch.Generator().manual_seed(self.seed)
        best_val = float("inf")
        best_state = copy.deepcopy(self.model.state_dict())
        wait = 0
        history = {"train_loss": [], "val_loss": []}
        for _ in range(int(epochs)):
            self.model.train()
            order = torch.randperm(len(x_train_tensor), generator=generator)
            for start in range(0, len(order), int(batch_size)):
                indices = order[start : start + int(batch_size)]
                xb = x_train_tensor[indices]
                yb = y_train_tensor[indices]
                weights = None
                if class_weight is not None:
                    weights = torch.where(
                        yb == 1.0,
                        torch.tensor(float(class_weight[1])),
                        torch.tensor(float(class_weight[0])),
                    )
                optimizer.zero_grad(set_to_none=True)
                loss = self._loss(self.model(xb), yb, weights)
                loss.backward()
                optimizer.step()
            self.model.eval()
            with torch.no_grad():
                train_loss = float(self._loss(self.model(x_train_tensor), y_train_tensor))
                val_loss = float(self._loss(self.model(x_val_tensor), y_val_tensor))
            history["train_loss"].append(train_loss)
            history["val_loss"].append(val_loss)
            if val_loss < best_val - float(min_delta):
                best_val = val_loss
                best_state = copy.deepcopy(self.model.state_dict())
                wait = 0
            else:
                wait += 1
                if wait >= int(patience):
                    break
        self.model.load_state_dict(best_state)
        return history

    def predict_score(self, x):
        self.model.eval()
        with torch.no_grad():
            raw = self.model(torch.as_tensor(np.asarray(x), dtype=torch.float32)).reshape(-1)
            if self.task == "binary":
                raw = torch.sigmoid(raw)
        return raw.cpu().numpy()

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "config": {
                    "input_dim": self.input_dim,
                    "task": self.task,
                    "hidden": list(self.hidden),
                    "seed": self.seed,
                    "learning_rate": self.learning_rate,
                    "l2": self.l2,
                },
                "state_dict": self.model.state_dict(),
            },
            path,
        )

    @classmethod
    def load(cls, path):
        payload = torch.load(Path(path), map_location="cpu", weights_only=False)
        model = cls(**payload["config"])
        model.model.load_state_dict(payload["state_dict"])
        return model
