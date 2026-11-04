"""Educational NumPy forward/backward primitives, without autograd/frameworks.

This reference engine is first verified on synthetic data in Phase25. Real
dataset training/evaluation is implemented and accepted in Phases26–29.
"""

from __future__ import annotations

import numpy as np

from src.common.model_core import parameter_shapes


def sigmoid(value):
    # Equivalent stable expression, without clipping the mathematical derivative.
    return np.exp(-np.logaddexp(0, -value))


def loss_and_gradient(logits, target, task, sample_weight=None):
    logits = np.asarray(logits)
    target = np.asarray(target)
    if logits.ndim != 2 or len(logits) == 0 or not np.isfinite(logits).all() or not np.isfinite(target).all():
        raise ValueError("Loss requires finite, nonempty [batch, outputs] logits")
    if task == "multiclass":
        if (
            target.shape != (len(logits),)
            or not np.equal(target, np.floor(target)).all()
            or np.any(target < 0)
            or np.any(target >= logits.shape[1])
        ):
            raise ValueError("Invalid class IDs")
        labels = target.astype(int)
        shift = logits - logits.max(axis=1, keepdims=True)
        probs = np.exp(shift)
        probs /= probs.sum(axis=1, keepdims=True)
        rows = np.log(np.exp(shift).sum(axis=1)) - shift[np.arange(len(logits)), labels]
        gradient = probs.copy()
        gradient[np.arange(len(logits)), labels] -= 1
    elif task in {"mse", "binary"}:
        if target.shape != logits.shape:
            raise ValueError("Target shape mismatch")
        if task == "binary":
            if not np.isin(target, [0, 1]).all():
                raise ValueError("Binary labels must be zero or one")
            rows = (np.logaddexp(0, logits) - target * logits).mean(axis=1)
            gradient = (sigmoid(logits) - target) / logits.shape[1]
        else:
            rows = np.mean((logits - target) ** 2, axis=1)
            gradient = 2 * (logits - target) / logits.shape[1]
    else:
        raise ValueError("Unknown loss")
    weights = np.ones(len(logits)) if sample_weight is None else np.asarray(sample_weight, dtype=float)
    if (
        weights.shape != (len(logits),)
        or not np.isfinite(weights).all()
        or np.any(weights < 0)
        or weights.sum() <= 0
    ):
        raise ValueError("Invalid sample weights")
    normalized = weights / weights.sum()
    return float(rows @ normalized), (gradient * normalized[:, None]).astype(logits.dtype)


def numerical_gradient(function, value, epsilon=1e-5):
    if value.dtype != np.float64 or epsilon <= 0:
        raise ValueError("Numerical checks require float64 and positive epsilon")
    gradient = np.zeros_like(value)
    for index in np.ndindex(value.shape):
        previous = value[index]
        try:
            value[index] = previous + epsilon
            positive = function()
            value[index] = previous - epsilon
            negative = function()
        finally:
            value[index] = previous
        gradient[index] = (positive - negative) / (2 * epsilon)
    return gradient


