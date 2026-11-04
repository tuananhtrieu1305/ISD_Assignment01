"""Validation-only measured RNN runs, safe optimizer resume and CPU checkpoints."""

import gzip
import json
import os
import platform
import shutil
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from src.ch02_ml.experiment import configure, provenance
from src.ch02_ml.protocol import array_sha256
from src.ch02_ml.test_gate import atomic_json
from src.ch02_ml.training import ScratchTrainer
from src.ch04_rnn_lstm.diagnostics import gradient_diagnostics
from src.ch04_rnn_lstm.protocol import (
    BASE,
    IMPLEMENTATIONS,
    METRICS,
    MODELS,
    PREDICTIONS,
    check_sources,
    checked,
    ref,
)
from src.ch04_rnn_lstm.training import RnnKerasTrainer, RnnTorchTrainer, fit_windows, predict_windows
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.artifact_core import ArtifactStore, write_once
from src.common.contracts import ROOT, canonical_sha256, read_json, validate_document
from src.common.device_core import DeviceMonitor
from src.common.metric_core import regression_metrics
from src.common.model_core import canonical_weights
from src.common.numpy_engine import NumpyNetwork
from src.common.parity import gradient_parity
from src.common.training_core import inference_timing


def make_trainer(method, plan, weights):
    if method == "scratch":
        return ScratchTrainer(plan, weights)
    if method == "pytorch":
        return RnnTorchTrainer(plan, weights, "gpu")
    if method == "keras":
        return RnnKerasTrainer(plan, weights, "gpu")
    raise ValueError("Unknown RNN implementation")


def save_progress(run, state, config_hash):
    folder = MODELS / run / "resume"
    folder.mkdir(parents=True, exist_ok=True)
    epoch = len(state["history"])
    path = folder / f"epoch_{epoch:03d}.npz"
    arrays = {
        f"{field}/{key}": value
        for field in ("weights", "m", "v")
        for key, value in state["trainer"][field].items()
    }
    arrays.update({f"best/{key}": value for key, value in state["best_weights"].items()})
    if any(value.dtype.kind not in "fiu" or not np.isfinite(value).all() for value in arrays.values()):
        raise ValueError("Unsafe optimizer state")
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    metadata = {key: value for key, value in state.items() if key not in {"trainer", "best_weights"}}
    metadata.update(
        {"iterations": state["trainer"]["iterations"], "config_sha256": config_hash, "arrays": ref(path)}
    )
    meta_path = folder / f"epoch_{epoch:03d}.json"
    write_once(meta_path, metadata)
    atomic_json(MODELS / run / "progress.json", ref(meta_path))


def load_progress(run, config_hash):
    pointer = MODELS / run / "progress.json"
    if not pointer.exists():
        return None
    metadata = read_json(checked(read_json(pointer)))
    if metadata["config_sha256"] != config_hash:
        raise ValueError("Resume config changed")
    path = checked(metadata["arrays"])
    if path.stat().st_size > 64 * 1024**2:
        raise ValueError("Resume exceeds 64 MiB budget")
    with zipfile.ZipFile(path) as archive:
        if sum(item.file_size for item in archive.infolist()) > 64 * 1024**2:
            raise ValueError("Expanded optimizer archive exceeds 64 MiB budget")
    with np.load(path, allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in archive.files}
    if sum(value.nbytes for value in arrays.values()) > 64 * 1024**2 or any(
        value.dtype.kind not in "fiu" or not np.isfinite(value).all() for value in arrays.values()
    ):
        raise ValueError("Unsafe expanded optimizer state")
    return {
        "history": metadata["history"],
        "early_stopping": metadata["early_stopping"],
        "elapsed_seconds": metadata["elapsed_seconds"],
        "trainer": {
            **{
                field: {
                    key.removeprefix(field + "/"): value
                    for key, value in arrays.items()
                    if key.startswith(field + "/")
                }
                for field in ("weights", "m", "v")
            },
            "iterations": metadata["iterations"],
        },
        "best_weights": {
            key.removeprefix("best/"): value for key, value in arrays.items() if key.startswith("best/")
        },
    }


def metric_rows(values, unit):
    rows = []
    for horizon, group in [
        (None, values),
        *[(int(h), group) for h, group in values.get("by_horizon", {}).items()],
    ]:
        for name in ("rmse", "mae", "smape", "macro_series_rmse"):
            if name in group:
                rows.append(
                    {
                        "name": name,
                        **group[name],
                        "unit": "percent" if name == "smape" else unit,
                        "direction": "min",
                        "horizon": horizon,
                    }
                )
    return rows


