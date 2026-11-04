"""Keras implementation of the matched Chapter 4 Vanilla RNN."""

import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras


class KerasRNN:
    def __init__(
        self,
        input_size,
        hidden_size=32,
        task="binary",
        seed=42,
        learning_rate=0.003,
        gradient_clip_norm=1.0,
        model=None,
    ):
        if task not in {"binary", "regression"}:
            raise ValueError("task must be 'binary' or 'regression'")
        self.input_size = int(input_size)
        self.hidden_size = int(hidden_size)
        self.task = task
        self.seed = int(seed)
        self.learning_rate = float(learning_rate)
        self.gradient_clip_norm = float(gradient_clip_norm)
        keras.utils.set_random_seed(self.seed)
        if model is None:
            self.model = keras.Sequential(
                [
                    keras.layers.Input(shape=(None, self.input_size)),
                    keras.layers.SimpleRNN(self.hidden_size, activation="tanh"),
                    keras.layers.Dense(1),
                ]
            )
            loss = (
                keras.losses.BinaryCrossentropy(from_logits=True)
                if self.task == "binary"
                else keras.losses.MeanSquaredError()
            )
            self.model.compile(
                optimizer=keras.optimizers.Adam(
                    learning_rate=self.learning_rate, clipnorm=self.gradient_clip_norm
                ),
                loss=loss,
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
        epochs=30,
        batch_size=512,
        patience=5,
        min_delta=1e-4,
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
        validation = [float(value) for value in result.history["val_loss"]]
        return {
            "train_loss": [float(value) for value in result.history["loss"]],
            "val_loss": validation,
            "best_epoch": int(np.argmin(validation) + 1),
        }

    def predict_score(self, x, batch_size=2048):
        output = self.model.predict(
            np.asarray(x, dtype=np.float32), batch_size=int(batch_size), verbose=0
        ).reshape(-1)
        if self.task == "binary":
            return tf.math.sigmoid(output).numpy()
        return output

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(path)
        Path(str(path) + ".metadata.json").write_text(
            json.dumps(
                {
                    "input_size": self.input_size,
                    "hidden_size": self.hidden_size,
                    "task": self.task,
                    "seed": self.seed,
                    "learning_rate": self.learning_rate,
                    "gradient_clip_norm": self.gradient_clip_norm,
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
