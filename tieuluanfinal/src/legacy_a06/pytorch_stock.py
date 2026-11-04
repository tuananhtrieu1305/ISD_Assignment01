"""Reusable PyTorch components for the A06 stock Vanilla RNN."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from torch import nn
from torch.utils.data import DataLoader, Dataset


class StockSequenceDataset(Dataset):
    """Expose finalized stock sequences without altering their values."""

    def __init__(self, features: np.ndarray, scaled_targets: np.ndarray) -> None:
        x = np.asarray(features)
        y = np.asarray(scaled_targets)
        if x.ndim != 3 or x.shape[1:] != (30, 5):
            raise ValueError("stock X must have shape (samples, 30, 5)")
        if y.ndim != 1 or len(x) != len(y):
            raise ValueError("stock y must be one-dimensional and align with X")
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError("stock features and targets must be finite")
        self.features = torch.as_tensor(x, dtype=torch.float32)
        self.targets = torch.as_tensor(y, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.features[index], self.targets[index]


class StockRNN(nn.Module):
    """One-layer Vanilla RNN followed by one continuous regression output."""

    def __init__(self, input_size: int = 5, hidden_size: int = 64, num_layers: int = 1) -> None:
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.rnn = nn.RNN(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            nonlinearity="tanh",
        )
        self.regressor = nn.Linear(hidden_size, 1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        _, hidden = self.rnn(inputs)
        final_hidden = hidden[-1]
        return self.regressor(final_hidden).squeeze(-1)


def count_trainable_parameters(model: nn.Module) -> int:
    """Count parameters that receive gradient updates."""

    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def _average_loss(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    model.eval()
    total_loss = 0.0
    total_samples = 0
    with torch.inference_mode():
        for features, targets in loader:
            predictions = model(features.to(device))
            loss = criterion(predictions, targets.to(device))
            batch_size = len(targets)
            total_loss += float(loss.item()) * batch_size
            total_samples += batch_size
    if total_samples == 0:
        raise ValueError("loader must contain at least one sample")
    return total_loss / total_samples


def _save_checkpoint_atomic(path: Path, payload: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    torch.save(payload, temporary)
    os.replace(temporary, destination)


def train_with_early_stopping(
    *,
    model: nn.Module,
    train_loader: DataLoader,
    validation_loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    checkpoint_path: Path,
    max_epochs: int = 30,
    patience: int = 5,
    min_delta: float = 1e-4,
    gradient_clip_norm: float | None = 1.0,
    seed: int = 42,
    verbose: bool = True,
) -> dict[str, Any]:
    """Train on TRAIN, select only by validation loss, and restore the best state."""

    if max_epochs <= 0 or patience <= 0:
        raise ValueError("max_epochs and patience must be positive")

    model.to(device)
    history: dict[str, list[float]] = {"train_loss": [], "validation_loss": []}
    best_validation_loss = float("inf")
    patience_reference_loss = float("inf")
    best_epoch = 0
    epochs_without_improvement = 0
    start_time = time.perf_counter()

    for epoch in range(1, max_epochs + 1):
        model.train()
        total_loss = 0.0
        total_samples = 0
        for features, targets in train_loader:
            features = features.to(device)
            targets = targets.to(device)
            optimizer.zero_grad(set_to_none=True)
            predictions = model(features)
            loss = criterion(predictions, targets)
            loss.backward()
            if gradient_clip_norm is not None:
                nn.utils.clip_grad_norm_(model.parameters(), gradient_clip_norm)
            optimizer.step()
            batch_size = len(targets)
            total_loss += float(loss.item()) * batch_size
            total_samples += batch_size

        if total_samples == 0:
            raise ValueError("train_loader must contain at least one sample")
        train_loss = total_loss / total_samples
        validation_loss = _average_loss(model, validation_loader, criterion, device)
        history["train_loss"].append(train_loss)
        history["validation_loss"].append(validation_loss)

        new_best = validation_loss < best_validation_loss
        if new_best:
            best_validation_loss = validation_loss
            best_epoch = epoch
            _save_checkpoint_atomic(
                checkpoint_path,
                {
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "best_epoch": best_epoch,
                    "best_validation_loss": best_validation_loss,
                    "seed": seed,
                    "architecture": {
                        "input_size": getattr(model, "input_size", None),
                        "hidden_size": getattr(model, "hidden_size", None),
                        "num_layers": getattr(model, "num_layers", None),
                    },
                },
            )

        if validation_loss < patience_reference_loss - min_delta:
            patience_reference_loss = validation_loss
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        if verbose:
            marker = " *" if new_best else ""
            print(
                f"Epoch {epoch:02d}/{max_epochs} | train={train_loss:.6f} | "
                f"val={validation_loss:.6f}{marker}"
            )
        if epochs_without_improvement >= patience:
            if verbose:
                print(f"Early stopping at epoch {epoch}; best epoch = {best_epoch}.")
            break

    duration_seconds = time.perf_counter() - start_time
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state_dict"])
    return {
        "history": history,
        "epochs_ran": len(history["train_loss"]),
        "best_epoch": int(best_epoch),
        "best_validation_loss": float(best_validation_loss),
        "training_duration_seconds": float(duration_seconds),
    }


def predict_scaled_targets(
    model: nn.Module,
    loader: DataLoader,
    *,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    """Return scaled labels and predictions in DataLoader order."""

    model.eval()
    target_batches: list[np.ndarray] = []
    prediction_batches: list[np.ndarray] = []
    with torch.inference_mode():
        for features, targets in loader:
            predictions = model(features.to(device))
            target_batches.append(targets.cpu().numpy())
            prediction_batches.append(predictions.cpu().numpy())
    if not target_batches:
        raise ValueError("loader must contain at least one sample")
    return np.concatenate(target_batches), np.concatenate(prediction_batches)


def inverse_transform_targets(scaler: Any, scaled_values: np.ndarray) -> np.ndarray:
    """Convert one-dimensional standardized Close values back to price scale."""

    values = np.asarray(scaled_values, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError("scaled_values must be one-dimensional")
    return np.asarray(scaler.inverse_transform(values.reshape(-1, 1))).ravel()


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    """Calculate MAE, RMSE, and R² on a shared real-value scale."""

    y_true = np.asarray(actual, dtype=np.float64)
    y_pred = np.asarray(predicted, dtype=np.float64)
    if y_true.ndim != 1 or y_true.shape != y_pred.shape:
        raise ValueError("actual and predicted must be aligned one-dimensional arrays")
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }
