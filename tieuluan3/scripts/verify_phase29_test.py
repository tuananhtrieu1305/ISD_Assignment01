"""Audit saved joint TEST outputs only; never construct a model or rerun TEST."""

import argparse
import gzip
import json

import numpy as np

from scripts.phase29_joint_test import evaluator_code, validate_gate
from scripts.verify_phase28 import audit_metric_rows
from src.ch04_rnn_lstm.export_r2 import validate_run
from src.ch04_rnn_lstm.phase29.experiment import metric_rows
from src.ch04_rnn_lstm.phase29.holdout_cache import CachedHoldout
from src.ch04_rnn_lstm.phase29.joint_evaluation import pending
from src.ch04_rnn_lstm.phase29.joint_gate import JointGate
from src.ch04_rnn_lstm.phase29.protocol import BASE, DATASETS, IMPLEMENTATIONS, checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import canonical_sha256, read_json
from src.common.metric_core import regression_metrics

EXPECTED = dict(zip(DATASETS, (116, 568, 4911), strict=True))


def audit_saved_rows(cache, rows, metrics):
    if len(rows) != len(cache.ids) or [r["id"] for r in rows] != cache.ids:
        raise ValueError("Saved TEST IDs/order/count mismatch")
    target = np.asarray([r["target"] for r in rows], "float64")
    prediction = np.asarray([r["prediction"] for r in rows], "float64")
    if not np.array_equal(target, cache.targets(cache.ids)):
        raise ValueError("Saved TEST original labels mismatch")
    if any(
        r["series"] != cache.rows[k]["series"] or r["target_times"] != cache.rows[k]["target_times"]
        for k, r in zip(cache.ids, rows, strict=True)
    ):
        raise ValueError("Saved TEST series/calendar mismatch")
    actual = regression_metrics(target, prediction, cache.horizons, cache.series(cache.ids))
    if canonical_sha256(actual) != canonical_sha256(metrics):
        raise ValueError("Saved TEST metrics differ from recomputed predictions")
    return len(rows)


def verify():
    code = evaluator_code()
    count, evidence, runs, dataset_rows = 0, [], 0, {}
    for dataset in DATASETS:
        gate = JointGate(BASE / "test_seals" / dataset)
        state, manifest = validate_gate(gate, code)
        if state["state"] != "evaluated" or state["evaluation_count"] != 1 or pending(gate, code):
            raise ValueError("Joint TEST is not terminal/evaluated once")
        if len(manifest["members"]) != 20:
            raise ValueError("Joint TEST membership incomplete")
        for name in ("evaluation.started", "inputs.materialized"):
            if not (gate.root / name).is_file():
                raise ValueError("Missing consumed TEST token")
        receipt_path = gate.root / "cache_receipt.json"
        receipt = read_json(receipt_path)
        cache = CachedHoldout(receipt["metadata"], state["manifest_sha256"])
        if len(cache.ids) != EXPECTED[dataset] or receipt["test_count"] != len(cache.ids):
            raise ValueError("Frozen TEST count mismatch")
        evidence += [ref(gate.root / name) for name in ("manifest.json", "seal.json", "cache_receipt.json")]
        evidence += [receipt["metadata"], cache.metadata["arrays"]]
        dataset_rows[dataset] = 0
        for member in manifest["members"]:
            run = member["run_id"]
            result_path = gate.root / (run + ".result.json")
            result = read_json(result_path)
            selected = read_json(checked(member["selection"]))
            details = read_json(checked(result["details"]))
            metric = read_json(checked(result["metrics"]))
            original = read_json(checked(selected["validation_metrics"]))
            config = read_json(checked(member["config"]))
            if (
                result["run_id"] != run
                or result["checkpoint"] != selected["checkpoint"]
                or details["checkpoint"] != selected["checkpoint"]
                or details["training_selection"] != member["selection"]
                or details["evaluator_sha256"] != code
                or details["test_seal_manifest_sha256"] != state["manifest_sha256"]
                or details["test_count"] != len(cache.ids)
                or details["test_forward_passes_per_window"] != 1
                or details["optimizer_updates"] != 0
                or result["optimizer_updates"] != 0
                or metric["run_id"] != run
                or metric["dataset_id"] != dataset
                or metric["family"] != member["family"]
                or metric["implementation"]
                != (member["method"] if member["method"] in IMPLEMENTATIONS else "numpy")
                or metric["seed"] != member["seed"]
                or metric["split"] != "test"
                or metric["test_seal_id"] != manifest["seal_id"]
                or metric["config_sha256"] != member["config"]["sha256"]
                or metric["evidence_kind"] != "measured"
            ):
                raise ValueError("TEST provenance/checkpoint/inference-only identity mismatch: " + run)
            if canonical_sha256(metric["efficiency"]) != canonical_sha256(
                original["efficiency"]
            ) or canonical_sha256(details["training_efficiency"]) != canonical_sha256(original["efficiency"]):
                raise ValueError("Training cost/null telemetry was changed or invented")
            if member["method"] in IMPLEMENTATIONS:
                validate_run(metric)
            elif metric["schema_version"] != "phase29.causal_baseline_test_run.1":
                raise ValueError("Wrong baseline schema")
            with gzip.open(checked(result["predictions"]), "rt", encoding="utf-8") as stream:
                rows = [json.loads(line) for line in stream]
            n = audit_saved_rows(cache, rows, details["metrics"])
            audit_metric_rows(metric["metrics"], metric_rows(details["metrics"], config["unit"]))
            count += n
            dataset_rows[dataset] += n
            runs += 1
            evidence += [ref(result_path), result["metrics"], result["predictions"], result["details"]]
    if count != 111900 or runs != 60:
        raise ValueError("Joint TEST total must be60 main runs/111900 saved prediction rows")
    result = {
        "phase": 29,
        "status": "PASS",
        "evaluator_sha256": code,
        "runs": runs,
        "test_prediction_rows": count,
        "dataset_rows": dataset_rows,
        "test_batches": 3,
        "evaluation_count_per_dataset": 1,
        "new_test_forward_executed": False,
        "optimizer_updates": 0,
        "evidence": evidence,
    }
    path = BASE / "test_verification.json"
    if path.exists():
        if canonical_sha256(read_json(path)) != canonical_sha256(result):
            raise ValueError("Saved TEST audit changed; versioned audit revision required")
    else:
        write_once(path, result)
    return {k: v for k, v in result.items() if k != "evidence"}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(verify(), indent=2))
