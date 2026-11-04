"""Read-only protected locks, development-only data inventory and real-shape LSTM probe."""

import os

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import argparse
import json
import subprocess
import time
import xml.etree.ElementTree as ET

import numpy as np

from src.ch02_ml.experiment import configure
from src.ch02_ml.training import ScratchTrainer
from src.ch04_rnn_lstm.phase29.training import LstmKerasTrainer, LstmTorchTrainer
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json
from src.common.device_core import DeviceMonitor
from src.common.model_core import build_plan, canonical_weights
from src.common.numpy_engine import NumpyNetwork
from src.common.parity import gradient_parity

BASE = ROOT / "artifacts/manifests/phase29"
DATASETS = ("ch4_gold_pink_sheet", "ch4_bis_house_prices", "ch4_household_power")
LOCKS = {
    "spec22": "artifacts/manifests/phase22/spec_lock.json",
    "data24": "artifacts/manifests/phase24/data_lock.json",
    "core25": "artifacts/manifests/phase25/core_lock.json",
    "experiment26": "artifacts/manifests/phase26/revisions/r2/experiment_lock.json",
    "experiment27": "artifacts/manifests/phase27/experiment_lock.json",
    "experiment28": "artifacts/manifests/phase28/experiment_lock.json",
}


def dependencies():
    if (
        sha256_file(ROOT / LOCKS["experiment28"])
        != "afd93a2a8c8c7336670c17c8d30132f5bcc663448f7658f5a3b35d6ae1d6c27e"
    ):
        raise ValueError("Published Phase28 lock identity changed")
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
        plan = build_plan("lstm", [data.lookback, data.features.shape[1]], len(data.horizons))
        weights = canonical_weights(plan, 17)
        trainer = {"scratch": ScratchTrainer, "keras": LstmKerasTrainer, "pytorch": LstmTorchTrainer}[method](
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


def proof():
    from src.ch04_rnn_lstm.phase29.protocol import SOURCE_FILES, code_info, ref

    evidence = []
    total = 0
    for name, expected in (("pretrain-final-torch-tests.xml", 27), ("pretrain-final-keras-tests.xml", 1)):
        path = BASE / name
        suites = ET.parse(path).getroot().iter("testsuite")
        rows = list(suites)
        count = sum(int(s.get("tests", 0)) for s in rows)
        if count != expected or any(
            int(s.get(k, 0)) for s in rows for k in ("failures", "errors", "skipped")
        ):
            raise ValueError("Final pretraining tests missing/failed/skipped")
        total += count
        evidence.append(ref(path))
    path = BASE / "pretrain-final-coverage.json"
    percent = read_json(path)["totals"]["percent_covered"]
    if percent < 80:
        raise ValueError("LSTM coverage below 80%")
    evidence.append(ref(path))
    paths = [
        p
        for p in SOURCE_FILES
        if p.endswith(".py")
        and ("/phase29/" in p or "phase29_" in p or "prepare_phase29" in p or "tests/lstm29/" in p)
    ]
    result = subprocess.run(
        ["/home/anhca/.local/share/ai-term-paper-v3/.venv-torch/bin/ruff", "check", *paths],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    write_once(
        BASE / "pretrain_verification.json",
        {
            "status": "PASS",
            "code": code_info(),
            "tests": total,
            "coverage_percent": percent,
            "lint": result.stdout.strip(),
            "evidence": evidence,
            "test_evaluation_executed": False,
        },
    )
    print(json.dumps({"status": "PASS", "tests": total, "coverage_percent": percent}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--proof", action="store_true")
    parser.add_argument("--method", choices=("scratch", "keras", "pytorch"))
    parser.add_argument("--variant", choices=("initial", "xla_v1"), default="initial")
    args = parser.parse_args()
    if args.proof:
        proof()
    elif args.inventory:
        inventory()
    elif args.method:
        probe(args.method, args.variant)
    else:
        parser.error("Choose --inventory or --method")


if __name__ == "__main__":
    main()
