"""Tests for the Keras customer Vanilla RNN milestone."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from tensorflow import keras

from src.keras_customer import (
    binary_classification_metrics,
    build_callbacks,
    build_customer_rnn,
    compute_class_weight,
    make_sample_weights,
    validate_customer_arrays,
)


def test_validate_customer_arrays_accepts_locked_shape_and_binary_target() -> None:
    x = np.zeros((7, 8, 5), dtype=np.float32)
    y = np.array([0, 1, 0, 1, 0, 0, 1], dtype=np.int8)

    validate_customer_arrays(x, y)


def test_validate_customer_arrays_rejects_wrong_sequence_shape() -> None:
    with pytest.raises(ValueError, match="shape"):
        validate_customer_arrays(np.zeros((7, 7, 5)), np.zeros(7))


def test_model_is_equivalent_simple_rnn_sigmoid_baseline() -> None:
    model = build_customer_rnn(input_shape=(8, 5), hidden_units=64, learning_rate=1e-3)

    assert model.input_shape == (None, 8, 5)
    assert model.output_shape == (None, 1)
    assert isinstance(model.layers[0], keras.layers.SimpleRNN)
    assert model.layers[0].units == 64
    assert isinstance(model.layers[1], keras.layers.Dense)
    assert model.layers[1].units == 1
    assert model.layers[1].activation.__name__ == "sigmoid"
    assert model.count_params() == 4545
    assert model.loss == "binary_crossentropy"


def test_class_weight_uses_only_supplied_train_labels() -> None:
    train_y = np.array([0, 0, 0, 1], dtype=np.int8)
    unrelated_future_y = np.ones(100, dtype=np.int8)

    assert compute_class_weight(train_y) == {0: 1.0, 1: 3.0}
    assert compute_class_weight(train_y) != compute_class_weight(
        np.concatenate([train_y, unrelated_future_y])
    )


def test_validation_sample_weights_reuse_train_derived_class_weight() -> None:
    labels = np.array([0, 1, 1, 0], dtype=np.int8)
    weights = make_sample_weights(labels, {0: 1.0, 1: 3.0})

    np.testing.assert_array_equal(weights, np.array([1.0, 3.0, 3.0, 1.0], dtype=np.float32))


def test_callbacks_restore_best_weights_and_save_best_model(tmp_path: Path) -> None:
    callbacks = build_callbacks(tmp_path / "best.keras", patience=5, min_delta=1e-4)

    early_stopping = next(cb for cb in callbacks if isinstance(cb, keras.callbacks.EarlyStopping))
    checkpoint = next(cb for cb in callbacks if isinstance(cb, keras.callbacks.ModelCheckpoint))
    assert early_stopping.monitor == "val_loss"
    assert early_stopping.patience == 5
    assert early_stopping.restore_best_weights is True
    assert checkpoint.monitor == "val_loss"
    assert checkpoint.save_best_only is True


def test_metrics_use_fixed_threshold_and_return_required_names() -> None:
    labels = np.array([0, 0, 1, 1], dtype=np.int8)
    probabilities = np.array([0.1, 0.7, 0.8, 0.2])
    metrics = binary_classification_metrics(labels, probabilities, threshold=0.5)

    assert set(metrics) == {"accuracy", "precision", "recall", "f1", "roc_auc"}
    assert metrics["accuracy"] == 0.5
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5
    assert metrics["roc_auc"] == 0.75
