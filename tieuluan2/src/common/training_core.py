"""Shared reproducibility and trainer hooks. No dataset training is started here."""

from __future__ import annotations

import random
import time

import numpy as np


def seed_everything(seed, backend="numpy"):
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("Invalid seed")
    random.seed(seed)
    np.random.seed(seed)
    if backend == "torch":
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.benchmark = False
        torch.use_deterministic_algorithms(True)
    elif backend == "tensorflow":
        import tensorflow as tf

        tf.keras.utils.set_random_seed(seed)
        tf.config.experimental.enable_op_determinism()
    elif backend != "numpy":
        raise ValueError("Unknown backend")


def batch_order(size, batch_size, seed, epoch):
    if size < 1 or batch_size < 1 or epoch < 0:
        raise ValueError("Invalid batch schedule")
    order = np.random.default_rng(np.random.SeedSequence([seed, epoch])).permutation(size).tolist()
    return [order[i : i + batch_size] for i in range(0, size, batch_size)]


def clip_gradients(gradients, max_norm=1):
    if max_norm <= 0 or not gradients or any(not np.isfinite(x).all() for x in gradients.values()):
        raise ValueError("Invalid/nonfinite gradients")
    norm = float(np.sqrt(sum(np.sum(np.square(v.astype(np.float64))) for v in gradients.values())))
    scale = min(1.0, max_norm / max(norm, np.finfo(float).tiny))
    return {key: value * scale for key, value in gradients.items()}, norm


class Adam:
    """Canonical Algorithm1: sqrt(v_hat)+eps, not Keras epsilon-hat."""

    def __init__(self, weights, learning_rate=0.001, beta1=0.9, beta2=0.999, epsilon=1e-7):
        if learning_rate <= 0 or epsilon <= 0 or not 0 <= beta1 < 1 or not 0 <= beta2 < 1:
            raise ValueError("Invalid Adam settings")
        self.lr, self.beta1, self.beta2, self.epsilon = learning_rate, beta1, beta2, epsilon
        self.m = {k: np.zeros_like(v) for k, v in weights.items()}
        self.v = {k: np.zeros_like(v) for k, v in weights.items()}
        self.t = 0

    def step(self, weights, gradients):
        if (
            set(weights) != set(self.m)
            or set(gradients) != set(weights)
            or any(
                gradients[k].shape != weights[k].shape or not np.isfinite(gradients[k]).all() for k in weights
            )
        ):
            raise ValueError("Adam gradient keys/shapes/values mismatch")
        self.t += 1
        for key in weights:
            self.m[key] = self.beta1 * self.m[key] + (1 - self.beta1) * gradients[key]
            self.v[key] = self.beta2 * self.v[key] + (1 - self.beta2) * gradients[key] ** 2
            mhat = self.m[key] / (1 - self.beta1**self.t)
            vhat = self.v[key] / (1 - self.beta2**self.t)
            weights[key] -= self.lr * mhat / (np.sqrt(vhat) + self.epsilon)


class EarlyStopping:
    def __init__(self, patience=6, min_delta=1e-5):
        if patience < 1 or min_delta < 0:
            raise ValueError("Invalid early stopping")
        self.patience, self.min_delta = patience, min_delta
        self.best = float("inf")
        self.patience_reference = float("inf")
        self.best_epoch = None
        self.bad_epochs = 0

    def observe(self, validation_loss, epoch):
        if not np.isfinite(validation_loss):
            raise ValueError("Nonfinite validation loss; record failed run")
        improved = validation_loss < self.best
        if improved:
            self.best = validation_loss
            self.best_epoch = epoch
        if validation_loss < self.patience_reference - self.min_delta:
            self.patience_reference = validation_loss
            self.bad_epochs = 0
        else:
            self.bad_epochs += 1
        return improved, self.bad_epochs >= self.patience


def inference_timing(function, synchronize=lambda: None, warmup=5, repeats=30):
    if warmup < 0 or repeats < 1:
        raise ValueError("Invalid timing repetitions")
    for _ in range(warmup):
        function()
        synchronize()
    values = []
    for _ in range(repeats):
        synchronize()
        start = time.perf_counter()
        function()
        synchronize()
        values.append((time.perf_counter() - start) * 1000)
    return {
        "inference_p50_ms": float(np.percentile(values, 50)),
        "inference_p95_ms": float(np.percentile(values, 95)),
        "warmup": warmup,
        "repeats": repeats,
    }