class NumpyNetwork:
    def __init__(self, plan, weights):
        self.plan = plan
        expected = {
            f"{s['id']}/{k}": shape for s in plan["steps"] for k, shape in parameter_shapes(s).items()
        }
        if set(expected) != set(weights) or any(
            weights[k].shape != shape or not np.isfinite(weights[k]).all() for k, shape in expected.items()
        ):
            raise ValueError("Canonical weight names/shapes/values mismatch")
        self.weights = {key: value.copy() for key, value in weights.items()}
        self.cache = []

    def forward(self, x, *, trace=False):
        x = np.asarray(x, dtype=next(iter(self.weights.values())).dtype)
        if (
            x.ndim != len(self.plan["input_shape"]) + 1
            or list(x.shape[1:]) != self.plan["input_shape"]
            or len(x) == 0
            or not np.isfinite(x).all()
        ):
            raise ValueError("Input tensor shape/value mismatch")
        self.cache = []
        traces = []
        for step in self.plan["steps"]:
            before = x
            kind = step["kind"]
            prefix = step["id"]
            params = {key: self.weights[f"{prefix}/{key}"] for key in parameter_shapes(step)}
            extra = None
            if kind == "dense":
                x = before @ params["w"] + params["b"]
            elif kind == "activation":
                x = np.maximum(before, 0)
            elif kind == "conv2d":
                padded = np.pad(before, ((0, 0), (1, 1), (1, 1), (0, 0)))
                x = np.zeros((len(before), *step["output_shape"]), dtype=before.dtype)
                for i in range(3):
                    for j in range(3):
                        x += np.einsum(
                            "nhwc,co->nhwo",
                            padded[:, i : i + before.shape[1], j : j + before.shape[2]],
                            params["w"][i, j],
                        )
                x += params["b"]
                extra = padded
            elif kind == "pooling":
                if step["pool"] == "global_average":
                    x = before.mean(axis=(1, 2))
                else:
                    n, h, w, c = before.shape
                    hh, ww = h // 2, w // 2
                    patches = (
                        before[:, : hh * 2, : ww * 2]
                        .reshape(n, hh, 2, ww, 2, c)
                        .transpose(0, 1, 3, 5, 2, 4)
                        .reshape(n, hh, ww, c, 4)
                    )
                    extra = patches.argmax(axis=-1)
                    x = patches.max(axis=-1)
            else:
                units = step["output_shape"][-1]
                h = np.zeros((len(before), units), dtype=before.dtype)
                c = np.zeros_like(h)
                states = []
                outputs = []
                for t in range(before.shape[1]):
                    z = before[:, t] @ params["w"] + h @ params["u"] + params["b"]
                    if kind == "rnn":
                        next_h = np.tanh(z)
                        states.append((before[:, t], h, next_h))
                        h = next_h
                    else:
                        zi, zf, zg, zo = np.split(z, 4, axis=1)
                        i, f, g, o = sigmoid(zi), sigmoid(zf), np.tanh(zg), sigmoid(zo)
                        next_c = f * c + i * g
                        next_h = o * np.tanh(next_c)
                        states.append((before[:, t], h, c, i, f, g, o, next_c))
                        h, c = next_h, next_c
                    outputs.append(h)
                full = np.stack(outputs, axis=1)
                x = full if step["return_sequences"] else full[:, -1]
                extra = states
            self.cache.append((step, before, params, extra))
            traces.append({"id": prefix, "input_shape": list(before.shape), "output_shape": list(x.shape)})
        return (x, traces) if trace else x

    def backward(self, gradient):
        gradients = {}
        for step, before, params, extra in reversed(self.cache):
            kind = step["kind"]
            prefix = step["id"]
            grads = {key: np.zeros_like(value) for key, value in params.items()}
            if kind == "dense":
                grads["w"] = before.T @ gradient
                grads["b"] = gradient.sum(axis=0)
                gradient = gradient @ params["w"].T
            elif kind == "activation":
                gradient = gradient * (before > 0)
            elif kind == "conv2d":
                grads["b"] = gradient.sum(axis=(0, 1, 2))
                padded = extra
                dx = np.zeros_like(padded)
                for i in range(3):
                    for j in range(3):
                        patch = padded[:, i : i + before.shape[1], j : j + before.shape[2]]
                        grads["w"][i, j] = np.einsum("nhwc,nhwo->co", patch, gradient)
                        dx[:, i : i + before.shape[1], j : j + before.shape[2]] += np.einsum(
                            "nhwo,co->nhwc", gradient, params["w"][i, j]
                        )
                gradient = dx[:, 1:-1, 1:-1]
            elif kind == "pooling":
                if step["pool"] == "global_average":
                    gradient = np.broadcast_to(
                        gradient[:, None, None, :] / (before.shape[1] * before.shape[2]), before.shape
                    ).copy()
                else:
                    n, h, w, c = before.shape
                    hh, ww = h // 2, w // 2
                    patches = np.zeros((n, hh, ww, c, 4), dtype=before.dtype)
                    np.put_along_axis(patches, extra[..., None], gradient[..., None], axis=-1)
                    dx = np.zeros_like(before)
                    dx[:, : hh * 2, : ww * 2] = (
                        patches.reshape(n, hh, ww, c, 2, 2)
                        .transpose(0, 1, 4, 2, 5, 3)
                        .reshape(n, hh * 2, ww * 2, c)
                    )
                    gradient = dx
            else:
                full_gradient = np.zeros(
                    (len(before), before.shape[1], step["output_shape"][-1]), dtype=before.dtype
                )
                if step["return_sequences"]:
                    full_gradient += gradient
                else:
                    full_gradient[:, -1] = gradient
                dh = np.zeros_like(full_gradient[:, 0])
                dc = np.zeros_like(dh)
                dx = np.zeros_like(before)
                for t in reversed(range(before.shape[1])):
                    dh = dh + full_gradient[:, t]
                    if kind == "rnn":
                        xt, previous_h, h = extra[t]
                        dz = dh * (1 - h * h)
                    else:
                        xt, previous_h, previous_c, i, f, g, o, c = extra[t]
                        tanhc = np.tanh(c)
                        dc = dc + dh * o * (1 - tanhc * tanhc)
                        dz = np.concatenate(
                            (
                                dc * g * i * (1 - i),
                                dc * previous_c * f * (1 - f),
                                dc * i * (1 - g * g),
                                dh * tanhc * o * (1 - o),
                            ),
                            axis=1,
                        )
                        dc = dc * f
                    grads["w"] += xt.T @ dz
                    grads["u"] += previous_h.T @ dz
                    grads["b"] += dz.sum(axis=0)
                    dx[:, t] = dz @ params["w"].T
                    dh = dz @ params["u"].T
                gradient = dx
            gradients.update({f"{prefix}/{name}": value for name, value in grads.items()})
        return gradients, gradient

    def loss_gradients(self, x, y, task, sample_weight=None):
        logits = self.forward(x)
        loss, gradient = loss_and_gradient(logits, y, task, sample_weight)
        gradients, dx = self.backward(gradient)
        return loss, gradients, dx
