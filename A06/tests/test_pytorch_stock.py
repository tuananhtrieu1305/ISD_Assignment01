"""Tests for the PyTorch stock Vanilla RNN milestone."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader

import src.pytorch_stock as stock_training_module
from src.pytorch_stock import (
    StockRNN,
    StockSequenceDataset,
    count_trainable_parameters,
    inverse_transform_targets,
    predict_scaled_targets,
    regression_metrics,
    train_with_early_stopping,
)


def _tiny_loader(*, shuffle: bool = False) -> DataLoader:
    rng = np.random.default_rng(42)
    x = rng.normal(size=(16, 30, 5)).astype(np.float32)
    y = rng.normal(size=16).astype(np.float32)
    return DataLoader(StockSequenceDataset(x, y), batch_size=4, shuffle=shuffle)


def test_dataset_returns_float_tensors_with_expected_shape() -> None:
    features, targets = next(iter(_tiny_loader()))

    assert features.shape == (4, 30, 5)
    assert targets.shape == (4,)
    assert features.dtype == torch.float32
    assert targets.dtype == torch.float32


def test_rnn_forward_returns_one_regression_value_per_sequence() -> None:
    model = StockRNN(input_size=5, hidden_size=64, num_layers=1)
    predictions = model(torch.zeros(7, 30, 5))

    assert predictions.shape == (7,)
    assert model.rnn.batch_first is True
    assert model.rnn.num_layers == 1
    assert isinstance(model.rnn, nn.RNN)
    assert not any(isinstance(module, (nn.LSTM, nn.GRU)) for module in model.modules())
    assert count_trainable_parameters(model) == 4609


def test_inverse_transform_targets_restores_original_scale() -> None:
    raw = np.array([10.0, 20.0, 40.0], dtype=np.float64)
    scaler = StandardScaler().fit(raw.reshape(-1, 1))
    scaled = scaler.transform(raw.reshape(-1, 1)).ravel()

    np.testing.assert_allclose(inverse_transform_targets(scaler, scaled), raw)


def test_regression_metrics_have_expected_values() -> None:
    actual = np.array([10.0, 20.0, 30.0])
    predicted = np.array([12.0, 18.0, 30.0])
    metrics = regression_metrics(actual, predicted)

    assert metrics["mae"] == 4.0 / 3.0
    assert np.isclose(metrics["rmse"], np.sqrt(8.0 / 3.0))
    assert np.isclose(metrics["r2"], 0.96)


def test_early_stopping_restores_raw_best_checkpoint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    torch.manual_seed(42)
    model = StockRNN(input_size=5, hidden_size=4)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.0)
    validation_losses = iter([1.00, 0.95, 0.96])
    monkeypatch.setattr(
        stock_training_module,
        "_average_loss",
        lambda *args, **kwargs: next(validation_losses),
    )

    result = train_with_early_stopping(
        model=model,
        train_loader=_tiny_loader(),
        validation_loader=_tiny_loader(),
        criterion=nn.MSELoss(),
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
    checkpoint = torch.load(tmp_path / "best.pt", map_location="cpu", weights_only=True)
    for name, value in model.state_dict().items():
        torch.testing.assert_close(value, checkpoint["model_state_dict"][name])


def test_prediction_returns_scaled_targets_in_loader_order() -> None:
    torch.manual_seed(42)
    labels, predictions = predict_scaled_targets(
        StockRNN(input_size=5, hidden_size=4),
        _tiny_loader(),
        device=torch.device("cpu"),
    )

    assert labels.shape == predictions.shape == (16,)
    assert np.isfinite(labels).all()
    assert np.isfinite(predictions).all()
