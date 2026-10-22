"""Native GPU updates with one canonical Adam denominator and clipping policy.

TensorFlow uses explicit slots so epsilon is applied to sqrt(v_hat), unlike
stock Keras Adam's epsilon-hat. No weights/gradients move to NumPy during update.
"""

from __future__ import annotations

import numpy as np


class NativeAdam:
    def __init__(self, backend, learning_rate=0.001, beta1=0.9, beta2=0.999, epsilon=1e-7, max_norm=1):
        if learning_rate <= 0 or epsilon <= 0 or max_norm <= 0 or not 0 <= beta1 < 1 or not 0 <= beta2 < 1:
            raise ValueError("Invalid optimizer settings")
        self.backend = backend
        self.lr = learning_rate
        self.b1 = beta1
        self.b2 = beta2
        self.eps = epsilon
        self.max_norm = max_norm
        self.t = 0
        self.is_torch = hasattr(backend, "torch")
        if self.is_torch:
            self.variables = [p for p in backend.ops.parameters() if p.requires_grad]
            self.optimizer = backend.torch.optim.Adam(
                self.variables, lr=learning_rate, betas=(beta1, beta2), eps=epsilon, foreach=False
            )
        else:
            tf = backend.tf
            self.variables = backend.model.trainable_weights
            with tf.device(backend.device):
                self.m = [tf.Variable(tf.zeros_like(p), trainable=False) for p in self.variables]
                self.v = [tf.Variable(tf.zeros_like(p), trainable=False) for p in self.variables]

    def step(self, x, y, task, sample_weight=None):
        if task not in {"mse", "binary", "multiclass"}:
            raise ValueError("Unknown loss")
        if self.is_torch:
            torch = self.backend.torch
            self.optimizer.zero_grad(set_to_none=True)
            logits = self.backend.forward(x)
            target = torch.as_tensor(y, device=self.backend.device)
            if task == "mse":
                rows = ((logits - target) ** 2).mean(dim=1)
            elif task == "binary":
                rows = torch.nn.functional.binary_cross_entropy_with_logits(
                    logits, target, reduction="none"
                ).mean(dim=1)
            else:
                rows = torch.nn.functional.cross_entropy(logits, target.long(), reduction="none")
            weights = (
                torch.ones_like(rows)
                if sample_weight is None
                else torch.as_tensor(sample_weight, device=self.backend.device, dtype=rows.dtype)
            )
            if (
                weights.shape != rows.shape
                or not bool(torch.isfinite(weights).all())
                or bool((weights < 0).any())
                or float(weights.sum()) <= 0
            ):
                raise ValueError("Invalid sample weights")
            loss = (rows * weights).sum() / weights.sum()
            if not bool(torch.isfinite(loss)):
                raise ValueError("Nonfinite loss")
            loss.backward()
            norm = torch.nn.utils.clip_grad_norm_(self.variables, self.max_norm, error_if_nonfinite=True)
            self.optimizer.step()
            value = float(loss.detach().cpu())
            norm = float(norm.detach().cpu())
        else:
            tf = self.backend.tf
            with tf.device(self.backend.device), tf.GradientTape() as tape:
                logits = self.backend.model(x, training=True)
                target = tf.convert_to_tensor(y)
                if task == "mse":
                    rows = tf.reduce_mean(tf.square(logits - tf.cast(target, logits.dtype)), axis=1)
                elif task == "binary":
                    rows = tf.reduce_mean(
                        tf.nn.sigmoid_cross_entropy_with_logits(
                            labels=tf.cast(target, logits.dtype), logits=logits
                        ),
                        axis=1,
                    )
                else:
                    rows = tf.nn.sparse_softmax_cross_entropy_with_logits(
                        labels=tf.cast(target, tf.int64), logits=logits
                    )
                weights = (
                    tf.ones_like(rows)
                    if sample_weight is None
                    else tf.convert_to_tensor(sample_weight, dtype=rows.dtype)
                )
                if (
                    weights.shape != rows.shape
                    or not bool(tf.reduce_all(tf.math.is_finite(weights)))
                    or bool(tf.reduce_any(weights < 0))
                    or float(tf.reduce_sum(weights)) <= 0
                ):
                    raise ValueError("Invalid sample weights")
                loss = tf.reduce_sum(rows * weights) / tf.reduce_sum(weights)
            with tf.device(self.backend.device):
                tf.debugging.assert_all_finite(loss, "Nonfinite loss")
                gradients = tape.gradient(loss, self.variables)
                for gradient in gradients:
                    tf.debugging.assert_all_finite(gradient, "Nonfinite gradients")
                gradients, norm = tf.clip_by_global_norm(gradients, self.max_norm)
            self.t += 1
            with tf.device(self.backend.device):
                for p, g, m, v in zip(self.variables, gradients, self.m, self.v, strict=True):
                    m.assign(self.b1 * m + (1 - self.b1) * g)
                    v.assign(self.b2 * v + (1 - self.b2) * tf.square(g))
                    mhat = m / (1 - self.b1**self.t)
                    vhat = v / (1 - self.b2**self.t)
                    p.assign_sub(self.lr * mhat / (tf.sqrt(vhat) + self.eps))
            value = float(loss.numpy())
            norm = float(norm.numpy())
        return {"loss": value, "gradient_global_norm_before_clip": norm}

    def weights(self):
        backend = self.backend
        if self.is_torch:
            result = {}
            for name, param, kind, key in backend.parameter_pairs():
                value = param.detach().cpu().numpy()
                if key in {"w", "u"}:
                    value = value.transpose(2, 3, 1, 0) if kind == "conv2d" else value.T
                result[name] = np.ascontiguousarray(value)
            return result
        return {name: variable.numpy().copy() for name, variable in backend.parameter_pairs()}
