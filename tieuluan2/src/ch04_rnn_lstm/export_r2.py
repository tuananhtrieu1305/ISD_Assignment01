"""Approved strict CPU export revision; frozen training remains unchanged.

Only a failed final CPU/GPU assertion in the exact frozen train_run frame may
enter the finalizer. All optimizer states, selected weights and native validation
outputs remain unchanged. The one already-dead process has explicitly missing
original training telemetry, represented by a separate versioned run schema.
"""

import copy
import platform
import time
from datetime import UTC, datetime

import numpy as np
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from src.ch02_ml.experiment import configure, provenance
from src.ch02_ml.protocol import array_sha256
from src.ch04_rnn_lstm import experiment as frozen
from src.ch04_rnn_lstm.protocol import BASE, IMPLEMENTATIONS, METRICS, MODELS, checked, ref
from src.ch04_rnn_lstm.training import predict_windows
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.artifact_core import ArtifactStore, write_once
from src.common.contracts import _finite, _run, load_schemas, read_json, validate_document
from src.common.device_core import DeviceMonitor
from src.common.metric_core import regression_metrics
from src.common.numpy_engine import NumpyNetwork
from src.common.training_core import inference_timing

ORPHAN = "ch4_household_power_rnn_pytorch_s17_main"
REVISION = BASE / "revisions/r2/revision.json"
RECOVERY_VERSION = "phase28.recovery_run.2"
MISSING_TELEMETRY = ("train_seconds", "peak_ram_bytes", "peak_vram_bytes")
LOST_TELEMETRY_WARNING = (
    "Original training wall/RAM/VRAM telemetry lost before export failure; null, excluded from cost aggregates. "
    "Recovery process measurements are not original training measurements."
)


def check_revision():
    release = frozen.check_sources()
    revision = read_json(REVISION)
    for group in ("source_files", "preserved_selections", "preserved_orphan"):
        for record in revision[group]:
            checked(record)
    checked(revision["original_release"])
    checked(revision["authorization"])
    checked(revision["recovery_schema"])
    return release


def compare_outputs(portable, native_cpu, native_gpu):
    arrays = [np.asarray(value) for value in (portable, native_cpu, native_gpu)]
    if any(a.shape != arrays[0].shape or not np.isfinite(a).all() for a in arrays):
        raise ValueError("Nonfinite or mismatched export outputs")

    def comparison(value):
        return {
            "status": "PASS" if np.isclose(arrays[0], value, rtol=1e-4, atol=1e-5).all() else "FAIL",
            "max_absolute_error": float(np.max(np.abs(arrays[0] - value))),
            "output": value.tolist(),
        }

    result = {"rtol": 1e-4, "atol": 1e-5,
              "cpu_reference": comparison(arrays[1]),
              "original_gpu_cpu_gate": comparison(arrays[2])}
    if result["cpu_reference"]["status"] != "PASS":
        raise AssertionError("Strict native CPU/portable CPU export parity failed")
    return result


def native_cpu(plan, weights, method, x):
    if method == "pytorch":
        from src.common.backend_models import TorchBackend

        return TorchBackend(plan, weights, "cpu").predict(x)
    if method == "keras":
        from src.common.backend_models import KerasBackend

        model = KerasBackend(plan, weights, "cpu")
        result = model.predict(x)
        model.keras.backend.clear_session()
        return result
    if method == "scratch":
        return NumpyNetwork(plan, weights).forward(x)
    raise ValueError("No native CPU reference for this implementation")


def completed_progress(progress, budget, weights):
    if not progress or not progress["history"]:
        raise ValueError("Completed immutable training state required")
    history, stop = progress["history"], progress["early_stopping"]
    if len(history) > budget["max_epochs"] or not (
        len(history) == budget["max_epochs"] or stop["bad_epochs"] >= budget["patience"]
    ):
        raise ValueError("Training not finished; finalization cannot add updates")
    if [row["epoch"] for row in history] != list(range(len(history))):
        raise ValueError("Training history is not contiguous")
    if set(weights) != set(progress["best_weights"]) or any(
        not np.array_equal(weights[k], progress["best_weights"][k]) for k in weights
    ):
        raise ValueError("Export checkpoint differs from the completed best state")
    if not 0 <= stop["best_epoch"] < len(history):
        raise ValueError("Invalid selected epoch")
    return stop["best_epoch"]


def recovery_schema():
    schema = copy.deepcopy(load_schemas()["run"])
    schema["$id"] = "urn:ai-paper:phase28:recovery-run:2"
    schema["title"] = "Phase28 single dead-process recovery; unavailable training telemetry"
    schema["properties"]["schema_version"] = {"const": RECOVERY_VERSION}
    schema["properties"]["run_id"] = {"const": ORPHAN}
    schema["properties"]["split"] = {"const": "validation"}
    schema["properties"]["device"] = {"const": "cuda:0"}
    schema["properties"]["implementation"] = {"const": "pytorch"}
    schema["properties"]["warnings"]["contains"] = {"const": LOST_TELEMETRY_WARNING}
    for key in MISSING_TELEMETRY:
        schema["properties"]["efficiency"]["properties"][key] = {"type": "null"}
    return schema


