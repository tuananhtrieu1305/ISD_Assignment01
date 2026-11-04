"""Reusable Keras components for the A06 stock Vanilla RNN."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tensorflow import keras


def validate_stock_arrays(features: np.ndarray, scaled_targets: np.ndarray) -> None:
    """Validate the finalized stock sequence contract without changing data."""

    x = np.asarray(features)
    y = np.asarray(scaled_targets)
    if x.ndim != 3 or x.shape[1:] != (30, 5):
        raise ValueError("stock X must have shape (samples, 30, 5)")
    if y.ndim != 1 or len(x) != len(y):
        raise ValueError("stock y must be one-dimensional and align with X")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("stock features and targets must be finite")


def build_stock_rnn(
    *,
    input_shape: tuple[int, int] = (30, 5),
    hidden_units: int = 64,
    learning_rate: float = 1e-3,
) -> keras.Model:
    """Build and compile the Keras SimpleRNN linear-regression baseline."""

    if input_shape != (30, 5):
        raise ValueError("input_shape must remain (30, 5) for A06 stock data")
    if hidden_units <= 0 or learning_rate <= 0:
        raise ValueError("hidden_units and learning_rate must be positive")

    model = keras.Sequential(
        [
            keras.Input(shape=input_shape, name="stock_sequence"),
            keras.layers.SimpleRNN(hidden_units, activation="tanh", name="simple_rnn"),
            keras.layers.Dense(1, activation="linear", name="scaled_close"),
        ],
        name="keras_stock_vanilla_rnn",
    )
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="mse",
    )
    return model


def build_callbacks(
    model_path: Path,
    *,
    patience: int = 5,
    min_delta: float = 1e-4,
) -> list[keras.callbacks.Callback]:
    """Create validation-loss callbacks that restore and save the best model."""

    if patience <= 0 or min_delta < 0:
        raise ValueError("patience must be positive and min_delta non-negative")
    destination = Path(model_path)
    if destination.suffix != ".keras":
        raise ValueError("Keras model path must end with .keras")
    destination.parent.mkdir(parents=True, exist_ok=True)
    return [
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            mode="min",
            patience=patience,
            min_delta=min_delta,
            restore_best_weights=True,
            verbose=1,
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=str(destination),
            monitor="val_loss",
            mode="min",
            save_best_only=True,
            save_weights_only=False,
            verbose=0,
        ),
    ]


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
