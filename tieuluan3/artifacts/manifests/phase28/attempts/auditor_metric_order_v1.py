"""Audit validation artifacts only; never train or execute a TEST forward."""

import argparse
import gzip
import json
from functools import lru_cache

import numpy as np

from scripts.phase28_preflight import dependencies
from src.ch02_ml.experiment import provenance
from src.ch02_ml.protocol import array_sha256
from src.ch02_ml.test_gate import atomic_json
from src.ch04_rnn_lstm.experiment import metric_rows
from src.ch04_rnn_lstm.export_r2 import (
    MISSING_TELEMETRY,
    ORPHAN,
    RECOVERY_VERSION,
    REVISION,
    check_revision,
    validate_run,
)
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
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.artifact_core import ArtifactStore
from src.common.contracts import ROOT, canonical_sha256, read_json, validate_document
from src.common.metric_core import regression_metrics
from src.common.model_core import canonical_weights, render_functions
from src.common.numpy_engine import NumpyNetwork
from src.common.training_core import batch_order


def audit_prediction_rows(data, rows, metrics):
    ids = data.validation_ids
    if len(rows) != len(ids) or [row["id"] for row in rows] != ids:
        raise ValueError("Validation prediction IDs/order/count changed")
    target = np.asarray([row["target"] for row in rows], dtype="float64")
    prediction = np.asarray([row["prediction"] for row in rows], dtype="float64")
    if not np.array_equal(target, data.targets(ids)):
        raise ValueError("Original validation labels changed")
    if any(
        row["series"] != data.rows[key]["series"] or row["target_times"] != data.rows[key]["target_times"]
        for key, row in zip(ids, rows, strict=True)
    ):
        raise ValueError("Prediction series/target calendar changed")
    actual = regression_metrics(target, prediction, data.horizons, data.series(ids))
    if canonical_sha256(actual) != canonical_sha256(metrics):
        raise ValueError("Saved validation metric does not match saved predictions")
    return len(rows)


@lru_cache(maxsize=2048)
def order_hash(size, seed, epoch):
    return canonical_sha256(batch_order(size, 32, seed, epoch))


