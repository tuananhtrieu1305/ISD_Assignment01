"""Real Chapter2 runs, immutable selections and schema-valid measured results."""

from __future__ import annotations

import gzip
import json
import os
import platform
import shutil
import time
import uuid
from datetime import UTC, datetime

import numpy as np

from src.ch02_ml.baselines import PortableBaseline, fit_baseline
from src.ch02_ml.diagnostics import calibration, group_diagnostics, groups_for_frame
from src.ch02_ml.protocol import (
    BASE,
    IMPLEMENTATIONS,
    METRICS,
    MODELS,
    PREDICTIONS,
    array_sha256,
    cache_data,
    check_sources,
    dataset_spec,
    ref,
    test_data,
)
from src.ch02_ml.test_gate import EvaluationGate, atomic_json
from src.ch02_ml.training import (
    KerasTrainer,
    ScratchTrainer,
    TorchTrainer,
    fit,
    predict_batches,
    task_outputs,
)
from src.common.artifact_core import ArtifactStore, sha256_file, write_once
from src.common.contracts import ROOT, canonical_sha256, read_json, validate_document
from src.common.data_access import DatasetView
from src.common.device_core import DeviceMonitor
from src.common.metric_core import classification_metrics, regression_metrics
from src.common.model_core import canonical_weights
from src.common.numpy_engine import NumpyNetwork
from src.common.parity import gradient_parity
from src.common.training_core import inference_timing, seed_everything


def configure(method, seed):
    backend = {"scratch": "numpy", "keras": "tensorflow", "pytorch": "torch"}.get(method, "numpy")
    if backend == "torch":
        import torch

        torch.set_num_threads(2)
    elif backend == "tensorflow":
        import tensorflow as tf

        tf.config.threading.set_intra_op_parallelism_threads(2)
        tf.config.threading.set_inter_op_parallelism_threads(2)
        for gpu in tf.config.list_physical_devices("GPU"):
            tf.config.experimental.set_memory_growth(gpu, True)
        tf.config.experimental.enable_tensor_float_32_execution(False)
    seed_everything(seed, backend)
    return backend


def make_trainer(method, plan, weights, device=None):
    if method == "scratch":
        return ScratchTrainer(plan, weights)
    if method == "pytorch":
        return TorchTrainer(plan, weights, device or "gpu")
    if method == "keras":
        return KerasTrainer(plan, weights, device or "gpu")
    raise ValueError("Unknown MLP method")


def provenance(entry, config):
    return {
        **config["provenance"],
        "adapter_sha256": config["adapter"]["sha256"],
        "config_sha256": entry["config"]["sha256"],
        "code_sha256": config["code"]["dirty_tree_sha256"],
        "environment_sha256": config["environment_sha256"],
        "model_contract_sha256": entry["model_contract"]["sha256"],
    }


def metrics_for(target_original, raw_output, task, adapter):
    if task == "binary":
        probs = task_outputs(raw_output, task) if raw_output.shape[1] == 1 else raw_output
        values = classification_metrics(np.asarray(target_original, dtype=int), probs)
        diagnostic = calibration(target_original, probs[:, 1])
        values["brier"] = {"value": diagnostic["brier"], "undefined_reason": None}
        values["ece"] = {"value": diagnostic["ece"], "undefined_reason": None}
        return values, probs, diagnostic
    prediction = adapter.inverse_target(raw_output).reshape(-1)
    values = regression_metrics(target_original, prediction)
    positive = np.abs(target_original) > 1e-8
    values["mape"] = {
        "value": float(np.mean(np.abs(prediction - target_original) / np.abs(target_original)) * 100)
        if positive.all()
        else None,
        "undefined_reason": None if positive.all() else "Zero/near-zero true targets",
    }
    return values, prediction[:, None], None


def metric_rows(values, task):
    rows = []
    scalar = {key: value for key, value in values.items() if isinstance(value, dict) and "value" in value}
    for label, value in values.get("per_class_recall", {}).items():
        scalar[f"recall_class_{label}"] = value
    for name, value in scalar.items():
        direction = (
            "max"
            if name in {"accuracy", "macro_f1", "weighted_f1", "auroc", "average_precision", "r2"}
            or name.startswith("recall_")
            else "min"
        )
        rows.append(
            {
                "name": name,
                **value,
                "unit": "USD"
                if task == "mse" and name in {"mae", "rmse"}
                else "percent"
                if name in {"mape", "smape"}
                else "ratio",
                "direction": direction,
                "horizon": None,
            }
        )
    return rows