def record(entry, config, data, values, efficiency, started, artifacts):
    document = {
        "schema_version": "3.0.0",
        "evidence_kind": "measured",
        "run_id": entry["run_id"],
        "dataset_id": entry["dataset_id"],
        "split_id": f"{entry['dataset_id']}_phase28_{'main' if entry['fold'] is None else 'fold' + str(entry['fold'])}",
        "split_sha256": config["provenance"]["split_sha256"],
        "config_sha256": entry["config"]["sha256"],
        "code": config["code"],
        "environment_sha256": config["environment_sha256"],
        "model_contract": entry["model_contract"],
        "implementation": entry["method"],
        "backend": {"scratch": "numpy", "keras": "tensorflow", "pytorch": "torch"}.get(
            entry["method"], "numpy"
        ),
        "family": "rnn",
        "track": "matched_subset",
        "seed": entry["seed"],
        "subset_sha256": config["provenance"]["subset_sha256"],
        "status": "succeeded",
        "split": "validation",
        "test_seal_id": None,
        "device": "cuda:0" if entry["method"] in {"keras", "pytorch"} else "cpu",
        "dtype": "float32",
        "batch_size": config["training"]["batch_size"],
        "started_at": started,
        "finished_at": datetime.now(UTC).isoformat(),
        "metrics": metric_rows(values, config["unit"]),
        "efficiency": efficiency,
        "artifacts": artifacts,
        "warnings": [
            "Validation only; no TEST evaluation in Phase28",
            "Latest revised snapshots, retrospective observation-origin forecast; no real-time publication/vintage claim or investment advice",
            "Each rolling fold uses its frozen scaler; windows reset recurrent state",
            "Train wall includes validation/progress I/O; RAM is process lifetime, VRAM allocator only; CPU/GPU and graph/eager differ",
        ],
        "dataset_sha256": config["provenance"]["dataset_sha256"],
        "comparison_group_sha256": entry["comparison_group_sha256"],
        "protocol_sha256": config["protocol_sha256"],
        "preprocessing": data.view.contract()["preprocessing"],
    }
    if entry["method"] in IMPLEMENTATIONS:
        validate_document("run", document, publish=True)
    else:
        document.update(
            {
                "schema_version": "phase28.causal_baseline_run.1",
                "family": "classical",
                "implementation": "numpy",
                "method": entry["method"],
            }
        )
    return document


def save_predictions(run, data, targets, predictions):
    path = PREDICTIONS / "validation" / f"{run}.jsonl.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream, gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as packed:
        for key, target, pred in zip(data.validation_ids, targets, predictions, strict=True):
            row = {
                "id": key,
                "series": data.rows[key]["series"],
                "target_times": data.rows[key]["target_times"],
                "target": target.tolist(),
                "prediction": pred.tolist(),
            }
            packed.write((json.dumps(row, sort_keys=True, allow_nan=False) + "\n").encode())
    return ref(path)


