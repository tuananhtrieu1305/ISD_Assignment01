"""Measured CNN runs, portable checkpoints and one-shot sealed evaluation."""

import gzip
import json
import os
import platform
import shutil
import time
from datetime import UTC, datetime

import numpy as np

from src.ch02_ml.experiment import configure, metric_rows, provenance
from src.ch02_ml.protocol import array_sha256
from src.ch02_ml.test_gate import atomic_json
from src.ch03_cnn.image_cache import development_cache
from src.ch03_cnn.protocol import BASE, IMPLEMENTATIONS, METRICS, MODELS, PREDICTIONS, check_sources, ref
from src.ch03_cnn.training import (
    CnnKerasTrainer,
    CnnScratchTrainer,
    CnnTorchTrainer,
    fit_images,
    predict_images,
    probabilities,
)
from src.ch03_cnn.workflow import CnnEvaluationGate, test_partition_cache
from src.common.artifact_core import ArtifactStore, write_once
from src.common.contracts import ROOT, canonical_sha256, read_json, validate_document
from src.common.data_access import DatasetView
from src.common.device_core import DeviceMonitor
from src.common.metric_core import classification_metrics
from src.common.model_core import canonical_weights
from src.common.numpy_engine import NumpyNetwork
from src.common.parity import gradient_parity
from src.common.training_core import inference_timing


def checked(record):
    path = (ROOT / record["path"]).resolve()
    if not path.is_relative_to(ROOT.resolve()) or ref(path) != record:
        raise ValueError("Missing/changed/escaping approved artifact")
    return path


def make_trainer(method, plan, weights):
    if method == "scratch":
        return CnnScratchTrainer(plan, weights)
    if method == "pytorch":
        return CnnTorchTrainer(plan, weights, "gpu")
    if method == "keras":
        return CnnKerasTrainer(plan, weights, "gpu")
    raise ValueError("Unknown CNN implementation")


def save_predictions(run, split, ids, targets, predictions):
    path = PREDICTIONS / split / f"{run}.jsonl.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream, gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as packed:
        for key, target, pred in zip(ids, targets, predictions, strict=True):
            packed.write(
                (
                    json.dumps(
                        {"id": key, "target": int(target), "prediction": [float(v) for v in pred]},
                        sort_keys=True,
                        allow_nan=False,
                    )
                    + "\n"
                ).encode()
            )
    return ref(path)


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
    if any(a.dtype.kind not in "fiu" or not np.isfinite(a).all() for a in arrays.values()):
        raise ValueError("Unsafe resume array")
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    metadata = {k: v for k, v in state.items() if k not in {"trainer", "best_weights"}}
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
    with np.load(checked(metadata["arrays"]), allow_pickle=False) as packed:
        arrays = {key: packed[key] for key in packed.files}
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