def save_predictions(run, split, ids, targets, predictions):
    path = PREDICTIONS / split / f"{run}.jsonl.gz"
    if path.exists():
        raise ValueError("Prediction artifact already exists; do not overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    with (
        path.open("xb") as outgoing,
        gzip.GzipFile(filename="", fileobj=outgoing, mode="wb", mtime=0) as packed,
    ):
        for index, key in enumerate(ids):
            row = {
                "id": key,
                "target": float(targets[index]),
                "prediction": [float(v) for v in predictions[index]],
            }
            packed.write((json.dumps(row, sort_keys=True, allow_nan=False) + "\n").encode())
    return ref(path)


def save_progress(run, state, config_hash):
    folder = MODELS / run
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "progress.npz"
    arrays = {
        f"{field}/{key}": value
        for field in ("weights", "m", "v")
        for key, value in state["trainer"][field].items()
    }
    arrays.update({f"best/{key}": value for key, value in state["best_weights"].items()})
    temporary = path.with_name(path.name + f".{uuid.uuid4().hex}.tmp")
    with temporary.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    os.replace(temporary, path)
    metadata = {k: v for k, v in state.items() if k not in {"trainer", "best_weights"}}
    metadata.update(
        {"iterations": state["trainer"]["iterations"], "config_sha256": config_hash, "arrays": ref(path)}
    )
    atomic_json(folder / "progress.json", metadata)


def load_progress(run, config_hash):
    path = MODELS / run / "progress.json"
    if not path.exists():
        return None
    metadata = read_json(path)
    record = metadata["arrays"]
    if metadata["config_sha256"] != config_hash or sha256_file(ROOT / record["path"]) != record["sha256"]:
        raise ValueError("Resume state/config integrity mismatch")
    with np.load(ROOT / record["path"], allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in archive.files}
    state = {
        "history": metadata["history"],
        "early_stopping": metadata["early_stopping"],
        "elapsed_seconds": metadata["elapsed_seconds"],
        "trainer": {
            field: {k.removeprefix(field + "/"): v for k, v in arrays.items() if k.startswith(field + "/")}
            for field in ("weights", "m", "v")
        },
        "best_weights": {k.removeprefix("best/"): v for k, v in arrays.items() if k.startswith("best/")},
    }
    state["trainer"]["iterations"] = metadata["iterations"]
    return state


def run_record(entry, config, split, values, efficiency, started, finished, artifacts, seal_id=None):
    if entry["method"] not in IMPLEMENTATIONS:
        return {
            "schema_version": "phase26.classical_run.1",
            "run_id": entry["run_id"],
            "dataset_id": entry["dataset_id"],
            "method": entry["method"],
            "family": "classical",
            "implementation": "scikit_learn",
            "backend": "sklearn_fit_numpy_portable_predict",
            "seed": entry["seed"],
            "split": split,
            "track": "matched_subset",
            "status": "succeeded",
            "metrics": metric_rows(values, config["task"]),
            "efficiency": efficiency,
            "config": entry["config"],
            "model_contract": entry["model_contract"],
            "provenance": provenance(entry, config),
            "code": config["code"],
            "device": "cpu",
            "test_seal_id": seal_id,
            "artifacts": artifacts,
            "started_at": started,
            "finished_at": finished,
        }
    view = DatasetView(entry["dataset_id"])
    spec = read_json(view.split_dir / "split_contract.json")
    document = {
        "schema_version": "3.0.0",
        "evidence_kind": "measured",
        "run_id": entry["run_id"],
        "dataset_id": entry["dataset_id"],
        "split_id": spec["split_id"],
        "split_sha256": config["provenance"]["split_sha256"],
        "config_sha256": entry["config"]["sha256"],
        "code": config["code"],
        "environment_sha256": config["environment_sha256"],
        "model_contract": entry["model_contract"],
        "implementation": entry["method"],
        "backend": {"scratch": "numpy", "keras": "tensorflow", "pytorch": "torch"}[entry["method"]],
        "family": "mlp",
        "track": "matched_subset",
        "seed": entry["seed"],
        "subset_sha256": config["provenance"]["subset_sha256"],
        "status": "succeeded",
        "split": split,
        "test_seal_id": seal_id,
        "device": "cpu" if entry["method"] == "scratch" else "cuda:0",
        "dtype": "float32",
        "batch_size": config["training"]["batch_size"],
        "started_at": started,
        "finished_at": finished,
        "metrics": metric_rows(values, config["task"]),
        "efficiency": efficiency,
        "artifacts": artifacts,
        "warnings": [
            "Retrospective group split; no clinical or market-deployment claim",
            "RAM is process-lifetime peak RSS; VRAM is framework allocator only",
            "Inference includes transfer; TensorFlow graph versus PyTorch/NumPy eager",
        ],
        "dataset_sha256": config["provenance"]["dataset_sha256"],
        "comparison_group_sha256": entry["comparison_group_sha256"],
        "protocol_sha256": config["protocol_sha256"],
        "preprocessing": view.contract()["preprocessing"],
    }
    validate_document("run", document, publish=True)
    return document


