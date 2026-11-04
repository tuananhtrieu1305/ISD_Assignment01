"""Chapter2 matched trainers; reuse frozen Phase25 models, not legacy notebooks."""

from __future__ import annotations

import time

import numpy as np

from src.common.contracts import canonical_sha256
from src.common.native_training import NativeAdam
from src.common.numpy_engine import NumpyNetwork, loss_and_gradient, sigmoid
from src.common.training_core import Adam, EarlyStopping, batch_order, clip_gradients


def validate_weights(weights, reference):
    if set(weights) != set(reference) or any(
        np.asarray(weights[key]).shape != reference[key].shape
        or np.asarray(weights[key]).dtype != reference[key].dtype
        or not np.isfinite(weights[key]).all()
        for key in reference
    ):
        raise ValueError("Weight keys/shapes/dtypes/finite values mismatch")


def validate_state(state, reference):
    if (
        set(state) != {"weights", "m", "v", "iterations"}
        or not isinstance(state["iterations"], int)
        or state["iterations"] < 0
    ):
        raise ValueError("Invalid optimizer state")
    for field in ("weights", "m", "v"):
        validate_weights(state[field], reference)


class ScratchTrainer:
    def __init__(self, plan, weights):
        self.model = NumpyNetwork(plan, weights)
        self.optimizer = Adam(self.model.weights)

    @property
    def iterations(self):
        return self.optimizer.t

    def predict(self, x):
        return self.model.forward(x)

    def weights(self):
        return {k: v.copy() for k, v in self.model.weights.items()}

    def assign(self, weights):
        validate_weights(weights, self.model.weights)
        for key, value in weights.items():
            self.model.weights[key][...] = value

    def step(self, x, y, task, sample_weight):
        loss, grad, _ = self.model.loss_gradients(x, y, task, sample_weight)
        grad, norm = clip_gradients(grad)
        self.optimizer.step(self.model.weights, grad)
        return {"loss": loss, "gradient_global_norm_before_clip": norm}

    def export_state(self):
        return {
            "weights": self.weights(),
            "m": {k: v.copy() for k, v in self.optimizer.m.items()},
            "v": {k: v.copy() for k, v in self.optimizer.v.items()},
            "iterations": self.iterations,
        }

    def restore_state(self, state):
        validate_state(state, self.model.weights)
        self.assign(state["weights"])
        for attr in ("m", "v"):
            if set(state[attr]) != set(self.model.weights):
                raise ValueError("Adam slot keys mismatch")
            setattr(self.optimizer, attr, {k: np.asarray(v).copy() for k, v in state[attr].items()})
        self.optimizer.t = int(state["iterations"])


class TorchTrainer:
    def __init__(self, plan, weights, device="gpu"):
        from src.common.backend_models import TorchBackend

        self.model = TorchBackend(plan, weights, device)
        self.optimizer = NativeAdam(self.model)

    @property
    def iterations(self):
        values = list(self.optimizer.optimizer.state.values())
        return int(values[0]["step"].item()) if values else 0

    def predict(self, x):
        return self.model.predict(x)

    def weights(self):
        return self.optimizer.weights()

    def assign(self, weights):
        self.model.assign(weights)

    def step(self, x, y, task, sample_weight):
        return self.optimizer.step(x, y, task, sample_weight)

    def export_state(self):
        m = {}
        v = {}
        for name, param, kind, key in self.model.parameter_pairs():
            state = self.optimizer.optimizer.state.get(param, {})
            for field, destination in (("exp_avg", m), ("exp_avg_sq", v)):
                array = (
                    state[field].detach().cpu().numpy().T
                    if state and key == "w"
                    else state[field].detach().cpu().numpy()
                    if state
                    else np.zeros_like(self.weights()[name])
                )
                destination[name] = np.ascontiguousarray(array)
        return {"weights": self.weights(), "m": m, "v": v, "iterations": self.iterations}

    def restore_state(self, state):
        validate_state(state, self.weights())
        self.assign(state["weights"])
        torch = self.model.torch
        for name, param, kind, key in self.model.parameter_pairs():
            target = self.optimizer.optimizer.state[param]
            target["step"] = torch.tensor(float(state["iterations"]), dtype=torch.float32)
            for field, source in (("exp_avg", "m"), ("exp_avg_sq", "v")):
                value = state[source][name].T if key == "w" else state[source][name]
                target[field] = torch.as_tensor(
                    np.ascontiguousarray(value), dtype=param.dtype, device=self.model.device
                ).clone()