def record(entry, config, split, values, efficiency, started, artifacts, seal_id=None):
    view = DatasetView(entry["dataset_id"])
    result = {
        "schema_version": "3.0.0",
        "evidence_kind": "measured",
        "run_id": entry["run_id"],
        "dataset_id": entry["dataset_id"],
        "split_id": read_json(view.split_dir / "split_contract.json")["split_id"],
        "split_sha256": config["provenance"]["split_sha256"],
        "config_sha256": entry["config"]["sha256"],
        "code": config["code"],
        "environment_sha256": config["environment_sha256"],
        "model_contract": entry["model_contract"],
        "implementation": entry["method"],
        "backend": {"scratch": "numpy", "keras": "tensorflow", "pytorch": "torch", "majority": "numpy"}[
            entry["method"]
        ],
        "family": "cnn",
        "track": "matched_subset",
        "seed": entry["seed"],
        "subset_sha256": config["provenance"]["subset_sha256"],
        "status": "succeeded",
        "split": split,
        "test_seal_id": seal_id,
        "device": "cuda:0" if entry["method"] in {"keras", "pytorch"} else "cpu",
        "dtype": "float32",
        "batch_size": config["training"]["batch_size"],
        "started_at": started,
        "finished_at": datetime.now(UTC).isoformat(),
        "metrics": metric_rows(values, "multiclass"),
        "efficiency": efficiency,
        "artifacts": artifacts,
        "warnings": [
            "Academic demonstration, not medical diagnosis",
            "No verified patient/geographic independence",
            "Matched subset and low resolution, not state-of-the-art full-data benchmark",
            "RAM is process-lifetime RSS; VRAM is framework allocator",
            "Train wall includes validation/checkpoint I/O; inference model+transfer only",
            "TEST records inherit validation timing, not a new speed benchmark",
        ],
        "dataset_sha256": config["provenance"]["dataset_sha256"],
        "comparison_group_sha256": entry["comparison_group_sha256"],
        "protocol_sha256": config["protocol_sha256"],
        "preprocessing": view.contract()["preprocessing"],
    }
    if entry["method"] == "majority":
        result.update(
            {
                "schema_version": "phase27.majority_run.1",
                "family": "classical",
                "implementation": "numpy",
                "method": "majority",
                "layer_count_applicable": False,
            }
        )
    else:
        validate_document("run", result, publish=True)
    return result