def verify():
    release = check_revision()
    if len(release["runs"]) != 132 or sum(e["method"] in IMPLEMENTATIONS for e in release["runs"]) != 108:
        raise ValueError("Incomplete RNN/baseline declaration")
    active = read_json(BASE / "active_controller.json")
    if active.get("pid") is not None or active.get("status") != "finished":
        raise ValueError("Wait until the single validation controller finishes")
    if (BASE / "test_seals").exists() or (METRICS / "test").exists() or (PREDICTIONS / "test").exists():
        raise ValueError("Phase28 must not contain TEST evaluation artifacts")
    data_cache, rows_audited, neural, baseline, artifacts = {}, 0, 0, 0, {}
    cpu_receipts, original_export_failures, missing_telemetry = 0, [], []
    for entry in release["runs"]:
        run = entry["run_id"]
        folder = BASE / "runs" / run
        selected = read_json(folder / "selection.json")
        if (
            selected["selection_split"] != "validation"
            or selected["test_evaluation_executed"]
            or selected["status"] != "succeeded"
            or not selected["inference_ready"]
        ):
            raise ValueError("Invalid validation selection")
        for value in selected.values():
            if isinstance(value, dict) and set(value) == {"path", "sha256"}:
                checked(value)
                artifacts[value["path"]] = value
        config = read_json(checked(entry["config"]))
        key = (entry["dataset_id"], entry["fold"])
        if key not in data_cache:
            data_cache[key] = WindowData(*key)
        data = data_cache[key]
        if (
            data.contract() != read_json(checked(config["data_contract"]))
            or selected["config"] != entry["config"]
            or selected["model_contract"] != entry["model_contract"]
        ):
            raise ValueError("Run/data/config contract changed")
        details = read_json(checked(selected["details"]))
        with gzip.open(checked(selected["validation_predictions"]), "rt", encoding="utf-8") as packed:
            rows = [json.loads(line) for line in packed]
        rows_audited += audit_prediction_rows(data, rows, details["metrics"])
        metric = read_json(checked(selected["validation_metrics"]))
        if (
            metric["metrics"] != metric_rows(details["metrics"], config["unit"])
            or metric["config_sha256"] != entry["config"]["sha256"]
            or metric["split"] != "validation"
        ):
            raise ValueError("Run metric/schema mismatch")
        weights = ArtifactStore(MODELS / run).load_checkpoint(
            "best",
            provenance(entry, config),
            expected_manifest_sha256=selected["checkpoint_metadata"]["sha256"],
        )
        demo = read_json(checked(selected["cpu_demo"]))
        x, _ = data.batch(data.train_ids[:4])
        if (
            demo["status"] != "PASS"
            or demo["ids"] != data.train_ids[:4]
            or demo["canonical_x_sha256"] != array_sha256(x)
        ):
            raise ValueError("CPU TRAIN-only demo not verified")
        history = read_json(checked(selected["history"]))
        if entry["method"] in IMPLEMENTATIONS:
            neural += 1
            validate_run(metric)
            if metric["schema_version"] == RECOVERY_VERSION:
                if run != ORPHAN or any(metric["efficiency"][key] is not None for key in MISSING_TELEMETRY):
                    raise ValueError("Undeclared missing training telemetry")
                note = read_json(checked(selected["export_recovery"]))
                if note["original_training_telemetry_available"] or note["weights_updated_during_finalization"]:
                    raise ValueError("Invalid dead-process recovery evidence")
                if details["memory"] is not None:
                    raise ValueError("Recovery RAM/VRAM cannot be claimed as original train peak")
                missing_telemetry.append(run)
            contract = read_json(checked(entry["model_contract"]))
            validate_document("model", contract, publish=True)
            functions = render_functions(contract)
            if read_json(folder / "functions.json") != {
                k: v for k, v in functions.items() if k != "markdown"
            }:
                raise ValueError("Function composition changed")
            initial = canonical_weights(config["plan"], entry["seed"])
            if (
                canonical_sha256({k: v.tolist() for k, v in initial.items()})
                != config["canonical_initial_weights_sha256"]
            ):
                raise ValueError("Initial canonical weights changed")
            if (
                not history
                or len(history) > 40
                or selected["best_epoch"] != int(np.argmin([h["validation_loss"] for h in history]))
            ):
                raise ValueError("Invalid best checkpoint selection")
            if all(np.array_equal(weights[k], initial[k]) for k in weights):
                raise ValueError("Checkpoint is still initialized, not trained")
            for epoch, record in enumerate(history):
                if record["epoch"] != epoch or record["batch_order_sha256"] != order_hash(
                    len(data.train_ids), entry["seed"], epoch
                ):
                    raise ValueError("Common batch schedule mismatch")
                if not 0 <= record["gradient_clip_fraction"] <= 1 or not np.isfinite(
                    record["gradient_norm_max"]
                ):
                    raise ValueError("Invalid gradient diagnostic")
            parity = read_json(folder / "initial_parity.json")
            if parity["forward"] != "PASS" or parity["gradient"]["max_relative_l2_error"] > 1e-3:
                raise ValueError("Initial gradient/forward parity missing")
            if (
                entry["method"] in {"keras", "pytorch"}
                and metric["schema_version"] != RECOVERY_VERSION
                and not 0 < metric["efficiency"]["peak_vram_bytes"] < 8 * 1024**3
            ):
                raise ValueError("Native GPU allocator evidence missing")
            gradient = read_json(folder / "gradient_diagnostics.json")
            if gradient["input_split"] != "train" or gradient["ids"] != data.train_ids[:4]:
                raise ValueError("Gradient diagnostic must use fixed TRAIN")
            output = NumpyNetwork(config["plan"], weights).forward(x)
            receipt_path = REVISION.parent / "cpu_receipts" / f"{run}.json"
            receipt = read_json(receipt_path)
            for name in ("revision", "selection", "checkpoint", "checkpoint_metadata"):
                checked(receipt[name])
            if (receipt["status"] != "PASS" or receipt["run_id"] != run
                or receipt["checkpoint"] != selected["checkpoint"]
                or receipt["checkpoint_metadata"] != selected["checkpoint_metadata"]
                or receipt["selection"] != ref(folder / "selection.json")
                or receipt["revision"] != ref(REVISION)
                or receipt["input_split"] != "train" or receipt["ids"] != data.train_ids[:4]
                or receipt["canonical_x_sha256"] != array_sha256(x)
                or receipt["native_cpu_device"] != "cpu" or receipt["weights_updated"]
                or receipt["validation_executed"] or receipt["test_executed"]):
                raise ValueError("Invalid strict native CPU receipt")
            comparison = receipt["comparisons"]
            if comparison["rtol"] != 1e-4 or comparison["atol"] != 1e-5 or comparison["cpu_reference"]["status"] != "PASS":
                raise ValueError("CPU export tolerance/reference changed")
            np.testing.assert_allclose(output, receipt["portable_cpu_output"], rtol=1e-5, atol=1e-6)
            np.testing.assert_allclose(receipt["portable_cpu_output"], comparison["cpu_reference"]["output"], rtol=1e-4, atol=1e-5)
            if comparison["original_gpu_cpu_gate"]["status"] == "FAIL":
                original_export_failures.append(run)
                if demo.get("comparisons", {}).get("original_gpu_cpu_gate") != comparison["original_gpu_cpu_gate"]:
                    raise ValueError("Original GPU/CPU failure was not preserved")
            cpu_receipts += 1
            artifacts[receipt_path.relative_to(ROOT).as_posix()] = ref(receipt_path)
        else:
            baseline += 1
            if history or selected["best_epoch"] is not None:
                raise ValueError("Causal baseline should not claim learned epochs")
            if set(weights) != {"baseline_kind"} or weights["baseline_kind"].tolist() != [
                int(entry["method"] == "seasonal_naive")
            ]:
                raise ValueError("Baseline checkpoint method marker changed")
            output = data.baseline(data.train_ids[:4], entry["method"])
        np.testing.assert_allclose(output, demo["raw_output"], rtol=1e-5, atol=1e-6)
        artifacts[(folder / "selection.json").relative_to(ROOT).as_posix()] = ref(folder / "selection.json")
    if cpu_receipts != 108 or neural != 108 or baseline != 24 or missing_telemetry != [ORPHAN]:
        raise ValueError("Incomplete strict CPU export matrix or missing declared telemetry exception")
    if ORPHAN not in original_export_failures:
        raise ValueError("Original orphan GPU/CPU FAIL must remain visible")
    protected = dependencies()
    result = {
        "phase": 28,
        "status": "PASS",
        "neural_runs": neural,
        "baseline_runs": baseline,
        "main_neural_runs": 27,
        "rolling_neural_runs": 81,
        "validation_rows_audited": rows_audited,
        "artifact_refs": len(artifacts),
        "data_views": len(data_cache),
        "cpu_reference_revision": ref(REVISION),
        "strict_native_cpu_receipts": cpu_receipts,
        "original_gpu_cpu_failures_preserved": original_export_failures,
        "original_training_telemetry_unavailable": missing_telemetry,
        "code_sha256": release["code"]["dirty_tree_sha256"],
        "protected_locks": protected,
        "auditor": ref(ROOT / "scripts/verify_phase28.py"),
        "test_evaluation_executed": False,
        "test_forward_executed": False,
        "validation_forward_executed_by_auditor": False,
    }
    atomic_json(BASE / "verification.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.status:
        release = check_sources()
        print(
            json.dumps(
                {
                    "completed": sum(
                        (BASE / "runs" / e["run_id"] / "selection.json").exists() for e in release["runs"]
                    ),
                    "expected": 132,
                    "test_executed": False,
                }
            )
        )
    else:
        print(json.dumps(verify(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
