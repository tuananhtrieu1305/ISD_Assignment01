"""Canonical recurrent Adam states and batch-only RNN training; no TEST API."""

import time

import numpy as np

from src.ch02_ml.training import KerasTrainer, TorchTrainer, validate_state
from src.common.contracts import canonical_sha256
from src.common.native_training import NativeAdam
from src.common.numpy_engine import loss_and_gradient
from src.common.training_core import EarlyStopping, batch_order


class RnnTorchTrainer(TorchTrainer):
    def export_state(self):
        weights, slots = self.weights(), {"m": {}, "v": {}}
        for name, param, _, key in self.model.parameter_pairs():
            state = self.optimizer.optimizer.state.get(param, {})
            for destination, field in (("m", "exp_avg"), ("v", "exp_avg_sq")):
                value = state[field].detach().cpu().numpy() if state else np.zeros_like(weights[name])
                if state and key in {"w", "u"}:
                    value = value.T
                slots[destination][name] = np.ascontiguousarray(value)
        return {"weights": weights, **slots, "iterations": self.iterations}

    def restore_state(self, state):
        validate_state(state, self.weights())
        self.assign(state["weights"])
        torch = self.model.torch
        for name, param, _, key in self.model.parameter_pairs():
            target = self.optimizer.optimizer.state[param]
            target["step"] = torch.tensor(float(state["iterations"]), dtype=torch.float32)
            for field, source in (("exp_avg", "m"), ("exp_avg_sq", "v")):
                value = state[source][name].T if key in {"w", "u"} else state[source][name]
                target[field] = torch.as_tensor(
                    np.ascontiguousarray(value), dtype=param.dtype, device=self.model.device
                ).clone()


class RnnKerasTrainer(KerasTrainer):
    def __init__(self, plan, weights, device="gpu", jit_compile=True):
        from src.common.backend_models import KerasBackend

        self.model = KerasBackend(plan, weights, device)
        self.optimizer = NativeAdam(self.model)
        tf = self.model.tf
        with tf.device(self.model.device):
            self.step_counter = tf.Variable(0, dtype=tf.int64, trainable=False)
        signature = [
            tf.TensorSpec([None, *plan["input_shape"]], tf.float32),
            tf.TensorSpec([None, *plan["output_shape"]], tf.float32),
            tf.TensorSpec([None], tf.float32),
        ]
        self._steps = {
            "mse": tf.function(
                self._graph_step("mse"), input_signature=signature, autograph=False, jit_compile=jit_compile
            )
        }
        self._predict = tf.function(
            lambda x: self.model.model(x, training=False),
            input_signature=[signature[0]],
            autograph=False,
            jit_compile=jit_compile,
        )

    def step(self, x, y, task, sample_weight):
        # XLA may elide tf.debugging assertions, so enforce these at the host boundary too.
        if (
            len(x) != len(y)
            or np.asarray(sample_weight).shape != (len(x),)
            or not np.isfinite(x).all()
            or not np.isfinite(y).all()
            or not np.isfinite(sample_weight).all()
            or np.any(sample_weight < 0)
            or np.sum(sample_weight) <= 0
        ):
            raise ValueError("Invalid/nonfinite recurrent batch or weights")
        result = super().step(x, y, task, sample_weight)
        if not np.isfinite(list(result.values())).all():
            raise ValueError("Nonfinite recurrent loss/gradient")
        return result


def predict_windows(trainer, data, ids, batch_size=32):
    if not ids or batch_size < 1:
        raise ValueError("Invalid prediction batch")
    result = np.concatenate(
        [trainer.predict(data.batch(ids[i : i + batch_size])[0]) for i in range(0, len(ids), batch_size)]
    )
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite RNN prediction")
    return result


def fit_windows(trainer, data, *, seed, budget, progress=None, resume=None):
    stop = EarlyStopping(budget["patience"], budget["min_delta"])
    history, best, elapsed = [], None, 0.0
    if resume is not None:
        trainer.restore_state(resume["trainer"])
        history, best, elapsed = resume["history"].copy(), resume["best_weights"], resume["elapsed_seconds"]
        for key, value in resume["early_stopping"].items():
            setattr(stop, key, value)
    started = time.perf_counter()
    val_y = np.concatenate(
        [
            data.batch(data.validation_ids[i : i + budget["batch_size"]])[1]
            for i in range(0, len(data.validation_ids), budget["batch_size"])
        ]
    )
    for epoch in range(len(history), budget["max_epochs"]):
        if stop.bad_epochs >= stop.patience:
            break
        order = batch_order(len(data.train_ids), budget["batch_size"], seed, epoch)
        loss_sum, count, norms = 0.0, 0, []
        for positions in order:
            if elapsed + time.perf_counter() - started >= budget["wall_time_limit_minutes"] * 60:
                raise TimeoutError("Locked recurrent wall-time budget exceeded")
            x, y = data.batch([data.train_ids[int(i)] for i in positions])
            output = trainer.step(x, y, "mse", np.ones(len(y), "float32"))
            loss_sum += output["loss"] * len(y)
            count += len(y)
            norms.append(output["gradient_global_norm_before_clip"])
        predicted = predict_windows(trainer, data, data.validation_ids, budget["batch_size"])
        loss = loss_and_gradient(predicted, val_y, "mse")[0]
        improved, terminate = stop.observe(loss, epoch)
        if improved:
            best = trainer.weights()
        history.append(
            {
                "epoch": epoch,
                "train_loss": loss_sum / count,
                "validation_loss": loss,
                "gradient_norm_mean": float(np.mean(norms)),
                "gradient_norm_max": float(np.max(norms)),
                "gradient_clip_fraction": float(np.mean(np.asarray(norms) > 1)),
                "batch_order_sha256": canonical_sha256(order),
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
            f"epoch={epoch + 1} train_loss={history[-1]['train_loss']:.6f} validation_loss={loss:.6f} best_epoch={stop.best_epoch + 1}",
            flush=True,
        )
        if terminate:
            break
    if best is None:
        raise ValueError("No finite validation-selected RNN weights")
    trainer.assign(best)
    return {
        "history": history,
        "best_epoch": stop.best_epoch,
        "best_validation_loss": stop.best,
        "weights": best,
        "train_seconds": elapsed + time.perf_counter() - started,
        "optimizer_steps": trainer.iterations,
    }
