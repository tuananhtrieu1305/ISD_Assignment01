"""Synthetic parity/update/shape and real-dimension memory probes, not training."""

from __future__ import annotations

import argparse
import gc
import json
import os
import platform

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np

from src.common.artifact_core import code_fingerprint, sha256_file, write_once
from src.common.backend_models import KerasBackend, TorchBackend
from src.common.contracts import PROTOCOL, ROOT, canonical_sha256, read_json
from src.common.data_access import DatasetView
from src.common.device_core import DeviceMonitor
from src.common.eda_artifacts import write_json
from src.common.model_core import build_plan, canonical_weights
from src.common.native_training import NativeAdam
from src.common.numpy_engine import NumpyNetwork
from src.common.parity import gradient_parity
from src.common.training_core import Adam, clip_gradients, inference_timing, seed_everything

BASE = ROOT / "artifacts/manifests/phase25"


def configure(implementation, device):
    if implementation == "pytorch":
        import torch

        torch.set_num_threads(2)
        seed_everything(42, "torch")
        return TorchBackend, "torch", torch.__version__
    if implementation == "keras":
        import keras
        import tensorflow as tf

        tf.config.threading.set_intra_op_parallelism_threads(2)
        tf.config.threading.set_inter_op_parallelism_threads(2)
        if device == "cpu":
            tf.config.set_visible_devices([], "GPU")
        else:
            for gpu in tf.config.list_physical_devices("GPU"):
                tf.config.experimental.set_memory_growth(gpu, True)
        tf.config.experimental.enable_tensor_float_32_execution(False)
        seed_everything(42, "tensorflow")
        return KerasBackend, "tensorflow", f"Keras {keras.__version__}/TensorFlow {tf.__version__}"
    raise ValueError("Unsupported implementation")


def parity_probe(constructor, implementation, device):
    results = []
    for family, shape, outputs in [
        ("mlp", [4], 2),
        ("cnn", [8, 8, 3], 3),
        ("rnn", [4, 2], 3),
        ("lstm", [4, 2], 3),
    ]:
        plan = build_plan(family, shape, outputs)
        weights = canonical_weights(plan, 42)
        # Bias perturbation only in the synthetic derivative fixture avoids ReLU kinks.
        for name, value in weights.items():
            if name.endswith("/b") and not name.startswith(("rnn_", "lstm_")):
                value += 0.1234
        rng = np.random.default_rng(73)
        x = rng.normal(size=(2, *shape)).astype("float32")
        y = rng.normal(size=(2, outputs)).astype("float32")
        reference = NumpyNetwork(plan, weights)
        model = constructor(plan, weights, device)
        expected = reference.forward(x)
        actual = model.predict(x)
        np.testing.assert_allclose(actual, expected, rtol=1e-4, atol=1e-5)
        loss, gradients, _ = reference.loss_gradients(x, y, "mse")
        native_loss, native_gradients = model.loss_gradients(x, y, "mse")
        if abs(loss - native_loss) > 1e-5:
            raise ValueError("Loss parity failure")
        gradient_check = gradient_parity(
            gradients,
            native_gradients,
            read_json(PROTOCOL)["comparison"]["numeric_parity"]["gradient_relative_error"],
        )
        if model.parameter_count != sum(v.size for v in weights.values()):
            raise ValueError("Trainable parameter parity failure")
        trace = model.trace(x)
        for row, step in zip(trace, plan["steps"], strict=True):
            if row["output_shape"] != [2, *step["output_shape"]]:
                raise ValueError("Runtime trace mismatch")
        optimizer = NativeAdam(model)
        numpy_optimizer = Adam(reference.weights)
        update_error = 0
        for _ in range(3):
            _, gradient, _ = reference.loss_gradients(x, y, "mse")
            gradient, _ = clip_gradients(gradient)
            numpy_optimizer.step(reference.weights, gradient)
            optimizer.step(x, y, "mse")
            for name, value in optimizer.weights().items():
                np.testing.assert_allclose(value, reference.weights[name], rtol=1e-3, atol=3e-6, err_msg=name)
                update_error = max(update_error, float(np.max(np.abs(value - reference.weights[name]))))
        results.append(
            {
                "family": family,
                "status": "PASS",
                "evidence_kind": "synthetic_fixture",
                "input_sha256": canonical_sha256(x.tolist()),
                "canonical_initial_weights_sha256": canonical_sha256(
                    {k: v.tolist() for k, v in weights.items()}
                ),
                "output_shape": list(actual.shape),
                "parameter_count": model.parameter_count,
                "trace": trace,
                "forward_max_abs_error": float(np.max(np.abs(actual - expected))),
                "gradient_parity": gradient_check,
                "three_updates_max_abs_error": update_error,
            }
        )
        print(
            json.dumps(
                {"parity": family, "implementation": implementation, "device": device, "status": "PASS"}
            ),
            flush=True,
        )
        del model, reference, optimizer
        gc.collect()
    return results


