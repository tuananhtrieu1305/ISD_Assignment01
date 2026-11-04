"""Audit LSTM saved validation predictions/history; never a validation/TEST forward.

Only a fixed TRAIN CPU forward is used to check checkpoint round-trip receipts.
"""

import argparse
import gzip
import json
import math

import numpy as np

from scripts.phase29_preflight import dependencies
from scripts.verify_phase28 import audit_metric_rows, audit_prediction_rows
from src.ch02_ml.experiment import provenance
from src.ch02_ml.protocol import array_sha256
from src.ch04_rnn_lstm.phase29.experiment import load_progress, metric_rows
from src.ch04_rnn_lstm.phase29.protocol import BASE, MODELS, check_sources, checked, ref
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.artifact_core import ArtifactStore, write_once
from src.common.contracts import canonical_sha256, read_json, validate_document
from src.common.model_core import canonical_weights, render_functions
from src.common.numpy_engine import NumpyNetwork
from src.common.training_core import EarlyStopping, batch_order


def audit_history(history, best_epoch, seed, train_count, budget):
    if not history or len(history) > budget["max_epochs"]:
        raise ValueError("Invalid/over-budget history")
    stop = EarlyStopping(budget["patience"], budget["min_delta"])
    terminate = False
    for epoch, row in enumerate(history):
        if (
            row["epoch"] != epoch
            or not np.isfinite(
                [
                    row["validation_loss"],
                    row["train_loss"],
                    row["gradient_norm_max"],
                    row["gradient_norm_mean"],
                ]
            ).all()
            or not 0 <= row["gradient_clip_fraction"] <= 1
            or row["batch_order_sha256"]
            != canonical_sha256(batch_order(train_count, budget["batch_size"], seed, epoch))
        ):
            raise ValueError("History loss/gradient/common schedule mismatch")
        _, terminate = stop.observe(row["validation_loss"], epoch)
        if terminate and epoch != len(history) - 1:
            raise ValueError("Updates continued after early stopping")
    if best_epoch != stop.best_epoch or best_epoch != int(np.argmin([h["validation_loss"] for h in history])):
        raise ValueError("Selected epoch is not the true minimum")
    if not terminate and len(history) != budget["max_epochs"]:
        raise ValueError("Selection made before declared stopping budget")
    return {
        "epochs": len(history),
        "optimizer_steps": math.ceil(train_count / budget["batch_size"]) * len(history),
    }


