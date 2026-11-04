"""PyTorch implementation of the matched Chapter 3 CNN."""

import copy
from pathlib import Path

import numpy as np
import torch
from torch import nn


class _MatchedCNN(nn.Module):
    def __init__(self, channels, num_classes, mode, filters, kernel_size):
        super().__init__()
        first, second = filters
        padding = kernel_size // 2
        if mode == "2d":
            self.network = nn.Sequential(
                nn.Conv2d(channels, first, kernel_size, padding=padding),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(first, second, kernel_size, padding=padding),
                nn.ReLU(),
                nn.AdaptiveAvgPool2d((1, 1)),
                nn.Flatten(),
                nn.Linear(second, num_classes),
            )
        else:
            self.network = nn.Sequential(
                nn.Conv1d(channels, first, kernel_size, padding=padding),
                nn.ReLU(),
                nn.MaxPool1d(2),
                nn.Conv1d(first, second, kernel_size, padding=padding),
                nn.ReLU(),
                nn.AdaptiveAvgPool1d(1),
                nn.Flatten(),
                nn.Linear(second, num_classes),
            )

    def forward(self, x):
        return self.network(x)


class TorchCNN:
    def __init__(
        self,
        input_shape,
        num_classes,
        mode="2d",
        filters=(8, 16),
        kernel_size=3,
        seed=42,
        learning_rate=0.01,
        model=None,
    ):
        if mode not in {"1d", "2d"}:
            raise ValueError("mode must be '1d' or '2d'")
        self.input_shape = tuple(int(value) for value in input_shape)
        self.num_classes = int(num_classes)
        self.mode = mode
        self.filters = tuple(int(value) for value in filters)
        self.kernel_size = int(kernel_size)
        self.seed = int(seed)
        self.learning_rate = float(learning_rate)
        torch.manual_seed(self.seed)
        self.model = model or _MatchedCNN(
            self.input_shape[-1],
            self.num_classes,
            self.mode,
            self.filters,
            self.kernel_size,
        )

    @property
    def parameter_count(self):
        return int(sum(parameter.numel() for parameter in self.model.parameters()))

    def _tensor_x(self, x):
        tensor = torch.as_tensor(np.asarray(x), dtype=torch.float32)
        if self.mode == "2d":
            return tensor.permute(0, 3, 1, 2)
        return tensor.permute(0, 2, 1)

    @staticmethod
    def _loss(logits, targets, class_weight=None):
        row_loss = nn.functional.cross_entropy(logits, targets, reduction="none")
        if class_weight is None:
            return row_loss.mean()
        weights = torch.as_tensor(
            [float(class_weight[int(value)]) for value in targets.cpu().numpy()],
            dtype=row_loss.dtype,
            device=row_loss.device,
        )
        return torch.sum(row_loss * weights) / torch.sum(weights)

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
        x_train_tensor = self._tensor_x(x_train)
        y_train_tensor = torch.as_tensor(np.array(y_train, copy=True), dtype=torch.long)
        x_val_tensor = self._tensor_x(x_val)
        y_val_tensor = torch.as_tensor(np.array(y_val, copy=True), dtype=torch.long)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        generator = torch.Generator().manual_seed(self.seed)
        best_val, wait, best_epoch = float("inf"), 0, 0
        best_state = copy.deepcopy(self.model.state_dict())
        history = {"train_loss": [], "val_loss": []}
        for epoch in range(int(epochs)):
            self.model.train()
            order = torch.randperm(len(x_train_tensor), generator=generator)
            for start in range(0, len(order), int(batch_size)):
                indices = order[start : start + int(batch_size)]
                optimizer.zero_grad(set_to_none=True)
                loss = self._loss(
                    self.model(x_train_tensor[indices]),
                    y_train_tensor[indices],
                    class_weight=class_weight,
                )
                loss.backward()
                optimizer.step()
            self.model.eval()
            with torch.no_grad():
                train_loss = float(
                    self._loss(
                        self.model(x_train_tensor),
                        y_train_tensor,
                        class_weight=class_weight,
                    )
                )
                val_loss = float(self._loss(self.model(x_val_tensor), y_val_tensor))
            history["train_loss"].append(train_loss)
            history["val_loss"].append(val_loss)
            if val_loss < best_val - float(min_delta):
                best_val = val_loss
                best_epoch = epoch + 1
                best_state = copy.deepcopy(self.model.state_dict())
                wait = 0
            else:
                wait += 1
                if wait >= int(patience):
                    break
        self.model.load_state_dict(best_state)
        history["best_epoch"] = best_epoch
        return history

    def predict_proba(self, x, batch_size=128):
        tensor = self._tensor_x(x)
        outputs = []
        self.model.eval()
        with torch.no_grad():
            for start in range(0, len(tensor), int(batch_size)):
                outputs.append(torch.softmax(self.model(tensor[start : start + int(batch_size)]), dim=1))
        if not outputs:
            return np.empty((0, self.num_classes))
        return torch.cat(outputs).cpu().numpy()

    def predict(self, x, batch_size=128):
        return np.argmax(self.predict_proba(x, batch_size=batch_size), axis=1)

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "config": {
                    "input_shape": list(self.input_shape),
                    "num_classes": self.num_classes,
                    "mode": self.mode,
                    "filters": list(self.filters),
                    "kernel_size": self.kernel_size,
                    "seed": self.seed,
                    "learning_rate": self.learning_rate,
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