def memory_probes(constructor, implementation, backend, device):
    results = []
    protocol = read_json(PROTOCOL)
    for row in protocol["datasets"]:
        if row["chapter"] not in {2, 3, 4}:
            continue
        view = DatasetView(row["dataset_id"])
        shape = (
            view.preprocessing.get("input_shape_hwc")
            if row["chapter"] == 3
            else [view.preprocessing["lookback"], view.preprocessing["output_width"]]
            if row["chapter"] == 4
            else [view.preprocessing["output_width"]]
        )
        outputs = row.get("class_count", 3 if row["chapter"] == 4 else 1)
        for family in {2: ["mlp"], 3: ["cnn"], 4: ["rnn", "lstm"]}[row["chapter"]]:
            plan = build_plan(family, shape, outputs)
            batch_size = protocol["training"]["batch_size"][family]
            monitor = DeviceMonitor(backend, device)
            monitor.start()
            model = constructor(plan, canonical_weights(plan, 42), device)
            optimizer = NativeAdam(model)
            x = np.random.default_rng(17).normal(size=(batch_size, *shape)).astype("float32")
            y = np.zeros((batch_size, outputs), dtype="float32")
            step = optimizer.step(x, y, "mse")
            memory = monitor.finish()
            output = model.forward(x) if implementation == "pytorch" else model.model(x, training=False)
            actual_device = str(output.device)
            if device == "gpu" and not any(s in actual_device.lower() for s in ("gpu", "cuda")):
                raise ValueError("GPU silently placed on CPU")
            if device == "cpu" and any(s in actual_device.lower() for s in ("gpu", "cuda")):
                raise ValueError("CPU probe used GPU")
            if memory["peak_vram_bytes"] >= 8 * 1024**3 or device == "gpu" and memory["peak_vram_bytes"] == 0:
                raise ValueError("VRAM measurement/budget failed")
            timing = inference_timing(lambda model=model, x=x: model.predict(x[:1]), monitor.synchronize)
            results.append(
                {
                    "dataset_id": row["dataset_id"],
                    "family": family,
                    "status": "PASS",
                    "evidence_kind": "synthetic_fixture",
                    "shape_source": "locked Phase24 dimensions, synthetic values (not real samples)",
                    "input_shape": [batch_size, *shape],
                    "dtype": "float32",
                    "batch_size": batch_size,
                    "parameter_count": model.parameter_count,
                    "actual_device": actual_device,
                    "step": step,
                    **memory,
                    **timing,
                }
            )
            print(
                json.dumps(
                    {
                        "memory": row["dataset_id"],
                        "family": family,
                        "device": device,
                        "peak_vram_bytes": memory["peak_vram_bytes"],
                    }
                ),
                flush=True,
            )
            del model, optimizer, output
            gc.collect()
            if implementation == "keras":
                import keras

                keras.backend.clear_session()
    return results


def run(implementation, device, with_memory=True):
    from scripts.prepare_phase25 import CORE_FILES

    constructor, backend, version = configure(implementation, device)
    return {
        "phase": 25,
        "status": "PASS",
        "implementation": implementation,
        "backend": backend,
        "framework_version": version,
        "device": device,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "seed": 42,
        "dtype": "float32",
        "protocol_sha256": sha256_file(PROTOCOL),
        "code_sha256": code_fingerprint(ROOT, CORE_FILES),
        "probe_code_sha256": sha256_file(ROOT / "scripts/phase25_backend_probe.py"),
        "phase24_lock_sha256": sha256_file(ROOT / "artifacts/manifests/phase24/data_lock.json"),
        "parity": parity_probe(constructor, implementation, device),
        "memory_probes": memory_probes(constructor, implementation, backend, device) if with_memory else [],
        "real_dataset_training_executed": False,
        "test_evaluation_executed": False,
    }


def main():
    if (BASE / "core_lock.json").exists():
        from scripts.verify_phase25 import verify

        print(json.dumps(verify(), ensure_ascii=False, indent=2))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--implementation", choices=["keras", "pytorch"], required=True)
    parser.add_argument("--device", choices=["cpu", "gpu"], required=True)
    parser.add_argument("--parity-only", action="store_true")
    args = parser.parse_args()
    path = BASE / f"probe_{args.implementation}_{args.device}.json"
    if path.exists() and read_json(path)["status"] == "FAIL":
        previous = read_json(path)
        write_once(
            BASE / "attempts" / f"{args.implementation}_{args.device}_{canonical_sha256(previous)[:12]}.json",
            previous,
        )
    try:
        result = run(args.implementation, args.device, not args.parity_only)
    except Exception as error:
        write_json(
            path,
            {
                "phase": 25,
                "status": "FAIL",
                "error": f"{type(error).__name__}: {error}",
                "real_dataset_training_executed": False,
                "test_evaluation_executed": False,
            },
        )
        raise
    write_json(path, result)
    print(json.dumps({"status": "PASS", "artifact": str(path.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