def train_run(run):
    release = check_sources()
    entry = next(row for row in release["runs"] if row["run_id"] == run)
    for record in (entry["config"], entry["model_contract"]):
        if sha256_file(ROOT / record["path"]) != record["sha256"]:
            raise ValueError("Declared configuration/contract changed before training")
    folder = BASE / "runs" / run
    selection_path = folder / "selection.json"
    if selection_path.exists():
        selected = read_json(selection_path)
        for record in (
            selected["checkpoint"],
            selected["checkpoint_metadata"],
            selected["validation_metrics"],
            selected["validation_predictions"],
        ):
            if sha256_file(ROOT / record["path"]) != record["sha256"]:
                raise ValueError("Completed run artifact changed")
        return {"run_id": run, "status": "reused"}
    if shutil.disk_usage(ROOT).free < 5 * 1024**3:
        raise OSError("Host C free storage below 5 GiB reserve")
    claim = folder / "training_claim.json"
    if claim.exists():
        old = read_json(claim)
        if old["pid"] != os.getpid() and (ROOT.__class__(f"/proc/{old['pid']}")).exists():
            raise ValueError("A training process still owns this run")
    atomic_json(
        claim,
        {
            "pid": os.getpid(),
            "run_id": run,
            "config_sha256": entry["config"]["sha256"],
            "started_at": datetime.now(UTC).isoformat(),
        },
    )
    config = read_json(ROOT / entry["config"]["path"])
    method = entry["method"]
    task = config["task"]
    view = DatasetView(entry["dataset_id"])
    backend = configure(method, entry["seed"])
    device = "gpu" if method in {"keras", "pytorch"} else "cpu"
    started_at = datetime.now(UTC).isoformat()
    prep_start = time.perf_counter()
    data = cache_data(entry["dataset_id"])
    preprocessing_seconds = time.perf_counter() - prep_start
    monitor = DeviceMonitor(backend, device)
    monitor.start()
    training_start = time.perf_counter()
    if method in IMPLEMENTATIONS:
        weights = canonical_weights(config["plan"], entry["seed"])
        if (
            canonical_sha256({k: v.tolist() for k, v in weights.items()})
            != config["canonical_initial_weights_sha256"]
        ):
            raise ValueError("Initialization hash mismatch")
        trainer = make_trainer(method, config["plan"], weights)
        # Paired first-batch checks use only fixed TRAIN samples, never TEST.
        reference = NumpyNetwork(config["plan"], weights)
        x = data["train_x"][:4]
        y = data["train_y"][:4]
        np.testing.assert_allclose(trainer.predict(x), reference.forward(x), rtol=1e-4, atol=1e-5)
        if method != "scratch":
            _, reference_grad, _ = reference.loss_gradients(x, y, task)
            _, native_grad = trainer.model.loss_gradients(x, y, task)
            gradient_parity(reference_grad, native_grad)
        resumed = load_progress(run, entry["config"]["sha256"])
        result = fit(
            trainer,
            data["train_x"],
            data["train_y"],
            data["validation_x"],
            data["validation_y"],
            task,
            seed=entry["seed"],
            budget=config["training"],
            class_weights=config["class_weights"],
            progress=lambda state: save_progress(run, state, entry["config"]["sha256"]),
            resume=resumed,
        )
        weights = result["weights"]
        raw = predict_batches(trainer, data["validation_x"])
        predict = lambda value: predict_batches(trainer, value)
        history = result["history"]
        best_epoch = result["best_epoch"]
        train_seconds = result["train_seconds"]
        reference = NumpyNetwork(config["plan"], weights)
        np.testing.assert_allclose(
            trainer.predict(data["train_x"][:4]), reference.forward(data["train_x"][:4]), rtol=1e-4, atol=1e-5
        )
        portable_meta = None
    else:
        fitted, portable = fit_baseline(
            method,
            data["train_x"],
            data["train_y"],
            task,
            seed=entry["seed"],
            settings=config["forest"],
            class_weights=config["class_weights"],
        )
        train_seconds = time.perf_counter() - training_start
        raw = portable.predict(data["validation_x"])
        expected = (
            fitted.predict_proba(data["validation_x"])
            if task == "binary"
            else fitted.predict(data["validation_x"]).reshape(-1, 1)
        )
        np.testing.assert_allclose(raw, expected, rtol=1e-5, atol=1e-5)
        weights = portable.arrays
        portable_meta = portable.metadata
        predict = portable.predict
        history = []
        best_epoch = None
    memory = monitor.finish()
    timing = inference_timing(lambda: predict(data["train_x"][:1]), monitor.synchronize)
    if device == "gpu" and not 0 < memory["peak_vram_bytes"] < 8 * 1024**3:
        raise ValueError("Missing/excessive GPU allocator measurement")
    values, predictions, calibration_info = metrics_for(
        data["validation_target_original"], raw, task, view.adapter
    )
    diagnostics = {
        "calibration": calibration_info,
        "groups": group_diagnostics(
            data["validation_target_original"],
            predictions[:, 1] if task == "binary" else predictions[:, 0],
            data["validation_groups"],
            task,
        ),
        "groups_are_descriptive_only": True,
    }
    meta = ArtifactStore(MODELS / run).save_checkpoint("best", weights, provenance(entry, config))
    checkpoint = ref(MODELS / run / "best.npz")
    checkpoint_metadata = ref(MODELS / run / "best.json")
    loaded = ArtifactStore(MODELS / run).load_checkpoint(
        "best", provenance(entry, config), expected_manifest_sha256=checkpoint_metadata["sha256"]
    )
    cpu_output = (
        NumpyNetwork(config["plan"], loaded).forward(data["train_x"][:4])
        if method in IMPLEMENTATIONS
        else PortableBaseline(portable_meta, loaded).predict(data["train_x"][:4])
    )
    native_output = predict(data["train_x"][:4])
    np.testing.assert_allclose(cpu_output, native_output, rtol=1e-4, atol=1e-5)
    write_once(
        folder / "cpu_demo.json",
        {
            "status": "PASS",
            "input_split": "train",
            "ids": data["train_ids"][:4].tolist(),
            "canonical_x_sha256": array_sha256(data["train_x"][:4]),
            "raw_output": cpu_output.tolist(),
            "max_absolute_error": float(np.max(np.abs(cpu_output - native_output))),
            "checkpoint": checkpoint,
            "load_policy": "numpy_no_pickle",
            "frameworks_imported_for_cpu_predict": False,
        },
    )
    if portable_meta is not None:
        write_once(folder / "baseline_metadata.json", portable_meta)
    write_once(folder / "history.json", history)
    write_once(
        folder / "validation_details.json",
        {
            "metrics": values,
            "diagnostics": diagnostics,
            "memory": memory,
            "preprocessing_seconds": preprocessing_seconds,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "inference_scope": "fixed TRAIN sample; model forward and host transfer, no preprocessing or inverse target",
        },
    )
    prediction_ref = save_predictions(
        run, "validation", data["validation_ids"].tolist(), data["validation_target_original"], predictions
    )
    efficiency = {
        "train_seconds": train_seconds,
        "inference_p50_ms": timing["inference_p50_ms"],
        "inference_p95_ms": timing["inference_p95_ms"],
        "warmup_batches": 5,
        "timed_repeats": 30,
        "peak_ram_bytes": memory["process_peak_ram_bytes"],
        "peak_vram_bytes": memory["peak_vram_bytes"],
        "checkpoint_bytes": meta["size_bytes"],
    }
    finished = datetime.now(UTC).isoformat()
    record = run_record(
        entry,
        config,
        "validation",
        values,
        efficiency,
        started_at,
        finished,
        [checkpoint, checkpoint_metadata, prediction_ref],
    )
    metric_path = METRICS / "validation" / f"{run}.json"
    write_once(metric_path, record)
    selection = {
        "run_id": run,
        "status": "succeeded",
        "lifecycle": "trained_validation_selected",
        "inference_ready": True,
        "selection_split": "validation",
        "best_epoch": best_epoch,
        "checkpoint": checkpoint,
        "checkpoint_metadata": checkpoint_metadata,
        "validation_predictions": prediction_ref,
        "validation_metrics": ref(metric_path),
        "history": ref(folder / "history.json"),
        "details": ref(folder / "validation_details.json"),
        "model_contract": entry["model_contract"],
        "config": entry["config"],
        "comparison_group_sha256": entry["comparison_group_sha256"],
        "classical_metadata": ref(folder / "baseline_metadata.json") if portable_meta else None,
        "cpu_loadable": True,
        "cpu_demo": ref(folder / "cpu_demo.json"),
        "test_evaluation_executed": False,
    }
    write_once(selection_path, selection)
    return {
        "run_id": run,
        "status": "succeeded",
        "epochs": len(history),
        "best_epoch": best_epoch,
        "primary_metric": values[dataset_spec(entry["dataset_id"])["primary_metric"]]["value"],
        "train_seconds": train_seconds,
    }


