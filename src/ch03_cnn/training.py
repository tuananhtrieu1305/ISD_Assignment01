"""CNN trainers: frozen core and canonical Adam, correct convolution slot layout."""

import time

import numpy as np

from src.ch02_ml.training import KerasTrainer, ScratchTrainer, TorchTrainer, validate_state
from src.common.contracts import canonical_sha256
from src.common.native_training import NativeAdam
from src.common.numpy_engine import loss_and_gradient
from src.common.training_core import EarlyStopping, batch_order


class CnnScratchTrainer(ScratchTrainer):
    """Manual conv/pool/backward/Adam inherited from locked NumPy core."""


class CnnTorchTrainer(TorchTrainer):
    def __init__(self, plan, weights, device="cpu"):
        super().__init__(plan, weights, device)

    def export_state(self):
        m, v = {}, {}
        weights = self.weights()
        for name, param, kind, key in self.model.parameter_pairs():
            state = self.optimizer.optimizer.state.get(param, {})
            for field, destination in (("exp_avg", m), ("exp_avg_sq", v)):
                value = state[field].detach().cpu().numpy() if state else None
                if value is not None and key == "w":
                    value = value.transpose(2, 3, 1, 0) if kind == "conv2d" else value.T
                destination[name] = (
                    np.ascontiguousarray(value) if value is not None else np.zeros_like(weights[name])
                )
        return {"weights": weights, "m": m, "v": v, "iterations": self.iterations}

    def restore_state(self, state):
        validate_state(state, self.weights())
        self.assign(state["weights"])
        torch = self.model.torch
        for name, param, kind, key in self.model.parameter_pairs():
            target = self.optimizer.optimizer.state[param]
            target["step"] = torch.tensor(float(state["iterations"]), dtype=torch.float32)
            for field, source in (("exp_avg", "m"), ("exp_avg_sq", "v")):
                value = state[source][name]
                if key == "w":
                    value = value.transpose(3, 2, 0, 1) if kind == "conv2d" else value.T
                target[field] = torch.as_tensor(
                    np.ascontiguousarray(value), dtype=param.dtype, device=self.model.device
                ).clone()


class CnnKerasTrainer(KerasTrainer):
    def __init__(self, plan, weights, device="gpu"):
        from src.common.backend_models import KerasBackend

        self.model = KerasBackend(plan, weights, device)
        self.optimizer = NativeAdam(self.model)
        tf = self.model.tf
        with tf.device(self.model.device):
            self.step_counter = tf.Variable(0, dtype=tf.int64, trainable=False)
        signature = [
            tf.TensorSpec([None, *plan["input_shape"]], tf.float32),
            tf.TensorSpec([None], tf.int64),
            tf.TensorSpec([None], tf.float32),
        ]
        self._steps = {"multiclass": tf.function(self._cnn_step, input_signature=signature, autograph=False)}
        self._predict = tf.function(
            lambda x: self.model.model(x, training=False), input_signature=[signature[0]], autograph=False
        )

    def _cnn_step(self, x, y, sample_weight):
        tf, optimizer = self.model.tf, self.optimizer
        with tf.device(self.model.device):
            tf.debugging.assert_all_finite(sample_weight, "Nonfinite weights")
            tf.debugging.assert_non_negative(sample_weight)
            tf.debugging.assert_positive(tf.reduce_sum(sample_weight))
            tf.debugging.assert_equal(tf.shape(x)[0], tf.shape(y)[0])
            tf.debugging.assert_equal(tf.shape(y)[0], tf.shape(sample_weight)[0])
            with tf.GradientTape() as tape:
                logits = self.model.model(x, training=True)
                rows = tf.nn.sparse_softmax_cross_entropy_with_logits(labels=y, logits=logits)
                loss = tf.reduce_sum(rows * sample_weight) / tf.reduce_sum(sample_weight)
            tf.debugging.assert_all_finite(loss, "Nonfinite loss")
            gradients = tape.gradient(loss, optimizer.variables)
            for g in gradients:
                tf.debugging.assert_all_finite(g, "Nonfinite gradient")
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