def verify():
    release = check_sources()
    active = read_json(BASE / "active_controller.json")
    if len(release["runs"]) != 108 or active.get("pid") is not None or active.get("status") != "finished":
        raise ValueError("Wait for complete108-run training controller to exit")
    protected = dependencies()
    cache, predictions, receipts, registry = {}, 0, 0, []
    for entry in release["runs"]:
        run = entry["run_id"]
        folder = BASE / "runs" / run
        selected_ref = ref(folder / "selection.json")
        selected = read_json(checked(selected_ref))
        if (
            selected["status"] != "succeeded"
            or selected["selection_split"] != "validation"
            or selected["test_evaluation_executed"]
            or not selected["inference_ready"]
            or selected["config"] != entry["config"]
            or selected["model_contract"] != entry["model_contract"]
        ):
            raise ValueError("Invalid LSTM validation selection")
        for value in selected.values():
            if isinstance(value, dict) and set(value) == {"path", "sha256"}:
                checked(value)
        config = read_json(checked(entry["config"]))
        key = (entry["dataset_id"], entry["fold"])
        if key not in cache:
            cache[key] = WindowData(*key)
        data = cache[key]
        if data.contract() != read_json(checked(config["data_contract"])):
            raise ValueError("Frozen LSTM data contract changed")
        details = read_json(checked(selected["details"]))
        with gzip.open(checked(selected["validation_predictions"]), "rt", encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream]
        predictions += audit_prediction_rows(data, rows, details["metrics"])
        metric = read_json(checked(selected["validation_metrics"]))
        validate_document("run", metric, publish=True)
        audit_metric_rows(metric["metrics"], metric_rows(details["metrics"], config["unit"]))
        if metric["family"] != "lstm" or metric["run_id"] != run or metric["split"] != "validation":
            raise ValueError("Model metric identity mismatch")
        contract = read_json(checked(entry["model_contract"]))
        validate_document("model", contract, publish=True)
        rendered = render_functions(contract)
        if read_json(folder / "functions.json") != {k: v for k, v in rendered.items() if k != "markdown"}:
            raise ValueError("LSTM function composition changed")
        weights = ArtifactStore(MODELS / run).load_checkpoint(
            "best",
            provenance(entry, config),
            expected_manifest_sha256=selected["checkpoint_metadata"]["sha256"],
        )
        initial = canonical_weights(config["plan"], entry["seed"])
        if all(np.array_equal(weights[k], initial[k]) for k in weights):
            raise ValueError("Initialized weights cannot be called trained")
        history = read_json(checked(selected["history"]))
        state = audit_history(
            history, selected["best_epoch"], entry["seed"], len(data.train_ids), config["training"]
        )
        progress = load_progress(run, entry["config"]["sha256"])
        if (
            progress["history"] != history
            or progress["trainer"]["iterations"] != state["optimizer_steps"]
            or any(not np.array_equal(weights[k], progress["best_weights"][k]) for k in weights)
        ):
            raise ValueError("Saved optimizer/best/history identity changed")
        parity = read_json(folder / "initial_parity.json")
        if parity["forward"] != "PASS" or parity["gradient"]["max_relative_l2_error"] > 1e-3:
            raise ValueError("Initial gradient parity missing")
        if entry["method"] != "scratch" and not 0 < metric["efficiency"]["peak_vram_bytes"] < 8 * 1024**3:
            raise ValueError("GPU allocator evidence missing")
        diagnostic = read_json(folder / "gradient_diagnostics.json")
        if (
            diagnostic["input_split"] != "train"
            or diagnostic["ids"] != data.train_ids[:4]
            or len(diagnostic["layers"]) != 3
        ):
            raise ValueError("LSTM gate diagnostics must use fixed TRAIN windows")
        x, _ = data.batch(data.train_ids[:4])
        output = NumpyNetwork(config["plan"], weights).forward(x)
        receipt = read_json(BASE / "cpu_receipts" / (run + ".json"))
        for name in ("selection", "checkpoint", "checkpoint_metadata", "config", "writer_source"):
            checked(receipt[name])
        if (
            receipt["selection"] != selected_ref
            or receipt["checkpoint"] != selected["checkpoint"]
            or receipt["status"] != "PASS"
            or receipt["input_split"] != "train"
            or receipt["ids"] != data.train_ids[:4]
            or receipt["canonical_x_sha256"] != array_sha256(x)
            or receipt["cuda_visible_devices"] != "-1"
            or receipt["native_cpu_device"] != "cpu"
            or receipt["optimizer_updates"] != 0
            or receipt["test_executed"]
        ):
            raise ValueError("Invalid independent strict CPU receipt")
        comparison = receipt["comparisons"]
        if (
            comparison["rtol"] != 1e-4
            or comparison["atol"] != 1e-5
            or comparison["cpu_reference"]["status"] != "PASS"
        ):
            raise ValueError("CPU parity threshold changed")
        np.testing.assert_allclose(output, receipt["portable_cpu_output"], rtol=1e-4, atol=1e-5)
        np.testing.assert_allclose(output, comparison["cpu_reference"]["output"], rtol=1e-4, atol=1e-5)
        receipts += 1
        registry.append(
            {
                **entry,
                "family": "lstm",
                "lifecycle": "trained_validation_selected",
                "inference_ready": True,
                "selection": selected_ref,
                "checkpoint": selected["checkpoint"],
                "checkpoint_metadata": selected["checkpoint_metadata"],
                "deployment_eligible": entry["fold"] is None,
                "test_evaluation_executed": False,
            }
        )
    write_once(
        BASE / "trained_validation_registry.json",
        {"phase": 29, "models": registry, "initialized_registry_replaced": False},
    )
    from scripts.phase29_joint_test import evaluator_code

    result = {
        "status": "PASS",
        "phase": 29,
        "evaluator_sha256": evaluator_code(),
        "runs": len(registry),
        "validation_prediction_rows": predictions,
        "native_cpu_receipts": receipts,
        "data_views": len(cache),
        "protected_locks": protected,
        "test_forward_executed": False,
        "validation_forward_executed": False,
        "checkpoint_forward_scope": "first four TRAIN IDs only",
    }
    write_once(BASE / "validation_verification.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