def evaluate_run(run):
    release = check_sources()
    entry = next(row for row in release["runs"] if row["run_id"] == run)
    config = read_json(ROOT / entry["config"]["path"])
    dataset = entry["dataset_id"]
    gate = EvaluationGate(BASE / "test_seals" / dataset)
    gate.claim(run, release["code"]["dirty_tree_sha256"])
    manifest = read_json(gate.root / "manifest.json")
    for record in manifest["artifacts"]:
        if sha256_file(ROOT / record["path"]) != record["sha256"]:
            raise ValueError("TEST approved artifact changed")
    selection = read_json(BASE / "runs" / run / "selection.json")
    weights = ArtifactStore(MODELS / run).load_checkpoint(
        "best", provenance(entry, config), expected_manifest_sha256=selection["checkpoint_metadata"]["sha256"]
    )
    configure(entry["method"], entry["seed"])
    started = datetime.now(UTC).isoformat()
    data = test_data(dataset, gate)
    if entry["method"] in IMPLEMENTATIONS:
        trainer = make_trainer(entry["method"], config["plan"], weights)
        raw = predict_batches(trainer, data["x"])
    else:
        raw = PortableBaseline(read_json(ROOT / selection["classical_metadata"]["path"]), weights).predict(
            data["x"]
        )
    values, predictions, calibration_info = metrics_for(
        data["target_original"], raw, config["task"], data["view"].adapter
    )
    prediction_ref = save_predictions(run, "test", data["ids"], data["target_original"], predictions)
    groups = groups_for_frame(dataset, data["raw"])
    details = {
        "metrics": values,
        "calibration": calibration_info,
        "groups": group_diagnostics(
            data["target_original"],
            predictions[:, 1] if config["task"] == "binary" else predictions[:, 0],
            groups,
            config["task"],
        ),
        "diagnostic_only_no_tuning": True,
    }
    write_once(BASE / "runs" / run / "test_details.json", details)
    old = read_json(ROOT / selection["validation_metrics"]["path"])
    record = run_record(
        entry,
        config,
        "test",
        values,
        old["efficiency"],
        started,
        datetime.now(UTC).isoformat(),
        [selection["checkpoint"], prediction_ref],
        gate.state()["seal_id"],
    )
    path = METRICS / "test" / f"{run}.json"
    write_once(path, record)
    gate.record(
        run,
        {
            "status": "PASS",
            "predictions": prediction_ref,
            "metrics": ref(path),
            "details": ref(BASE / "runs" / run / "test_details.json"),
        },
    )
    return {"run_id": run, "status": "PASS", "test_prediction_count": len(data["ids"])}