def probabilities(logits):
    values = np.asarray(logits)
    if values.ndim != 2 or not len(values) or not np.isfinite(values).all():
        raise ValueError("Invalid multiclass logits")
    exp = np.exp(values - values.max(axis=1, keepdims=True))
    return exp / exp.sum(axis=1, keepdims=True)


def predict_images(trainer, cache, ids, batch_size=16):
    if not ids or batch_size < 1:
        raise ValueError("Empty prediction or invalid batch size")
    outputs = [
        trainer.predict(cache.batch(ids[i : i + batch_size])[0]) for i in range(0, len(ids), batch_size)
    ]
    result = np.concatenate(outputs)
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite CNN output")
    return result


def fit_images(
    trainer, cache, train_ids, validation_ids, *, seed, budget, class_weights=None, progress=None, resume=None
):
    """Materialize float32 batches only; checkpoint/validation included in wall time."""
    stop = EarlyStopping(budget["patience"], budget["min_delta"])
    history, best, elapsed = [], None, 0.0
    if resume is not None:
        trainer.restore_state(resume["trainer"])
        history, best, elapsed = resume["history"].copy(), resume["best_weights"], resume["elapsed_seconds"]
        for key, value in resume["early_stopping"].items():
            setattr(stop, key, value)
    val_y = np.asarray([cache.labels[cache.positions[k]] for k in validation_ids])

    def sample_weights(y):
        return (
            np.ones(len(y), dtype="float32")
            if class_weights is None
            else np.asarray([class_weights[str(int(v))] for v in y], dtype="float32")
        )

    started = time.perf_counter()
    for epoch in range(len(history), budget["max_epochs"]):
        if stop.bad_epochs >= stop.patience:
            break
        orders = batch_order(len(train_ids), budget["batch_size"], seed, epoch)
        loss_sum, weight_sum, norms = 0.0, 0.0, []
        for positions in orders:
            if elapsed + time.perf_counter() - started > budget["wall_time_limit_minutes"] * 60:
                raise TimeoutError("Locked CNN wall-time budget exceeded")
            x, y = cache.batch([train_ids[int(i)] for i in positions])
            sw = sample_weights(y)
            output = trainer.step(x, y, "multiclass", sw)
            batch_weight = float(sw.sum())
            loss_sum += output["loss"] * batch_weight
            weight_sum += batch_weight
            norms.append(output["gradient_global_norm_before_clip"])
        logits = predict_images(trainer, cache, validation_ids, budget["batch_size"])
        val_loss = loss_and_gradient(logits, val_y, "multiclass", sample_weights(val_y))[0]
        improved, terminate = stop.observe(val_loss, epoch)
        if improved:
            best = trainer.weights()
        history.append(
            {
                "epoch": epoch,
                "train_loss": loss_sum / weight_sum,
                "validation_loss": val_loss,
                "gradient_norm_mean": float(np.mean(norms)),
                "gradient_norm_max": float(np.max(norms)),
                "batch_order_sha256": canonical_sha256(orders),
                "augmentation": "none",
            }
        )
        if progress:
            progress(
                {
                    "history": history.copy(),
                    "best_weights": best,
                    "early_stopping": {
                        key: getattr(stop, key)
                        for key in ("best", "best_epoch", "bad_epochs", "patience_reference")
                    },
                    "trainer": trainer.export_state(),
                    "elapsed_seconds": elapsed + time.perf_counter() - started,
                }
            )
        print(
            f"epoch={epoch + 1} train_loss={history[-1]['train_loss']:.6f} validation_loss={val_loss:.6f} best_epoch={stop.best_epoch + 1}",
            flush=True,
        )
        if terminate:
            break
    if best is None:
        raise ValueError("No finite validation-selected CNN weights")
    trainer.assign(best)
    return {
        "history": history,
        "best_epoch": stop.best_epoch,
        "best_validation_loss": stop.best,
        "weights": best,
        "train_seconds": elapsed + time.perf_counter() - started,
        "optimizer_steps": trainer.iterations,
    }
