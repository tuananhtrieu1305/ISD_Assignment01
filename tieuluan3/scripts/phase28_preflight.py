"""Read-only protected locks, development-only data inventory and real-shape RNN probe."""

import os

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import argparse
import json
import time

import numpy as np

from src.ch02_ml.experiment import configure
from src.ch02_ml.training import ScratchTrainer
from src.ch04_rnn_lstm.training import RnnKerasTrainer, RnnTorchTrainer
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json
from src.common.device_core import DeviceMonitor
from src.common.model_core import build_plan, canonical_weights
from src.common.numpy_engine import NumpyNetwork
from src.common.parity import gradient_parity

BASE = ROOT / "artifacts/manifests/phase28"
DATASETS = ("ch4_gold_pink_sheet", "ch4_bis_house_prices", "ch4_household_power")
LOCKS = {
    "spec22": "artifacts/manifests/phase22/spec_lock.json",
    "data24": "artifacts/manifests/phase24/data_lock.json",
    "core25": "artifacts/manifests/phase25/core_lock.json",
    "experiment26": "artifacts/manifests/phase26/revisions/r2/experiment_lock.json",
    "experiment27": "artifacts/manifests/phase27/experiment_lock.json",
}


def dependencies():
    result = {}
    for name, path in LOCKS.items():
        lock = read_json(ROOT / path)
        for row in lock["files"]:
            if sha256_file(ROOT / row["path"]) != row["sha256"]:
                raise ValueError(f"Protected file changed: {row['path']}")
        result[name] = {
            "path": path,
            "sha256": sha256_file(ROOT / path),
            "verified_files": len(lock["files"]),
        }
    return result


def inventory():
    protected = dependencies()
    for dataset in DATASETS:
        for fold in (None, 1, 2, 3):
            data = WindowData(dataset, fold)
            path = BASE / "data" / f"{dataset}_{'main' if fold is None else 'fold' + str(fold)}.json"
            write_once(path, data.contract())
            print(
                json.dumps(
                    {
                        "dataset": dataset,
                        "fold": fold,
                        "train": len(data.train_ids),
                        "validation": len(data.validation_ids),
                        "reconstructed_fold_index": len(data.reconstructed_fold_ids),
                    }
                ),
                flush=True,
            )
    write_once(
        BASE / "dependency_audit.json",
        {"status": "PASS", "locks": protected, "test_evaluation_executed": False},
    )


def probe(method, variant="initial"):
    backend = configure(method, 17)
    rows = []
    for dataset in DATASETS:
        data = WindowData(dataset)
        plan = build_plan("rnn", [data.lookback, data.features.shape[1]], len(data.horizons))
        weights = canonical_weights(plan, 17)
        trainer = {"scratch": ScratchTrainer, "keras": RnnKerasTrainer, "pytorch": RnnTorchTrainer}[method](
            plan, weights
        )
        x, y = data.batch(data.train_ids[:32])
        reference = NumpyNetwork(plan, weights)
        np.testing.assert_allclose(trainer.predict(x[:4]), reference.forward(x[:4]), rtol=1e-4, atol=1e-5)
        _, expected, _ = reference.loss_gradients(x[:4], y[:4], "mse")
        actual = expected if method == "scratch" else trainer.model.loss_gradients(x[:4], y[:4], "mse")[1]
        parity = gradient_parity(expected, actual)
        monitor = DeviceMonitor(backend, "cpu" if method == "scratch" else "gpu")
        monitor.start()
        durations = []
        for _ in range(3):
            tick = time.perf_counter()
            output = trainer.step(x, y, "mse", np.ones(len(y), "float32"))
            monitor.synchronize()
            durations.append(time.perf_counter() - tick)
        memory = monitor.finish()
        rows.append(
            {
                "dataset": dataset,
                "shape": list(x.shape),
                "step_seconds": durations,
                "parity": parity,
                "memory": memory,
                "last_loss": output["loss"],
                "test_windows_materialized": False,
            }
        )
        print(json.dumps(rows[-1]), flush=True)
    write_once(
        BASE / f"preflight_{method}{'' if variant == 'initial' else '_' + variant}.json",
        {"status": "PASS", "implementation": method, "datasets": rows, "test_evaluation_executed": False},
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--method", choices=("scratch", "keras", "pytorch"))
    parser.add_argument("--variant", choices=("initial", "xla_v1"), default="initial")
    args = parser.parse_args()
    if args.inventory:
        inventory()
    elif args.method:
        probe(args.method, args.variant)
    else:
        parser.error("Choose --inventory or --method")


if __name__ == "__main__":
    main()
