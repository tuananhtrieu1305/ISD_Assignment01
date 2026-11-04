# PHỤ LỤC D. TRÍCH MÃ NGUỒN ĐÃ THỰC THI

Các đoạn dưới trích nguyên method từ source đã khóa, không viết một mô hình minh họa khác rồi gán metric cũ cho nó. Method nằm trong class, dùng import/state của module gốc; không phải script độc lập để copy chạy. Computational plan và canonical weights quyết định đủ6 hoặc7 lớp như các bảng Chương2–4. RNN/LSTM còn có các đoạn kiến trúc ba cách viết trực tiếp ở Chương4.

## D.1. Scratch: forward cho MLP/CNN/RNN/LSTM

Nguồn: `src/common/numpy_engine.py`, `NumpyNetwork.forward`, dòng94–166.

```python
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
```

## D.2. Scratch: nối loss, backward và gradient

Nguồn: `src/common/numpy_engine.py`, `NumpyNetwork.loss_gradients`, dòng248–252.

```python
    def loss_gradients(self, x, y, task, sample_weight=None):
        logits = self.forward(x)
        loss, gradient = loss_and_gradient(logits, y, task, sample_weight)
        gradients, dx = self.backward(gradient)
        return loss, gradients, dx
```

## D.3. Scratch: clipping và optimizer update

Nguồn: `src/ch02_ml/training.py`, `ScratchTrainer.step`, dòng56–60.

```python
    def step(self, x, y, task, sample_weight):
        loss, grad, _ = self.model.loss_gradients(x, y, task, sample_weight)
        grad, norm = clip_gradients(grad)
        self.optimizer.step(self.model.weights, grad)
        return {"loss": loss, "gradient_global_norm_before_clip": norm}
```

## D.4. Keras/TensorFlow: tạo các lớp từ cùng plan

Nguồn: `src/common/backend_models.py`, `KerasBackend.__init__`, dòng143–190.

```python
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
```

## D.5. PyTorch: tạo các lớp từ cùng plan

Nguồn: `src/common/backend_models.py`, `TorchBackend.__init__`, dòng16–50.

```python
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
```

Backward/BPTT đầy đủ ở NumpyNetwork.backward; optimizer moment/update ở src/common/training_core.py và native_training.py; vòng train/checkpoint riêng từng chương ở các module training. Không dùng loss_gradients parity không trọng số thay cho weighted training step. Kiểm numerical gradient, native parity và update/resume đã có bằng chứng trước TEST; đoạn trích này không chạy lại chúng để tạo metric mới.