class KerasTrainer:
    """Keras model + TensorFlow graph step, canonical Adam (not stock epsilon-hat)."""

    def __init__(self, plan, weights, device="gpu"):
        from src.common.backend_models import KerasBackend

        self.model = KerasBackend(plan, weights, device)
        self.optimizer = NativeAdam(self.model)
        tf = self.model.tf
        with tf.device(self.model.device):
            self.step_counter = tf.Variable(0, dtype=tf.int64, trainable=False)
        signature = [
            tf.TensorSpec([None, plan["input_shape"][0]], tf.float32),
            tf.TensorSpec([None, 1], tf.float32),
            tf.TensorSpec([None], tf.float32),
        ]
        self._steps = {
            task: tf.function(self._graph_step(task), input_signature=signature, autograph=False)
            for task in ("mse", "binary")
        }
        self._predict = tf.function(
            lambda x: self.model.model(x, training=False), input_signature=[signature[0]], autograph=False
        )

    def _graph_step(self, task):
        tf = self.model.tf
        optimizer = self.optimizer

        def step(x, y, sample_weight):
            tf.debugging.assert_all_finite(sample_weight, "Nonfinite sample weights")
            tf.debugging.assert_non_negative(sample_weight)
            tf.debugging.assert_positive(tf.reduce_sum(sample_weight))
            tf.debugging.assert_equal(tf.shape(x)[0], tf.shape(sample_weight)[0])
            tf.debugging.assert_equal(tf.shape(x)[0], tf.shape(y)[0])
            with tf.device(self.model.device), tf.GradientTape() as tape:
                logits = self.model.model(x, training=True)
                rows = tf.reduce_mean(
                    tf.square(logits - y)
                    if task == "mse"
                    else tf.nn.sigmoid_cross_entropy_with_logits(labels=y, logits=logits),
                    axis=1,
                )
                loss = tf.reduce_sum(rows * sample_weight) / tf.reduce_sum(sample_weight)
            with tf.device(self.model.device):
                tf.debugging.assert_all_finite(loss, "Nonfinite loss")
                gradients = tape.gradient(loss, optimizer.variables)
                for gradient in gradients:
                    tf.debugging.assert_all_finite(gradient, "Nonfinite gradient")
                gradients, norm = tf.clip_by_global_norm(gradients, optimizer.max_norm)
                self.step_counter.assign_add(1)
                t = tf.cast(self.step_counter, tf.float64)
                for p, g, m, v in zip(optimizer.variables, gradients, optimizer.m, optimizer.v, strict=True):
                    m.assign(optimizer.b1 * m + (1 - optimizer.b1) * g)
                    v.assign(optimizer.b2 * v + (1 - optimizer.b2) * tf.square(g))
                    mhat = m / tf.cast(1 - tf.pow(tf.constant(optimizer.b1, tf.float64), t), tf.float32)
                    vhat = v / tf.cast(1 - tf.pow(tf.constant(optimizer.b2, tf.float64), t), tf.float32)
                    p.assign_sub(optimizer.lr * mhat / (tf.sqrt(vhat) + optimizer.eps))
            return loss, norm

        return step

    @property
    def iterations(self):
        return int(self.step_counter.numpy())

    def predict(self, x):
        with self.model.tf.device(self.model.device):
            return self._predict(x).numpy()

    def weights(self):
        return self.optimizer.weights()

    def assign(self, weights):
        self.model.assign(weights)

    def step(self, x, y, task, sample_weight):
        if task not in self._steps:
            raise ValueError("Unknown MLP loss")
        loss, norm = self._steps[task](x, y, sample_weight)
        return {"loss": float(loss.numpy()), "gradient_global_norm_before_clip": float(norm.numpy())}

    def export_state(self):
        names = [name for name, _ in self.model.parameter_pairs()]
        return {
            "weights": self.weights(),
            "m": {k: v.numpy().copy() for k, v in zip(names, self.optimizer.m, strict=True)},
            "v": {k: v.numpy().copy() for k, v in zip(names, self.optimizer.v, strict=True)},
            "iterations": self.iterations,
        }

    def restore_state(self, state):
        validate_state(state, self.weights())
        self.assign(state["weights"])
        self.step_counter.assign(state["iterations"])
        for slots, field in ((self.optimizer.m, "m"), (self.optimizer.v, "v")):
            for (name, _), slot in zip(self.model.parameter_pairs(), slots, strict=True):
                slot.assign(state[field][name])


