"""Keras implementation of the matched Chapter 2 MLP."""

import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras


class KerasMLP:
    def __init__(
        self,
        input_dim,
        task,
        hidden=(64, 32),
        seed=42,
        learning_rate=0.01,
        l2=0.0,
        model=None,
    ):
        if task not in {"binary", "regression"}:
            raise ValueError("task must be 'binary' or 'regression'")
        self.input_dim = int(input_dim)
        self.task = task
        self.hidden = tuple(int(v) for v in hidden)
        self.seed = int(seed)
        self.learning_rate = float(learning_rate)
        self.l2 = float(l2)
        keras.utils.set_random_seed(self.seed)
        if model is None:
            regularizer = keras.regularizers.L2(self.l2) if self.l2 else None
            self.model = keras.Sequential(
                [
                    keras.layers.Input(shape=(self.input_dim,)),
                    keras.layers.Dense(
                        self.hidden[0], activation="relu", kernel_regularizer=regularizer
                    ),
                    keras.layers.Dense(
                        self.hidden[1], activation="relu", kernel_regularizer=regularizer
                    ),
                    keras.layers.Dense(1),
                ]
            )
            loss = (
                keras.losses.BinaryCrossentropy(from_logits=True)
                if self.task == "binary"
                else keras.losses.MeanSquaredError()
            )
            self.model.compile(optimizer=keras.optimizers.Adam(self.learning_rate), loss=loss)
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
        epochs=100,
        batch_size=512,
        patience=10,
        min_delta=1e-5,
        class_weight=None,
    ):
        callback = keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=int(patience),
            min_delta=float(min_delta),
            restore_best_weights=True,
        )
        history = self.model.fit(
            np.asarray(x_train, dtype=np.float32),
            np.asarray(y_train, dtype=np.float32),
            validation_data=(
                np.asarray(x_val, dtype=np.float32),
                np.asarray(y_val, dtype=np.float32),
            ),
            epochs=int(epochs),
            batch_size=int(batch_size),
            callbacks=[callback],
            class_weight=class_weight,
            verbose=0,
            shuffle=True,
        )
        return {
            "train_loss": [float(v) for v in history.history["loss"]],
            "val_loss": [float(v) for v in history.history["val_loss"]],
        }

    def predict_score(self, x):
        raw = self.model.predict(np.asarray(x, dtype=np.float32), verbose=0).reshape(-1)
        if self.task == "binary":
            return tf.math.sigmoid(raw).numpy()
        return raw

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(path)
        metadata_path = Path(str(path) + ".metadata.json")
        metadata_path.write_text(
            json.dumps(
                {
                    "input_dim": self.input_dim,
                    "task": self.task,
                    "hidden": list(self.hidden),
                    "seed": self.seed,
                    "learning_rate": self.learning_rate,
                    "l2": self.l2,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path):
        path = Path(path)
        metadata = json.loads(Path(str(path) + ".metadata.json").read_text(encoding="utf-8"))
        model = keras.models.load_model(path)
        return cls(model=model, **metadata)

