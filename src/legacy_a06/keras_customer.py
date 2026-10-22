"""Reusable Keras components for the A06 customer Vanilla RNN."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from tensorflow import keras


def validate_customer_arrays(features: np.ndarray, labels: np.ndarray) -> None:
    """Validate the finalized customer sequence contract without changing data."""

    x = np.asarray(features)
    y = np.asarray(labels)
    if x.ndim != 3 or x.shape[1:] != (8, 5):
        raise ValueError("customer X must have shape (samples, 8, 5)")
    if y.ndim != 1 or len(x) != len(y):
        raise ValueError("customer y must be one-dimensional and align with X")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("customer features and labels must be finite")
    if not np.isin(y, [0, 1]).all():
        raise ValueError("customer labels must be binary")


def build_customer_rnn(
    *,
    input_shape: tuple[int, int] = (8, 5),
    hidden_units: int = 64,
    learning_rate: float = 1e-3,
) -> keras.Model:
    """Build and compile the Keras SimpleRNN binary-classification baseline."""

    if input_shape != (8, 5):
        raise ValueError("input_shape must remain (8, 5) for A06 customer data")
    if hidden_units <= 0 or learning_rate <= 0:
        raise ValueError("hidden_units and learning_rate must be positive")

    model = keras.Sequential(
        [
            keras.Input(shape=input_shape, name="customer_sequence"),
            keras.layers.SimpleRNN(hidden_units, activation="tanh", name="simple_rnn"),
            keras.layers.Dense(1, activation="sigmoid", name="purchase_probability"),
        ],
        name="keras_customer_vanilla_rnn",
    )
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
    )
    return model


def compute_class_weight(train_labels: np.ndarray) -> dict[int, float]:
    """Return Keras class weights from the supplied TRAIN labels only."""

    labels = np.asarray(train_labels)
    negatives = int(np.count_nonzero(labels == 0))
    positives = int(np.count_nonzero(labels == 1))
    if negatives == 0 or positives == 0 or negatives + positives != len(labels):
        raise ValueError("train_labels must contain both binary classes and no other values")
    return {0: 1.0, 1: negatives / positives}


def make_sample_weights(
    labels: np.ndarray,
    class_weight: dict[int, float],
) -> np.ndarray:
    """Map binary labels to weights fixed from TRAIN without recomputing them."""

    y = np.asarray(labels)
    if y.ndim != 1 or not np.isin(y, [0, 1]).all():
        raise ValueError("labels must be a one-dimensional binary array")
    if set(class_weight) != {0, 1} or min(class_weight.values()) <= 0:
        raise ValueError("class_weight must provide positive weights for classes 0 and 1")
    return np.where(y == 1, class_weight[1], class_weight[0]).astype(np.float32)


def build_callbacks(
    model_path: Path,
    *,
    patience: int = 5,
    min_delta: float = 1e-4,
) -> list[keras.callbacks.Callback]:
    """Create validation-loss callbacks that restore and persist the best model."""

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


def binary_classification_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    *,
    threshold: float = 0.5,
) -> dict[str, float]:
    """Calculate fixed-threshold classification metrics and ROC-AUC."""

    y_true = np.asarray(labels).astype(np.int8)
    y_probability = np.asarray(probabilities, dtype=np.float64)
    if y_true.ndim != 1 or y_true.shape != y_probability.shape:
        raise ValueError("labels and probabilities must be aligned one-dimensional arrays")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must lie in [0, 1]")
    predictions = (y_probability >= threshold).astype(np.int8)
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_probability)),
    }
