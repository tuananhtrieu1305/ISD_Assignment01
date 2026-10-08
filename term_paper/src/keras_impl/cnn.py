"""Keras implementation of the matched Chapter 3 CNN."""

import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras


class KerasCNN:
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
        keras.utils.set_random_seed(self.seed)
        if model is None:
            first, second = self.filters
            if self.mode == "2d":
                layers = [
                    keras.layers.Input(shape=self.input_shape),
                    keras.layers.Conv2D(first, self.kernel_size, padding="same", activation="relu"),
                    keras.layers.MaxPool2D(pool_size=2),
                    keras.layers.Conv2D(second, self.kernel_size, padding="same", activation="relu"),
                    keras.layers.GlobalAveragePooling2D(),
                    keras.layers.Dense(self.num_classes),
                ]
            else:
                layers = [
                    keras.layers.Input(shape=self.input_shape),
                    keras.layers.Conv1D(first, self.kernel_size, padding="same", activation="relu"),
                    keras.layers.MaxPool1D(pool_size=2),
                    keras.layers.Conv1D(second, self.kernel_size, padding="same", activation="relu"),
                    keras.layers.GlobalAveragePooling1D(),
                    keras.layers.Dense(self.num_classes),
                ]
            self.model = keras.Sequential(layers)
            self.model.compile(
                optimizer=keras.optimizers.Adam(self.learning_rate),
                loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            )
        else:
            self.model = model

    @property
    def parameter_count(self):
        return int(self.model.count_params())

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
        callback = keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=int(patience),
            min_delta=float(min_delta),
            restore_best_weights=True,
        )
        result = self.model.fit(
            np.asarray(x_train, dtype=np.float32),
            np.asarray(y_train, dtype=np.int64),
            validation_data=(
                np.asarray(x_val, dtype=np.float32),
                np.asarray(y_val, dtype=np.int64),
            ),
            epochs=int(epochs),
            batch_size=int(batch_size),
            callbacks=[callback],
            class_weight=class_weight,
            verbose=0,
            shuffle=True,
        )
        validation = [float(value) for value in result.history["val_loss"]]
        return {
            "train_loss": [float(value) for value in result.history["loss"]],
            "val_loss": validation,
            "best_epoch": int(np.argmin(validation) + 1),
        }

    def predict_proba(self, x, batch_size=128):
        logits = self.model.predict(
            np.asarray(x, dtype=np.float32), batch_size=int(batch_size), verbose=0
        )
        return tf.nn.softmax(logits, axis=1).numpy()

    def predict(self, x, batch_size=128):
        return np.argmax(self.predict_proba(x, batch_size=batch_size), axis=1)

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(path)
        Path(str(path) + ".metadata.json").write_text(
            json.dumps(
                {
                    "input_shape": list(self.input_shape),
                    "num_classes": self.num_classes,
                    "mode": self.mode,
                    "filters": list(self.filters),
                    "kernel_size": self.kernel_size,
                    "seed": self.seed,
                    "learning_rate": self.learning_rate,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path):
        path = Path(path)
        metadata = json.loads(Path(str(path) + ".metadata.json").read_text(encoding="utf-8"))
        return cls(model=keras.models.load_model(path), **metadata)
