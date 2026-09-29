"""Tests for the PyTorch customer Vanilla RNN milestone."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

import src.pytorch_customer as customer_training_module
from src.pytorch_customer import (
    CustomerRNN,
    CustomerSequenceDataset,
    binary_classification_metrics,
    compute_positive_weight,
    count_trainable_parameters,
    predict_probabilities,
    train_with_early_stopping,
)


def _tiny_loader(*, shuffle: bool = False) -> DataLoader:
    rng = np.random.default_rng(42)
    x = rng.normal(size=(16, 8, 5)).astype(np.float32)
    y = np.array([0, 1] * 8, dtype=np.int8)
    return DataLoader(CustomerSequenceDataset(x, y), batch_size=4, shuffle=shuffle)


def test_dataset_returns_float_tensors_with_expected_shape() -> None:
    loader = _tiny_loader()
    features, labels = next(iter(loader))

    assert features.shape == (4, 8, 5)
    assert labels.shape == (4,)
    assert features.dtype == torch.float32
    assert labels.dtype == torch.float32


def test_rnn_forward_returns_one_logit_per_sequence_without_sigmoid() -> None:
    model = CustomerRNN(input_size=5, hidden_size=64, num_layers=1)
    logits = model(torch.zeros(7, 8, 5))

    assert logits.shape == (7,)
    assert model.rnn.batch_first is True
    assert model.rnn.num_layers == 1
    assert not any(isinstance(module, nn.Sigmoid) for module in model.modules())
    assert count_trainable_parameters(model) == 4609


def test_positive_weight_uses_only_labels_passed_by_caller() -> None:
    train_y = np.array([0, 0, 0, 1], dtype=np.int8)
    unrelated_future_y = np.ones(100, dtype=np.int8)

    assert compute_positive_weight(train_y) == 3.0
    assert compute_positive_weight(train_y) != compute_positive_weight(
        np.concatenate([train_y, unrelated_future_y])
    )


def test_early_stopping_restores_best_checkpoint(tmp_path: Path) -> None:
    torch.manual_seed(42)
    model = CustomerRNN(input_size=5, hidden_size=4, num_layers=1)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.0)
    criterion = nn.BCEWithLogitsLoss()
    checkpoint_path = tmp_path / "best.pt"

    result = train_with_early_stopping(
        model=model,
        train_loader=_tiny_loader(shuffle=True),
        validation_loader=_tiny_loader(),
        criterion=criterion,
        optimizer=optimizer,
        device=torch.device("cpu"),
        checkpoint_path=checkpoint_path,
        max_epochs=10,
        patience=2,
        min_delta=0.0,
        gradient_clip_norm=1.0,
        seed=42,
        verbose=False,
    )

    assert checkpoint_path.is_file()
    assert result["epochs_ran"] == 3
    assert result["best_epoch"] == 1
    assert len(result["history"]["train_loss"]) == 3
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    assert checkpoint["best_epoch"] == 1
    for name, value in model.state_dict().items():
        torch.testing.assert_close(value, checkpoint["model_state_dict"][name])


def test_sub_min_delta_raw_improvement_still_updates_best_checkpoint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    torch.manual_seed(42)
    model = CustomerRNN(input_size=5, hidden_size=4)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.0)
    validation_losses = iter([1.00, 0.95, 0.96])
    monkeypatch.setattr(
        customer_training_module,
        "_average_loss",
        lambda *args, **kwargs: next(validation_losses),
    )

    result = train_with_early_stopping(
        model=model,
        train_loader=_tiny_loader(),
        validation_loader=_tiny_loader(),
        criterion=nn.BCEWithLogitsLoss(),
        optimizer=optimizer,
        device=torch.device("cpu"),
        checkpoint_path=tmp_path / "best.pt",
        max_epochs=5,
        patience=2,
        min_delta=0.10,
        verbose=False,
    )

    assert result["epochs_ran"] == 3
    assert result["best_epoch"] == 2
    assert result["best_validation_loss"] == 0.95


def test_prediction_and_metrics_are_well_formed() -> None:
    torch.manual_seed(42)
    model = CustomerRNN(input_size=5, hidden_size=4)
    labels, probabilities = predict_probabilities(
        model,
        _tiny_loader(),
        device=torch.device("cpu"),
    )
    metrics = binary_classification_metrics(labels, probabilities, threshold=0.5)

    assert labels.shape == probabilities.shape == (16,)
    assert np.logical_and(probabilities >= 0, probabilities <= 1).all()
    assert set(metrics) == {"accuracy", "precision", "recall", "f1", "roc_auc"}
    assert all(0.0 <= value <= 1.0 for value in metrics.values())
