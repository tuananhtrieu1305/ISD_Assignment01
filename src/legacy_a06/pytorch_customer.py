"""Reusable PyTorch components for the A06 customer Vanilla RNN."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from torch import nn
from torch.utils.data import DataLoader, Dataset


class CustomerSequenceDataset(Dataset):
    """Expose preprocessed customer sequences without changing their values."""

    def __init__(self, features: np.ndarray, labels: np.ndarray) -> None:
        x = np.asarray(features)
        y = np.asarray(labels)
        if x.ndim != 3 or x.shape[1:] != (8, 5):
            raise ValueError("customer X must have shape (samples, 8, 5)")
        if y.ndim != 1 or len(x) != len(y):
            raise ValueError("customer y must be one-dimensional and align with X")
        if not np.isin(y, [0, 1]).all():
            raise ValueError("customer labels must be binary")
        self.features = torch.as_tensor(x, dtype=torch.float32)
        self.labels = torch.as_tensor(y, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.features[index], self.labels[index]


class CustomerRNN(nn.Module):
    """One-layer Vanilla RNN followed by a single binary-classification logit."""

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
        self.classifier = nn.Linear(hidden_size, 1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        _, hidden = self.rnn(inputs)
        final_hidden = hidden[-1]
        return self.classifier(final_hidden).squeeze(-1)


def count_trainable_parameters(model: nn.Module) -> int:
    """Count parameters that participate in gradient updates."""

    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def compute_positive_weight(train_labels: np.ndarray) -> float:
    """Return negative/positive ratio from the supplied TRAIN labels only."""

    labels = np.asarray(train_labels)
    negatives = int(np.count_nonzero(labels == 0))
    positives = int(np.count_nonzero(labels == 1))
    if negatives == 0 or positives == 0 or negatives + positives != len(labels):
        raise ValueError("train_labels must contain both binary classes and no other values")
    return negatives / positives


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
        for features, labels in loader:
            features = features.to(device)
            labels = labels.to(device)
            logits = model(features)
            loss = criterion(logits, labels)
            batch_size = len(labels)
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
        running_loss = 0.0
        sample_count = 0
        for features, labels in train_loader:
            features = features.to(device)
            labels = labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(features)
            loss = criterion(logits, labels)
            loss.backward()
            if gradient_clip_norm is not None:
                nn.utils.clip_grad_norm_(model.parameters(), gradient_clip_norm)
            optimizer.step()
            batch_size = len(labels)
            running_loss += float(loss.item()) * batch_size
            sample_count += batch_size

        if sample_count == 0:
            raise ValueError("train_loader must contain at least one sample")
        train_loss = running_loss / sample_count
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

        meaningful_improvement = validation_loss < patience_reference_loss - min_delta
        if meaningful_improvement:
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
                print(f"Early stopping tại epoch {epoch}; best epoch = {best_epoch}.")
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


def predict_probabilities(
    model: nn.Module,
    loader: DataLoader,
    *,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    """Return true labels and sigmoid probabilities in DataLoader order."""

    model.eval()
    label_batches: list[np.ndarray] = []
    probability_batches: list[np.ndarray] = []
    with torch.inference_mode():
        for features, labels in loader:
            logits = model(features.to(device))
            probabilities = torch.sigmoid(logits)
            label_batches.append(labels.cpu().numpy())
            probability_batches.append(probabilities.cpu().numpy())
    if not label_batches:
        raise ValueError("loader must contain at least one sample")
    return np.concatenate(label_batches), np.concatenate(probability_batches)


def binary_classification_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    *,
    threshold: float = 0.5,
) -> dict[str, float]:
    """Calculate fixed-threshold classification metrics plus threshold-free ROC-AUC."""

    y_true = np.asarray(labels).astype(np.int8)
    y_probability = np.asarray(probabilities, dtype=np.float64)
    if y_true.shape != y_probability.shape:
        raise ValueError("labels and probabilities must have identical shapes")
    predictions = (y_probability >= threshold).astype(np.int8)
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_probability)),
    }