def predict_batches(trainer, x, batch_size=4096):
    if batch_size < 1 or len(x) == 0:
        raise ValueError("Invalid prediction batch")
    result = np.concatenate([trainer.predict(x[i : i + batch_size]) for i in range(0, len(x), batch_size)])
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite prediction")
    return result


def task_outputs(logits, task):
    if task == "mse":
        return logits
    if task != "binary":
        raise ValueError("Unknown MLP task")
    p = sigmoid(np.asarray(logits).reshape(-1))
    return np.column_stack([1 - p, p])


def fit(trainer, x, y, val_x, val_y, task, *, seed, budget, class_weights=None, progress=None, resume=None):
    stop = EarlyStopping(budget["patience"], budget["min_delta"])
    history = []
    best = None
    elapsed = 0.0
    if resume is not None:
        trainer.restore_state(resume["trainer"])
        history = resume["history"]
        best = resume["best_weights"]
        elapsed = resume["elapsed_seconds"]
        for name, value in resume["early_stopping"].items():
            setattr(stop, name, value)
    train_weights = (
        np.ones(len(y), dtype="float32")
        if class_weights is None
        else np.asarray([class_weights[str(int(value))] for value in y.reshape(-1)], dtype="float32")
    )
    val_weights = (
        np.ones(len(val_y), dtype="float32")
        if class_weights is None
        else np.asarray([class_weights[str(int(value))] for value in val_y.reshape(-1)], dtype="float32")
    )
    started = time.perf_counter()
    for epoch in range(len(history), budget["max_epochs"]):
        if stop.bad_epochs >= stop.patience:
            break
        order = batch_order(len(x), budget["batch_size"], seed, epoch)
        loss_sum = weight_sum = 0.0
        norms = []
        for positions in order:
            if elapsed + time.perf_counter() - started > budget["wall_time_limit_minutes"] * 60:
                raise TimeoutError("Locked wall-time budget exceeded")
            output = trainer.step(x[positions], y[positions], task, train_weights[positions])
            weight = float(train_weights[positions].sum())
            loss_sum += output["loss"] * weight
            weight_sum += weight
            norms.append(output["gradient_global_norm_before_clip"])
        val_logits = predict_batches(trainer, val_x)
        validation_loss = loss_and_gradient(val_logits, val_y, task, val_weights)[0]
        improved, terminate = stop.observe(validation_loss, epoch)
        if improved:
            best = trainer.weights()
        history.append(
            {
                "epoch": epoch,
                "train_loss": loss_sum / weight_sum,
                "validation_loss": validation_loss,
                "gradient_norm_mean": float(np.mean(norms)),
                "gradient_norm_max": float(np.max(norms)),
                "batch_order_sha256": canonical_sha256(order),
            }
        )
        if progress is not None:
            progress(
                {
                    "history": history,
                    "best_weights": best,
                    "early_stopping": {
                        "best": stop.best,
                        "best_epoch": stop.best_epoch,
                        "bad_epochs": stop.bad_epochs,
                        "patience_reference": stop.patience_reference,
                    },
                    "trainer": trainer.export_state(),
                    "elapsed_seconds": elapsed + time.perf_counter() - started,
                }
            )
        print(
            f"epoch={epoch + 1} train_loss={history[-1]['train_loss']:.6f} validation_loss={validation_loss:.6f} best_epoch={stop.best_epoch + 1}",
            flush=True,
        )
        if terminate:
            break
    if best is None:
        raise ValueError("No finite best checkpoint")
    elapsed += time.perf_counter() - started
    trainer.assign(best)
    return {
        "history": history,
        "best_epoch": stop.best_epoch,
        "best_validation_loss": stop.best,
        "weights": best,
        "train_seconds": elapsed,
        "optimizer_steps": trainer.iterations,
    }
