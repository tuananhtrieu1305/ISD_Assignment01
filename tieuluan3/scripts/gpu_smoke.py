"""Small synthetic workloads: no dataset download, tuning, or sealed TEST access."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import resource
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.common.environment import SHARED_PACKAGES, validate_smoke


def torch_workloads(report):
    import torch
    from torch import nn

    torch.set_num_threads(2)
    torch.manual_seed(42)
    device = torch.device("cuda:0" if report["device"] == "gpu" else "cpu")
    report["framework_versions"] = {
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(),
    }
    if device.type == "cuda":
        assert torch.cuda.is_available(), "CUDA unavailable"
        torch.cuda.reset_peak_memory_stats()
        report["gpu"] = torch.cuda.get_device_name(0)
        report["capability"] = list(torch.cuda.get_device_capability(0))
        report["compiled_architectures"] = torch.cuda.get_arch_list()
    a = torch.ones((128, 128), device=device)
    value = a @ a
    report["checks"].append(
        {"name": "matmul", "passed": bool((value == 128).all()), "actual_device": str(value.device)}
    )

    class SequenceModel(nn.Module):
        def __init__(self, kind):
            super().__init__()
            self.recurrent = (nn.RNN if kind == "rnn" else nn.LSTM)(4, 8, 3, batch_first=True)
            self.head = nn.Sequential(nn.Linear(8, 8), nn.ReLU(), nn.Linear(8, 8), nn.ReLU(), nn.Linear(8, 3))

        def forward(self, x):
            return self.head(self.recurrent(x)[0][:, -1])

    conv = []
    for index in range(5):
        conv.extend([nn.Conv2d(3 if index == 0 else 4, 4, 3, padding=1), nn.ReLU()])
    cnn = nn.Sequential(
        *conv, nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, 3)
    )
    for name in ("cnn", "rnn", "lstm"):
        model = (cnn if name == "cnn" else SequenceModel(name)).to(device)
        x = torch.randn((8, 3, 16, 16) if name == "cnn" else (8, 10, 4), device=device)
        y = torch.randint(0, 3, (8,), device=device)
        optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
        before = [p.detach().clone() for p in model.parameters()]
        output = model(x)
        loss = nn.functional.cross_entropy(output, y)
        loss.backward()
        finite = all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters())
        optimizer.step()
        changed = any(not torch.equal(old, new) for old, new in zip(before, model.parameters()))
        report["checks"].append(
            {
                "name": name,
                "passed": bool(torch.isfinite(loss)) and changed and finite,
                "actual_device": str(output.device),
                "gradients_finite": finite,
                "weight_updated": changed,
                "loss": loss.item(),
                "learnable_layers": 7 if name == "cnn" else 6,
                "parameters": sum(p.numel() for p in model.parameters()),
            }
        )
    if device.type == "cuda":
        torch.cuda.synchronize()
        report["peak_vram_bytes"] = torch.cuda.max_memory_allocated()


def keras_workloads(report, backend):
    os.environ["KERAS_BACKEND"] = backend
    import keras
    import numpy as np

    keras.utils.set_random_seed(42)
    report["framework_versions"] = {"keras": keras.__version__, "backend": backend}
    if backend == "tensorflow":
        import tensorflow as tf

        report["framework_versions"]["tensorflow"] = tf.__version__
        report["tensorflow_build"] = tf.sysconfig.get_build_info()
        tf.config.threading.set_intra_op_parallelism_threads(2)
        tf.config.threading.set_inter_op_parallelism_threads(2)
        gpus = tf.config.list_physical_devices("GPU")
        if report["device"] == "gpu":
            assert gpus, "TensorFlow GPU unavailable"
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            report["gpu"] = str(gpus)
        a = tf.ones((128, 128))
        value = tf.matmul(a, a)
        actual = value.device
        passed = bool(tf.reduce_all(value == 128).numpy())
    else:
        import torch

        report["framework_versions"].update(
            torch=torch.__version__, cuda=torch.version.cuda, cudnn=torch.backends.cudnn.version()
        )
        torch.set_num_threads(2)
        if report["device"] == "gpu":
            assert torch.cuda.is_available(), "Keras/PyTorch CUDA unavailable"
            torch.cuda.reset_peak_memory_stats()
            report["gpu"] = torch.cuda.get_device_name(0)
        a = torch.ones((128, 128), device="cuda:0" if report["device"] == "gpu" else "cpu")
        value = a @ a
        actual, passed = str(value.device), bool((value == 128).all())
    report["checks"].append({"name": "matmul", "passed": passed, "actual_device": actual})
    rng = np.random.default_rng(42)
    for name in ("cnn", "rnn", "lstm"):
        layers = [keras.layers.Input((16, 16, 3) if name == "cnn" else (10, 4))]
        if name == "cnn":
            layers += [keras.layers.Conv2D(4, 3, padding="same", activation="relu") for _ in range(5)]
            layers += [keras.layers.GlobalAveragePooling2D(), keras.layers.Dense(8, activation="relu")]
        else:
            recurrent = keras.layers.SimpleRNN if name == "rnn" else keras.layers.LSTM
            layers += [recurrent(8, return_sequences=index < 2) for index in range(3)]
            layers += [keras.layers.Dense(8, activation="relu"), keras.layers.Dense(8, activation="relu")]
        model = keras.Sequential([*layers, keras.layers.Dense(3)])
        model.compile(
            optimizer=keras.optimizers.SGD(0.01),
            loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            jit_compile=False,
        )
        x = rng.normal(size=(8, 16, 16, 3) if name == "cnn" else (8, 10, 4)).astype("float32")
        y = rng.integers(0, 3, 8).astype("int32")
        before = model.get_weights()
        if backend == "tensorflow":
            with tf.GradientTape() as tape:
                output = model(x, training=True)
                loss = model.loss(y, output)
            gradients = tape.gradient(loss, model.trainable_weights)
            finite = all(g is not None and bool(tf.reduce_all(tf.math.is_finite(g))) for g in gradients)
            actual = output.device
        else:
            model.zero_grad()
            output = model(x, training=True)
            labels = torch.as_tensor(y, dtype=torch.long, device=output.device)
            loss = torch.nn.functional.cross_entropy(output, labels)
            loss.backward()
            # Keras registers integer RNG-state buffers as non-trainable Parameters.
            # They intentionally have no gradient; inspect only trainable weights.
            finite = all(
                p.grad is not None and bool(torch.isfinite(p.grad).all())
                for p in model.parameters()
                if p.requires_grad
            )
            actual = str(output.device)
        batch_loss = float(np.asarray(model.train_on_batch(x, y)))
        after = model.get_weights()
        changed = any(not np.array_equal(a, b) for a, b in zip(before, after))
        report["checks"].append(
            {
                "name": name,
                "passed": bool(np.isfinite(batch_loss)) and finite and changed,
                "actual_device": actual,
                "gradients_finite": finite,
                "weight_updated": changed,
                "loss": batch_loss,
                "learnable_layers": len([layer for layer in model.layers if layer.trainable_weights]),
                "parameters": model.count_params(),
            }
        )
    if report["device"] == "gpu":
        if backend == "tensorflow":
            report["peak_vram_bytes"] = int(tf.config.experimental.get_memory_info("GPU:0")["peak"])
        else:
            torch.cuda.synchronize()
            report["peak_vram_bytes"] = torch.cuda.max_memory_allocated()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", choices=["torch", "tensorflow", "keras-torch"], required=True)
    parser.add_argument("--device", choices=["gpu", "cpu"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    report = {
        "status": "FAIL",
        "framework": args.framework,
        "device": args.device,
        "python": sys.version,
        "python_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
        "checks": [],
        "peak_vram_bytes": 0,
    }
    started = time.monotonic()
    try:
        if args.framework == "torch":
            torch_workloads(report)
        else:
            keras_workloads(report, "tensorflow" if args.framework == "tensorflow" else "torch")
        report["shared_packages"] = {name: importlib.metadata.version(name) for name in SHARED_PACKAGES}
        report["status"] = "PASS"
        report["validation_errors"] = validate_smoke(report)
        if report["validation_errors"]:
            report["status"] = "FAIL"
    except Exception:  # noqa: BLE001 -- process boundary must preserve any framework failure as evidence
        report["error"] = traceback.format_exc()
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["peak_process_ram_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
