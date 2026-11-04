"""Tests for the Keras stock Vanilla RNN milestone."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from sklearn.preprocessing import StandardScaler
from tensorflow import keras

from src.keras_stock import (
    build_callbacks,
    build_stock_rnn,
    inverse_transform_targets,
    regression_metrics,
    validate_stock_arrays,
)


def test_validate_stock_arrays_accepts_locked_shape_and_target() -> None:
    x = np.zeros((7, 30, 5), dtype=np.float32)
    y = np.linspace(-1, 1, 7, dtype=np.float32)

    validate_stock_arrays(x, y)


def test_validate_stock_arrays_rejects_wrong_sequence_shape() -> None:
    with pytest.raises(ValueError, match="shape"):
        validate_stock_arrays(np.zeros((7, 29, 5)), np.zeros(7))


def test_model_is_simple_rnn_with_linear_regression_head() -> None:
    model = build_stock_rnn(input_shape=(30, 5), hidden_units=64, learning_rate=1e-3)

    assert model.input_shape == (None, 30, 5)
    assert model.output_shape == (None, 1)
    assert isinstance(model.layers[0], keras.layers.SimpleRNN)
    assert model.layers[0].units == 64
    assert isinstance(model.layers[1], keras.layers.Dense)
    assert model.layers[1].units == 1
    assert model.layers[1].activation.__name__ == "linear"
    assert model.count_params() == 4545
    assert model.loss == "mse"


def test_inverse_transform_targets_restores_price_scale() -> None:
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


def test_callbacks_restore_and_save_best_validation_model(tmp_path: Path) -> None:
    callbacks = build_callbacks(tmp_path / "best.keras", patience=5, min_delta=1e-4)

    early_stopping = next(cb for cb in callbacks if isinstance(cb, keras.callbacks.EarlyStopping))
    checkpoint = next(cb for cb in callbacks if isinstance(cb, keras.callbacks.ModelCheckpoint))
    assert early_stopping.monitor == "val_loss"
    assert early_stopping.patience == 5
    assert early_stopping.restore_best_weights is True
    assert checkpoint.monitor == "val_loss"
    assert checkpoint.save_best_only is True