def validate_run(document):
    if document["schema_version"] != RECOVERY_VERSION:
        return validate_document("run", document, publish=True)
    schemas = load_schemas()
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    )
    _finite(document)
    errors = list(Draft202012Validator(
        recovery_schema(), registry=registry, format_checker=FormatChecker()
    ).iter_errors(document))
    if errors:
        raise ValueError("Recovery run schema: " + errors[0].message)
    _run(document)


def export_failure_context(failure):
    """Accept only the final assertion of the pinned original function, not BPTT/parity bugs."""
    trace = failure.__traceback__
    while trace:
        if trace.tb_frame.f_code is frozen.train_run.__code__:
            context = trace.tb_frame.f_locals
            required = {"checkpoint", "metadata", "loaded", "cpu", "native_demo", "memory", "timing",
                        "output", "targets", "values", "history", "train_seconds", "best_epoch"}
            if required.issubset(context) and context.get("method") in IMPLEMENTATIONS:
                return context.copy()
        trace = trace.tb_next
    return None


def finalize(context, *, lost_telemetry=False):
    c = context
    entry, config, data = c["entry"], c["config"], c["data"]
    run, method = entry["run_id"], entry["method"]
    folder = BASE / "runs" / run
    if (folder / "selection.json").exists():
        raise ValueError("Never overwrite an existing completed selection")
    checked(c["checkpoint"])
    checked(c["metadata"])
    progress = frozen.load_progress(run, entry["config"]["sha256"])
    best_epoch = completed_progress(progress, config["training"], c["weights"])
    if c["history"] != progress["history"] or c["best_epoch"] != best_epoch:
        raise ValueError("Finalizer cannot reselect a checkpoint or rewrite training history")
    x, _ = data.batch(data.train_ids[:4])
    loaded = ArtifactStore(MODELS / run).load_checkpoint(
        "best", provenance(entry, config), expected_manifest_sha256=c["metadata"]["sha256"]
    )
    if any(not np.array_equal(loaded[k], c["weights"][k]) for k in loaded):
        raise ValueError("Checkpoint loading differs from selected weights")
    cpu = NumpyNetwork(config["plan"], loaded).forward(x)
    comparisons = compare_outputs(cpu, native_cpu(config["plan"], loaded, method, x), c["native_demo"])
    demo = {
        "status": "PASS", "input_split": "train", "ids": data.train_ids[:4],
        "canonical_x_sha256": array_sha256(x), "raw_output": cpu.tolist(),
        "max_absolute_error": comparisons["cpu_reference"]["max_absolute_error"],
        "checkpoint": c["checkpoint"], "serving_backend": "numpy_cpu_portable",
        "training_implementation": method, "reference_policy": "r2_native_cpu",
        "comparisons": comparisons, "revision": ref(REVISION),
    }
    write_once(folder / "cpu_demo.json", demo)
    write_once(folder / "history.json", c["history"])
    note = {
        "revision": ref(REVISION), "weights_updated_during_finalization": False,
        "original_gpu_cpu_gate": comparisons["original_gpu_cpu_gate"],
        "original_training_telemetry_available": not lost_telemetry,
        "validation_predictions": "recomputed from same frozen best checkpoint after process loss"
        if lost_telemetry else "retained exact native GPU outputs from original failed frame",
        "train_snapshot_elapsed_seconds": progress["elapsed_seconds"],
        "elapsed_scope": "Last epoch snapshot, not full train wall; never used as replacement training timer",
        "recovery_process_memory": c["memory"] if lost_telemetry else None,
        "recovery_started_at": c["started"] if lost_telemetry else None,
        "test_executed": False,
    }
    write_once(folder / "export_recovery_r2.json", note)
    details = {
        "metrics": c["values"], "memory": None if lost_telemetry else c["memory"],
        "best_epoch": best_epoch, "preprocessing_seconds": None if lost_telemetry else c["prep_seconds"],
        "train_count": len(data.train_ids), "validation_count": len(data.validation_ids),
        "unit": config["unit"], "fold": entry["fold"], "platform": platform.platform(),
        "numpy": np.__version__, "test_evaluation_executed": False,
        "export_recovery": ref(folder / "export_recovery_r2.json"),
    }
    write_once(folder / "validation_details.json", details)
    predictions = frozen.save_predictions(run, data, c["targets"], c["output"])
    memory, timing = c["memory"], c["timing"]
    efficiency = {
        "train_seconds": c["train_seconds"], "inference_p50_ms": timing["inference_p50_ms"],
        "inference_p95_ms": timing["inference_p95_ms"], "warmup_batches": timing["warmup"],
        "timed_repeats": timing["repeats"], "peak_ram_bytes": memory["process_peak_ram_bytes"],
        "peak_vram_bytes": memory["peak_vram_bytes"], "checkpoint_bytes": checked(c["checkpoint"]).stat().st_size,
    }
    # For the orphan, these initial numbers measure recovery, never original training.
    # Only the final null-valued recovery schema document is published.
    document = frozen.record(entry, config, data, c["values"], efficiency, c["started"],
                             [c["checkpoint"], c["metadata"], predictions, ref(folder / "export_recovery_r2.json")])
    if lost_telemetry:
        if run != ORPHAN:
            raise ValueError("Nullable telemetry exception applies only to the declared dead process")
        document["schema_version"] = RECOVERY_VERSION
        for key in MISSING_TELEMETRY:
            document["efficiency"][key] = None
        document["warnings"] += [LOST_TELEMETRY_WARNING,
                                 "started_at identifies recovery, not the lost original process start"]
    document["warnings"].append("r2 strict native CPU export; original GPU/CPU result retained separately")
    validate_run(document)
    metric_path = METRICS / "validation" / f"{run}.json"
    write_once(metric_path, document)
    write_once(folder / "selection.json", {
        "run_id": run, "status": "succeeded", "lifecycle": "trained_validation_selected",
        "selection_split": "validation", "inference_ready": True, "best_epoch": best_epoch,
        "checkpoint": c["checkpoint"], "checkpoint_metadata": c["metadata"],
        "validation_metrics": ref(metric_path), "validation_predictions": predictions,
        "history": ref(folder / "history.json"), "details": ref(folder / "validation_details.json"),
        "cpu_demo": ref(folder / "cpu_demo.json"), "config": entry["config"],
        "model_contract": entry["model_contract"], "comparison_group_sha256": entry["comparison_group_sha256"],
        "export_revision": ref(REVISION), "export_recovery": ref(folder / "export_recovery_r2.json"),
        "test_evaluation_executed": False,
    })
    return {"run_id": run, "status": "PASS", "recovery": "r2", "epochs": len(c["history"]),
            "original_gpu_cpu_gate": comparisons["original_gpu_cpu_gate"]["status"],
            "original_training_telemetry_available": not lost_telemetry}


