"""Lazy independent PyTorch and Keras/TensorFlow adapters for canonical plans.

No torch import is needed in the Keras environment (or vice versa). The public
probe methods accept canonical NHWC/NTF NumPy arrays. DatasetView separately
provides native NCHW batches for future PyTorch training runners.
"""

from __future__ import annotations

import numpy as np

from src.common.model_core import parameter_shapes


class TorchBackend:
    def __init__(self, plan, weights, device="cpu"):
        import torch
        from torch import nn

        torch.backends.fp32_precision = "ieee"
        torch.backends.cuda.matmul.fp32_precision = "ieee"
        torch.backends.cudnn.fp32_precision = "ieee"
        torch.backends.cudnn.conv.fp32_precision = "ieee"
        torch.backends.cudnn.rnn.fp32_precision = "ieee"
        if device not in {"cpu", "gpu"}:
            raise ValueError("Unknown device")
        if device == "gpu" and not torch.cuda.is_available():
            raise RuntimeError("Requested GPU is unavailable; no silent fallback")
        self.torch = torch
        self.plan = plan
        self.device = "cuda:0" if device == "gpu" else "cpu"
        self.ops = nn.ModuleDict()
        for step in plan["steps"]:
            kind = step["kind"]
            width = step["input_shape"][-1]
            units = step["output_shape"][-1]
            if kind == "dense":
                layer = nn.Linear(width, units)
            elif kind == "conv2d":
                layer = nn.Conv2d(width, units, 3, padding=1)
            elif kind == "activation":
                layer = nn.ReLU()
            elif kind == "pooling":
                layer = nn.MaxPool2d(2) if step["pool"] == "max2" else nn.AdaptiveAvgPool2d(1)
            else:
                layer = (nn.LSTM if kind == "lstm" else nn.RNN)(width, units, batch_first=True)
                layer.bias_hh_l0.requires_grad_(False)
            self.ops[step["id"]] = layer
        self.ops.to(self.device)
        self.assign(weights)

    @property
    def parameter_count(self):
        return sum(v.numel() for v in self.ops.parameters() if v.requires_grad)

    def parameter_pairs(self):
        pairs = []
        for step in self.plan["steps"]:
            layer = self.ops[step["id"]]
            kind = step["kind"]
            for key in parameter_shapes(step):
                name = (
                    {"w": "weight_ih_l0", "u": "weight_hh_l0", "b": "bias_ih_l0"}[key]
                    if kind in {"rnn", "lstm"}
                    else "weight"
                    if key == "w"
                    else "bias"
                )
                pairs.append((f"{step['id']}/{key}", getattr(layer, name), kind, key))
        return pairs

    def assign(self, weights):
        with self.torch.no_grad():
            for name, param, kind, key in self.parameter_pairs():
                value = weights[name]
                if key in {"w", "u"}:
                    value = value.transpose(3, 2, 0, 1) if kind == "conv2d" else value.T
                param.copy_(self.torch.as_tensor(np.ascontiguousarray(value), device=self.device))
            for step in self.plan["steps"]:
                if step["kind"] in {"rnn", "lstm"}:
                    self.ops[step["id"]].bias_hh_l0.zero_()

    def forward(self, x, trace=False):
        torch = self.torch
        value = (
            torch.as_tensor(np.ascontiguousarray(x), dtype=torch.float32, device=self.device)
            if isinstance(x, np.ndarray)
            else x
        )
        is_image = self.plan["family"] == "cnn"
        if is_image:
            value = value.permute(0, 3, 1, 2).contiguous()
        traces = []
        for step in self.plan["steps"]:
            before = list(value.shape)
            kind = step["kind"]
            value = self.ops[step["id"]](value)
            if kind in {"rnn", "lstm"}:
                value = value[0]
                if not step["return_sequences"]:
                    value = value[:, -1]
            if kind == "pooling" and step["pool"] == "global_average":
                value = value.flatten(1)
            after = list(value.shape)
            if is_image and len(before) == 4:
                before = [before[0], before[2], before[3], before[1]]
            if is_image and len(after) == 4:
                after = [after[0], after[2], after[3], after[1]]
            traces.append({"id": step["id"], "input_shape": before, "output_shape": after})
        return (value, traces) if trace else value

    def predict(self, x):
        with self.torch.no_grad():
            return self.forward(x).cpu().numpy()

    def trace(self, x):
        with self.torch.no_grad():
            return self.forward(x, True)[1]

    def loss_gradients(self, x, y, task):
        self.ops.zero_grad(set_to_none=True)
        logits = self.forward(x)
        target = self.torch.as_tensor(y, device=self.device)
        if task == "mse":
            loss = self.torch.mean((logits - target) ** 2)
        elif task == "binary":
            loss = self.torch.nn.functional.binary_cross_entropy_with_logits(logits, target)
        elif task == "multiclass":
            loss = self.torch.nn.functional.cross_entropy(logits, target.long())
        else:
            raise ValueError("Unknown loss")
        loss.backward()
        gradients = {}
        for name, param, kind, key in self.parameter_pairs():
            value = param.grad.detach().cpu().numpy()
            if key in {"w", "u"}:
                value = value.transpose(2, 3, 1, 0) if kind == "conv2d" else value.T
            gradients[name] = np.ascontiguousarray(value)
        return float(loss.detach().cpu()), gradients