def train_run(run):
    release = check_sources()
    if any(
        (BASE / "test_seals" / dataset / "evaluation.started").exists()
        for dataset in ("ch3_idrid", "ch3_eurosat", "ch3_cifar10")
    ):
        raise ValueError("Training prohibited after TEST started")
    entry = next(row for row in release["runs"] if row["run_id"] == run)
    folder = BASE / "runs" / run
    if (folder / "selection.json").exists():
        selection = read_json(folder / "selection.json")
        for key in (
            "checkpoint",
            "checkpoint_metadata",
            "validation_metrics",
            "validation_predictions",
            "history",
            "details",
            "cpu_demo",
        ):
            checked(selection[key])
        return {"run_id": run, "status": "reused"}
    if shutil.disk_usage(ROOT).free < 5 * 1024**3:
        raise OSError("Host disk below 5 GiB reserve")
    claim = folder / "training_claim.json"
    if (
        claim.exists()
        and read_json(claim)["pid"] != os.getpid()
        and (ROOT.__class__(f"/proc/{read_json(claim)['pid']}")).exists()
    ):
        raise ValueError("Live process owns CNN run")
    atomic_json(claim, {"pid": os.getpid(), "run_id": run, "started_at": datetime.now(UTC).isoformat()})
    config = read_json(checked(entry["config"]))
    method = entry["method"]
    backend = configure(method, entry["seed"])
    started = datetime.now(UTC).isoformat()
    tick = time.perf_counter()
    cache, view = development_cache(entry["dataset_id"])
    if ref(cache.root / "manifest.json") != config["cache_manifest"]:
        raise ValueError("Declared development cache changed")
    train_ids, val_ids = view.ids("train"), view.ids("validation")
    x_demo, _ = cache.batch(train_ids[:4])
    prep_seconds = time.perf_counter() - tick
    monitor = DeviceMonitor(backend, "gpu" if method in {"keras", "pytorch"} else "cpu")
    monitor.start()
    if method in IMPLEMENTATIONS:
        weights = canonical_weights(config["plan"], entry["seed"])
        if (
            canonical_sha256({k: v.tolist() for k, v in weights.items()})
            != config["canonical_initial_weights_sha256"]
        ):
            raise ValueError("CNN initialization changed")
        trainer = make_trainer(method, config["plan"], weights)
        reference = NumpyNetwork(config["plan"], weights)
        np.testing.assert_allclose(
            trainer.predict(x_demo),
            reference.forward(x_demo),
            atol=1e-5,
            rtol=1e-4,
        )
        parity = {"forward": "PASS", "gradient": None, "input_split": "train", "ids": train_ids[:2]}
        if method != "scratch":
            _, y_pair = cache.batch(train_ids[:2])
            _, expected_gradient, _ = reference.loss_gradients(x_demo[:2], y_pair, "multiclass")
            _, actual_gradient = trainer.model.loss_gradients(x_demo[:2], y_pair, "multiclass")
            parity["gradient"] = gradient_parity(expected_gradient, actual_gradient)
        write_once(folder / "initial_parity.json", parity)
        result = fit_images(
            trainer,
            cache,
            train_ids,
            val_ids,
            seed=entry["seed"],
            budget=config["training"],
            class_weights=config["class_weights"],
            resume=load_progress(run, entry["config"]["sha256"]),
            progress=lambda state: save_progress(run, state, entry["config"]["sha256"]),
        )
        weights, history, train_seconds, best_epoch = (
            result["weights"],
            result["history"],
            result["train_seconds"],
            result["best_epoch"],
        )
        output = probabilities(predict_images(trainer, cache, val_ids))
        native_demo = trainer.predict(x_demo)
        predict_one = lambda: trainer.predict(x_demo[:1])
    else:
        tick = time.perf_counter()
        labels = np.asarray([cache.labels[cache.positions[k]] for k in train_ids])
        chosen = int(np.bincount(labels, minlength=view.spec["class_count"]).argmax())
        weights = {"class_probabilities": np.eye(view.spec["class_count"], dtype="float32")[chosen]}
        train_seconds = time.perf_counter() - tick
        output = np.tile(weights["class_probabilities"], (len(val_ids), 1))
        native_demo = np.tile(weights["class_probabilities"], (len(x_demo), 1))
        predict_one = lambda: np.tile(weights["class_probabilities"], (1, 1))
        history, best_epoch = [], None
    memory = monitor.finish()
    if method in {"keras", "pytorch"} and not 0 < memory["peak_vram_bytes"] < 8 * 1024**3:
        raise ValueError("Missing/excessive native GPU allocator measurement")
    timing = inference_timing(predict_one, monitor.synchronize)
    y = np.asarray([cache.labels[cache.positions[k]] for k in val_ids])
    values = classification_metrics(y, output)
    metadata = ArtifactStore(MODELS / run).save_checkpoint("best", weights, provenance(entry, config))
    checkpoint, cp_meta = ref(MODELS / run / "best.npz"), ref(MODELS / run / "best.json")
    loaded = ArtifactStore(MODELS / run).load_checkpoint(
        "best", provenance(entry, config), expected_manifest_sha256=cp_meta["sha256"]
    )
    cpu = (
        NumpyNetwork(config["plan"], loaded).forward(x_demo)
        if method in IMPLEMENTATIONS
        else np.tile(loaded["class_probabilities"], (len(x_demo), 1))
    )
    np.testing.assert_allclose(cpu, native_demo, atol=1e-5, rtol=1e-4)
    write_once(
        folder / "cpu_demo.json",
        {
            "status": "PASS",
            "input_split": "train",
            "ids": train_ids[:4],
            "canonical_x_sha256": array_sha256(x_demo),
            "raw_output": cpu.tolist(),
            "max_absolute_error": float(np.max(np.abs(cpu - native_demo))),
            "checkpoint": checkpoint,
            "load_policy": "numpy_no_pickle",
            "serving_backend": "numpy_cpu_portable",
            "training_implementation": method,
        },
    )
    write_once(folder / "history.json", history)
    write_once(
        folder / "validation_details.json",
        {
            "metrics": values,
            "memory": memory,
            "preprocessing_seconds": prep_seconds,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "class_names": config["class_names"],
            "best_epoch": best_epoch,
            "output_dtype": str(output.dtype),
            "no_augmentation": True,
            "train_count": len(train_ids),
            "validation_count": len(val_ids),
        },
    )
    predictions = save_predictions(run, "validation", val_ids, y, output)
    efficiency = {
        "train_seconds": train_seconds,
        "inference_p50_ms": timing["inference_p50_ms"],
        "inference_p95_ms": timing["inference_p95_ms"],
        "warmup_batches": 5,
        "timed_repeats": 30,
        "peak_ram_bytes": memory["process_peak_ram_bytes"],
        "peak_vram_bytes": memory["peak_vram_bytes"],
        "checkpoint_bytes": metadata["size_bytes"],
    }
    metric_path = METRICS / "validation" / f"{run}.json"
    write_once(
        metric_path,
        record(entry, config, "validation", values, efficiency, started, [checkpoint, cp_meta, predictions]),
    )
    write_once(
        folder / "selection.json",
        {
            "run_id": run,
            "status": "succeeded",
            "lifecycle": "trained_validation_selected",
            "inference_ready": True,
            "selection_split": "validation",
            "best_epoch": best_epoch,
            "checkpoint": checkpoint,
            "checkpoint_metadata": cp_meta,
            "validation_predictions": predictions,
            "validation_metrics": ref(metric_path),
            "history": ref(folder / "history.json"),
            "details": ref(folder / "validation_details.json"),
            "cpu_demo": ref(folder / "cpu_demo.json"),
            "model_contract": entry["model_contract"],
            "config": entry["config"],
            "comparison_group_sha256": entry["comparison_group_sha256"],
            "cpu_loadable": True,
            "test_evaluation_executed": False,
        },
    )
    return {
        "run_id": run,
        "status": "succeeded",
        "epochs": len(history),
        "best_epoch": best_epoch,
        "macro_f1": values["macro_f1"]["value"],
        "train_seconds": train_seconds,
    }