def recover_orphan(entry):
    run = entry["run_id"]
    if run != ORPHAN:
        raise ValueError("Unexpected orphan checkpoint: inspect before recovery")
    config = read_json(checked(entry["config"]))
    progress = frozen.load_progress(run, entry["config"]["sha256"])
    metadata, checkpoint = ref(MODELS / run / "best.json"), ref(MODELS / run / "best.npz")
    weights = ArtifactStore(MODELS / run).load_checkpoint(
        "best", provenance(entry, config), expected_manifest_sha256=metadata["sha256"]
    )
    best_epoch = completed_progress(progress, config["training"], weights)
    started = datetime.now(UTC).isoformat()
    configure(entry["method"], entry["seed"])
    data = WindowData(entry["dataset_id"], entry["fold"])
    if data.contract() != read_json(checked(config["data_contract"])):
        raise ValueError("Recovery data contract changed")
    monitor = DeviceMonitor("torch", "gpu")
    monitor.start()
    tick = time.perf_counter()
    trainer = frozen.make_trainer(entry["method"], config["plan"], weights)
    x, _ = data.batch(data.train_ids[:4])
    native_demo = trainer.predict(x)
    output = data.adapter.inverse_target(predict_windows(trainer, data, data.validation_ids))
    timing = inference_timing(lambda: trainer.predict(x[:1]), monitor.synchronize)
    memory = monitor.finish()
    targets = data.targets(data.validation_ids)
    values = regression_metrics(targets, output, data.horizons, data.series(data.validation_ids))
    return finalize({"entry": entry, "config": config, "data": data, "weights": weights,
                     "history": progress["history"], "best_epoch": best_epoch,
                     "train_seconds": time.perf_counter() - tick, "memory": memory,
                     "timing": timing, "prep_seconds": None, "output": output,
                     "targets": targets, "values": values, "native_demo": native_demo,
                     "checkpoint": checkpoint, "metadata": metadata, "started": started},
                    lost_telemetry=True)


def run_revision(run):
    entry = next(e for e in check_revision()["runs"] if e["run_id"] == run)
    if (BASE / "runs" / run / "selection.json").exists():
        return frozen.train_run(run)
    if (MODELS / run / "best.npz").exists():
        return recover_orphan(entry)
    try:
        return frozen.train_run(run)
    except AssertionError as failure:
        context = export_failure_context(failure)
        if context is None:
            raise
        import traceback

        write_once(BASE / "attempts" / f"r2_{run}_gpu_cpu_failure.json", {
            "run_id": run, "traceback": traceback.format_exc(), "test_executed": False,
            "stage": "original_frozen_gpu_cpu_export_gate", "revision": ref(REVISION),
        })
        return finalize(context)
