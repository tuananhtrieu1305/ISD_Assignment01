"""PyTorch implementation of the matched Chapter 4 Vanilla RNN."""

import copy
from pathlib import Path

import numpy as np
import torch
from torch import nn


class _MatchedRNN(nn.Module):
    def __init__(self, input_size, hidden_size):
        super().__init__()
        self.rnn = nn.RNN(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=1,
            nonlinearity="tanh",
            batch_first=True,
            bias=True,
        )
        # Keras/NumPy use one recurrent bias.  Keep PyTorch's second bias fixed at zero.
        with torch.no_grad():
            self.rnn.bias_hh_l0.zero_()
        self.rnn.bias_hh_l0.requires_grad_(False)
        self.head = nn.Linear(hidden_size, 1)

    def forward(self, x):
        output, _ = self.rnn(x)
        return self.head(output[:, -1, :])


class TorchRNN:
    def __init__(
        self,
        input_size,
        hidden_size=32,
        task="binary",
        seed=42,
        learning_rate=0.003,
        gradient_clip_norm=1.0,
        model=None,
    ):
        if task not in {"binary", "regression"}:
            raise ValueError("task must be 'binary' or 'regression'")
        self.input_size = int(input_size)
        self.hidden_size = int(hidden_size)
        self.task = task
        self.seed = int(seed)
        self.learning_rate = float(learning_rate)
        self.gradient_clip_norm = float(gradient_clip_norm)
        torch.manual_seed(self.seed)
        self.model = model or _MatchedRNN(self.input_size, self.hidden_size)

    @property
    def parameter_count(self):
        return int(sum(parameter.numel() for parameter in self.model.parameters() if parameter.requires_grad))

    def _loss(self, output, target, class_weight=None):
        if self.task == "binary":
            row_loss = nn.functional.binary_cross_entropy_with_logits(
                output, target, reduction="none"
            )
            if class_weight is not None:
                weights = torch.where(
                    target == 1.0,
                    torch.tensor(float(class_weight[1]), dtype=output.dtype),
                    torch.tensor(float(class_weight[0]), dtype=output.dtype),
                )
                return torch.sum(row_loss * weights) / torch.sum(weights)
            return row_loss.mean()
        return torch.mean((output - target) ** 2)

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
        x_train_tensor = torch.as_tensor(np.asarray(x_train), dtype=torch.float32)
        y_train_tensor = torch.as_tensor(np.array(y_train, copy=True), dtype=torch.float32).reshape(-1, 1)
        x_val_tensor = torch.as_tensor(np.asarray(x_val), dtype=torch.float32)
        y_val_tensor = torch.as_tensor(np.array(y_val, copy=True), dtype=torch.float32).reshape(-1, 1)
        parameters = [parameter for parameter in self.model.parameters() if parameter.requires_grad]
        optimizer = torch.optim.Adam(parameters, lr=self.learning_rate)
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
                nn.utils.clip_grad_norm_(parameters, self.gradient_clip_norm)
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

    def predict_score(self, x, batch_size=2048):
        tensor = torch.as_tensor(np.asarray(x), dtype=torch.float32)
        outputs = []
        self.model.eval()
        with torch.no_grad():
            for start in range(0, len(tensor), int(batch_size)):
                output = self.model(tensor[start : start + int(batch_size)]).reshape(-1)
                if self.task == "binary":
                    output = torch.sigmoid(output)
                outputs.append(output)
        return torch.cat(outputs).cpu().numpy() if outputs else np.empty(0)

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "config": {
                    "input_size": self.input_size,
                    "hidden_size": self.hidden_size,
                    "task": self.task,
                    "seed": self.seed,
                    "learning_rate": self.learning_rate,
                    "gradient_clip_norm": self.gradient_clip_norm,
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