def evaluate_run(run):
    release = check_sources()
    entry = next(row for row in release["runs"] if row["run_id"] == run)
    config = read_json(checked(entry["config"]))
    gate = CnnEvaluationGate(BASE / "test_seals" / entry["dataset_id"])
    gate.claim(run, release["code"]["dirty_tree_sha256"])
    for artifact in read_json(gate.root / "manifest.json")["artifacts"]:
        checked(artifact)
    selected = read_json(BASE / "runs" / run / "selection.json")
    weights = ArtifactStore(MODELS / run).load_checkpoint(
        "best", provenance(entry, config), expected_manifest_sha256=selected["checkpoint_metadata"]["sha256"]
    )
    configure(entry["method"], entry["seed"])
    started = datetime.now(UTC).isoformat()
    cache, _view, ids = test_partition_cache(entry["dataset_id"], gate, run)
    if entry["method"] in IMPLEMENTATIONS:
        trainer = make_trainer(entry["method"], config["plan"], weights)
        output = probabilities(predict_images(trainer, cache, ids))
    else:
        output = np.tile(weights["class_probabilities"], (len(ids), 1))
    values = classification_metrics(np.asarray(cache.labels), output)
    prediction = save_predictions(run, "test", ids, cache.labels, output)
    folder = BASE / "runs" / run
    write_once(
        folder / "test_details.json",
        {
            "metrics": values,
            "class_names": config["class_names"],
            "output_dtype": str(output.dtype),
            "diagnostic_only_no_tuning": True,
            "test_count": len(ids),
        },
    )
    path = METRICS / "test" / f"{run}.json"
    efficiency = read_json(checked(selected["validation_metrics"]))["efficiency"]
    write_once(
        path,
        record(
            entry,
            config,
            "test",
            values,
            efficiency,
            started,
            [selected["checkpoint"], prediction],
            gate.state()["seal_id"],
        ),
    )
    gate.record(
        run,
        {
            "status": "PASS",
            "predictions": prediction,
            "metrics": ref(path),
            "details": ref(folder / "test_details.json"),
        },
    )
    return {"run_id": run, "status": "PASS", "test_prediction_count": len(ids)}