class KerasBackend:
    def __init__(self, plan, weights, device="cpu"):
        import keras
        import tensorflow as tf

        if keras.backend.backend() != "tensorflow":
            raise RuntimeError("Keras must use the independently locked TensorFlow backend")
        if device not in {"cpu", "gpu"}:
            raise ValueError("Unknown device")
        if device == "gpu" and not tf.config.list_physical_devices("GPU"):
            raise RuntimeError("Requested GPU unavailable; no silent fallback")
        self.tf = tf
        tf.config.experimental.enable_tensor_float_32_execution(False)
        self.keras = keras
        self.plan = plan
        self.device = "/GPU:0" if device == "gpu" else "/CPU:0"
        self.layers = {}
        with tf.device(self.device):
            inputs = keras.Input(shape=plan["input_shape"], dtype="float32")
            value = inputs
            for step in plan["steps"]:
                kind = step["kind"]
                units = step["output_shape"][-1]
                name = step["id"]
                if kind == "dense":
                    layer = keras.layers.Dense(units, name=name)
                elif kind == "conv2d":
                    layer = keras.layers.Conv2D(units, 3, padding="same", name=name)
                elif kind == "activation":
                    layer = keras.layers.ReLU(name=name)
                elif kind == "pooling":
                    layer = (
                        keras.layers.MaxPooling2D(2, name=name)
                        if step["pool"] == "max2"
                        else keras.layers.GlobalAveragePooling2D(name=name)
                    )
                elif kind == "rnn":
                    layer = keras.layers.SimpleRNN(
                        units, return_sequences=step["return_sequences"], name=name
                    )
                else:
                    layer = keras.layers.LSTM(
                        units, return_sequences=step["return_sequences"], unit_forget_bias=False, name=name
                    )
                value = layer(value)
                self.layers[name] = layer
            self.model = keras.Model(inputs, value)
            self.trace_model = keras.Model(inputs, [layer.output for layer in self.layers.values()])
            self.assign(weights)

    @property
    def parameter_count(self):
        return sum(int(np.prod(v.shape)) for v in self.model.trainable_weights)

    def parameter_pairs(self):
        return [
            (f"{step['id']}/{key}", variable)
            for step in self.plan["steps"]
            for key, variable in zip(
                parameter_shapes(step), self.layers[step["id"]].trainable_weights, strict=True
            )
        ]

    def assign(self, weights):
        with self.tf.device(self.device):
            for name, variable in self.parameter_pairs():
                variable.assign(weights[name])

    def predict(self, x):
        with self.tf.device(self.device):
            return self.model(x, training=False).numpy()

    def trace(self, x):
        with self.tf.device(self.device):
            values = self.trace_model(x, training=False)
        before = list(x.shape)
        rows = []
        for step, value in zip(self.plan["steps"], values, strict=True):
            rows.append({"id": step["id"], "input_shape": before, "output_shape": list(value.shape)})
            before = list(value.shape)
        return rows

    def loss_gradients(self, x, y, task):
        tf = self.tf
        with tf.device(self.device), tf.GradientTape() as tape:
            logits = self.model(x, training=True)
            target = tf.convert_to_tensor(y)
            if task == "mse":
                loss = tf.reduce_mean(tf.square(logits - tf.cast(target, logits.dtype)))
            elif task == "binary":
                loss = tf.reduce_mean(
                    tf.nn.sigmoid_cross_entropy_with_logits(
                        labels=tf.cast(target, logits.dtype), logits=logits
                    )
                )
            elif task == "multiclass":
                loss = tf.reduce_mean(
                    tf.nn.sparse_softmax_cross_entropy_with_logits(
                        labels=tf.cast(target, tf.int64), logits=logits
                    )
                )
            else:
                raise ValueError("Unknown loss")
        with tf.device(self.device):
            gradients = tape.gradient(loss, self.model.trainable_weights)
        return float(loss.numpy()), {
            name: gradient.numpy()
            for (name, _), gradient in zip(self.parameter_pairs(), gradients, strict=True)
        }
