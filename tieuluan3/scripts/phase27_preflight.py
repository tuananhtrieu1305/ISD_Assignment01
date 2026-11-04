"""Read-only dependency audit, development cache and CNN feasibility probe."""

import os

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import argparse
import json
import time
from datetime import UTC, datetime

import numpy as np

from src.ch02_ml.experiment import configure
from src.ch02_ml.test_gate import atomic_json
from src.ch03_cnn.image_cache import development_cache
from src.ch03_cnn.training import CnnKerasTrainer, CnnScratchTrainer, CnnTorchTrainer
from src.common.artifact_core import sha256_file
from src.common.contracts import ROOT, read_json
from src.common.device_core import DeviceMonitor
from src.common.model_core import build_plan, canonical_weights
from src.common.numpy_engine import NumpyNetwork
from src.common.parity import gradient_parity

BASE = ROOT / "artifacts/manifests/phase27"
DATASETS = ("ch3_idrid", "ch3_eurosat", "ch3_cifar10")


def dependencies():
    result = {}
    for name, path in {
        "spec22": "artifacts/manifests/phase22/spec_lock.json",
        "data24": "artifacts/manifests/phase24/data_lock.json",
        "core25": "artifacts/manifests/phase25/core_lock.json",
        "experiment26": "artifacts/manifests/phase26/revisions/r2/experiment_lock.json",
    }.items():
        lock = read_json(ROOT / path)
        files = lock["files"]
        for row in files:
            if sha256_file(ROOT / row["path"]) != row["sha256"]:
                raise ValueError(f"Protected artifact changed: {row['path']}")
        result[name] = {"path": path, "sha256": sha256_file(ROOT / path), "verified_files": len(files)}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation", choices=("scratch", "pytorch", "keras"), default="scratch")
    args = parser.parse_args()
    method = args.implementation
    configure(method, 17)
    backend = {"scratch": "numpy", "pytorch": "torch", "keras": "tensorflow"}[method]
    audit = dependencies()
    evidence = []
    for dataset in DATASETS:
        started = time.perf_counter()
        cache, view = development_cache(dataset)
        cache_seconds = time.perf_counter() - started
        ids = view.ids("train")[:16]
        x, y = cache.batch(ids)
        plan = build_plan("cnn", view.preprocessing["input_shape_hwc"], view.spec["class_count"])
        weights = canonical_weights(plan, 17)
        trainer = {"scratch": CnnScratchTrainer, "pytorch": CnnTorchTrainer, "keras": CnnKerasTrainer}[
            method
        ](plan, weights, **({"device": "gpu"} if method != "scratch" else {}))
        monitor = DeviceMonitor(backend, "cpu" if method == "scratch" else "gpu")
        monitor.start()
        expected = NumpyNetwork(plan, weights)
        np.testing.assert_allclose(trainer.predict(x[:2]), expected.forward(x[:2]), rtol=1e-4, atol=1e-5)
        cw = view.adapter_contract["class_weights_by_id"] if dataset == "ch3_idrid" else None
        sw = np.asarray([cw[str(v)] for v in y], dtype="float32") if cw else np.ones(len(y), dtype="float32")
        parity = None
        if method != "scratch":
            _, ref_grads, _ = expected.loss_gradients(x[:2], y[:2], "multiclass")
            _, native_grads = trainer.model.loss_gradients(x[:2], y[:2], "multiclass")
            parity = gradient_parity(ref_grads, native_grads)
        steps = []
        for _ in range(2):
            tick = time.perf_counter()
            output = trainer.step(x, y, "multiclass", sw)
            monitor.synchronize()
            steps.append(time.perf_counter() - tick)
        tick = time.perf_counter()
        trainer.predict(x)
        monitor.synchronize()
        predict_seconds = time.perf_counter() - tick
        memory = monitor.finish()
        row = {
            "dataset_id": dataset,
            "implementation": method,
            "batch": len(ids),
            "shape": list(x.shape),
            "train_count": len(view.ids("train")),
            "validation_count": len(view.ids("validation")),
            "cache_shape": list(cache.pixels.shape),
            "cache_seconds": cache_seconds,
            "cache_manifest_sha256": sha256_file(cache.root / "manifest.json"),
            "step_seconds": steps,
            "forward_seconds": predict_seconds,
            "weighted_loss": output["loss"],
            "memory": memory,
            "gradient_parity": parity,
            "test_accessed": False,
        }
        evidence.append(row)
        print(json.dumps(row, default=str), flush=True)
        atomic_json(
            BASE / f"preflight_{method}.json",
            {
                "status": "IN_PROGRESS",
                "at": datetime.now(UTC).isoformat(),
                "dependencies": audit,
                "datasets": evidence,
                "test_evaluation_executed": False,
            },
        )
    atomic_json(
        BASE / f"preflight_{method}.json",
        {
            "status": "PASS",
            "at": datetime.now(UTC).isoformat(),
            "dependencies": audit,
            "datasets": evidence,
            "test_evaluation_executed": False,
        },
    )


if __name__ == "__main__":
    main()