def train_run(run):
    release = check_sources()
    entry = next(row for row in release["runs"] if row["run_id"] == run)
    folder = BASE / "runs" / run
    if (folder / "selection.json").exists():
        selected = read_json(folder / "selection.json")
        for value in selected.values():
            if isinstance(value, dict) and set(value) == {"path", "sha256"}:
                checked(value)
        return {"run_id": run, "status": "reused"}
    if shutil.disk_usage(ROOT).free < 5 * 1024**3:
        raise OSError("Host disk below 5 GiB reserve")
    claim = folder / "training_claim.json"
    if (
        claim.exists()
        and read_json(claim)["pid"] != os.getpid()
        and Path(f"/proc/{read_json(claim)['pid']}").exists()
    ):
        raise ValueError("Live worker owns recurrent run")
    atomic_json(claim, {"pid": os.getpid(), "run_id": run})
    config = read_json(checked(entry["config"]))
    method, started = entry["method"], datetime.now(UTC).isoformat()
    backend = configure(method, entry["seed"])
    tick = time.perf_counter()
    data = WindowData(entry["dataset_id"], entry["fold"])
    if data.contract() != read_json(checked(config["data_contract"])):
        raise ValueError("Declared recurrent data contract changed")
    x_demo, y_demo = data.batch(data.train_ids[:4])
    prep_seconds = time.perf_counter() - tick
    monitor = DeviceMonitor(backend, "gpu" if method in {"keras", "pytorch"} else "cpu")
    monitor.start()
    if method in IMPLEMENTATIONS:
        weights = canonical_weights(config["plan"], entry["seed"])
        if (
            canonical_sha256({k: v.tolist() for k, v in weights.items()})
            != config["canonical_initial_weights_sha256"]
        ):
            raise ValueError("Initialization changed")
        trainer = make_trainer(method, config["plan"], weights)
        reference = NumpyNetwork(config["plan"], weights)
        np.testing.assert_allclose(trainer.predict(x_demo), reference.forward(x_demo), atol=1e-5, rtol=1e-4)
        expected = reference.loss_gradients(x_demo, y_demo, "mse")[1]
        actual = expected if method == "scratch" else trainer.model.loss_gradients(x_demo, y_demo, "mse")[1]
        write_once(
            folder / "initial_parity.json",
            {
                "forward": "PASS",
                "gradient": gradient_parity(expected, actual),
                "input_split": "train",
                "ids": data.train_ids[:4],
            },
        )
        result = fit_windows(
            trainer,
            data,
            seed=entry["seed"],
            budget=config["training"],
            resume=load_progress(run, entry["config"]["sha256"]),
            progress=lambda state: save_progress(run, state, entry["config"]["sha256"]),
        )
        weights, history, best_epoch, train_seconds = (
            result["weights"],
            result["history"],
            result["best_epoch"],
            result["train_seconds"],
        )
        output = data.adapter.inverse_target(predict_windows(trainer, data, data.validation_ids))
        native_demo = trainer.predict(x_demo)
        predict_one = lambda: trainer.predict(x_demo[:1])
        write_once(
            folder / "gradient_diagnostics.json",
            {**gradient_diagnostics(config["plan"], weights, x_demo, y_demo), "ids": data.train_ids[:4]},
        )
    else:
        tick = time.perf_counter()
        weights = {"baseline_kind": np.asarray([int(method == "seasonal_naive")], dtype="int64")}
        train_seconds = time.perf_counter() - tick
        output = data.baseline(data.validation_ids, method)
        native_demo = data.baseline(data.train_ids[:4], method)
        predict_one = lambda: data.baseline(data.train_ids[:1], method)
        history, best_epoch = [], None
    memory = monitor.finish()
    if method in {"keras", "pytorch"} and not 0 < memory["peak_vram_bytes"] < 8 * 1024**3:
        raise ValueError("Invalid GPU memory measurement")
    timing = inference_timing(predict_one, monitor.synchronize)
    targets = data.targets(data.validation_ids)
    values = regression_metrics(targets, output, data.horizons, data.series(data.validation_ids))
    cp = ArtifactStore(MODELS / run).save_checkpoint("best", weights, provenance(entry, config))
    checkpoint, metadata = ref(MODELS / run / "best.npz"), ref(MODELS / run / "best.json")
    loaded = ArtifactStore(MODELS / run).load_checkpoint(
        "best", provenance(entry, config), expected_manifest_sha256=metadata["sha256"]
    )
    cpu = (
        NumpyNetwork(config["plan"], loaded).forward(x_demo)
        if method in IMPLEMENTATIONS
        else data.baseline(data.train_ids[:4], method)
    )
    np.testing.assert_allclose(cpu, native_demo, atol=1e-5, rtol=1e-4)
    write_once(
        folder / "cpu_demo.json",
        {
            "status": "PASS",
            "input_split": "train",
            "ids": data.train_ids[:4],
            "canonical_x_sha256": array_sha256(x_demo),
            "raw_output": cpu.tolist(),
            "max_absolute_error": float(np.max(np.abs(cpu - native_demo))),
            "checkpoint": checkpoint,
            "serving_backend": "numpy_cpu_portable",
            "training_implementation": method,
        },
    )
    write_once(folder / "history.json", history)
    details = {
        "metrics": values,
        "memory": memory,
        "best_epoch": best_epoch,
        "preprocessing_seconds": prep_seconds,
        "train_count": len(data.train_ids),
        "validation_count": len(data.validation_ids),
        "unit": config["unit"],
        "fold": entry["fold"],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "test_evaluation_executed": False,
    }
    write_once(folder / "validation_details.json", details)
    predictions = save_predictions(run, data, targets, output)
    efficiency = {
        "train_seconds": train_seconds,
        "inference_p50_ms": timing["inference_p50_ms"],
        "inference_p95_ms": timing["inference_p95_ms"],
        "warmup_batches": timing["warmup"],
        "timed_repeats": timing["repeats"],
        "peak_ram_bytes": memory["process_peak_ram_bytes"],
        "peak_vram_bytes": memory["peak_vram_bytes"],
        "checkpoint_bytes": cp["size_bytes"],
    }
    metric_path = METRICS / "validation" / f"{run}.json"
    write_once(
        metric_path,
        record(entry, config, data, values, efficiency, started, [checkpoint, metadata, predictions]),
    )
    write_once(
        folder / "selection.json",
        {
            "run_id": run,
            "status": "succeeded",
            "lifecycle": "trained_validation_selected",
            "selection_split": "validation",
            "inference_ready": True,
            "best_epoch": best_epoch,
            "checkpoint": checkpoint,
            "checkpoint_metadata": metadata,
            "validation_metrics": ref(metric_path),
            "validation_predictions": predictions,
            "history": ref(folder / "history.json"),
            "details": ref(folder / "validation_details.json"),
            "cpu_demo": ref(folder / "cpu_demo.json"),
            "config": entry["config"],
            "model_contract": entry["model_contract"],
            "comparison_group_sha256": entry["comparison_group_sha256"],
            "test_evaluation_executed": False,
        },
    )
    return {
        "run_id": run,
        "status": "PASS",
        "epochs": len(history),
        "best_epoch": best_epoch,
        "rmse": values["rmse"]["value"],
        "train_seconds": train_seconds,
    }
