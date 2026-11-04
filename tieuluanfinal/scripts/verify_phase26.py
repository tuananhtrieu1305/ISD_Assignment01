"""Audit saved evidence. Never execute a model on TEST or refit preprocessing."""

from __future__ import annotations

import argparse
import gzip
import json
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

import numpy as np

from scripts.verify_phase25 import verify as verify_core
from src.ch02_ml.diagnostics import calibration
from src.ch02_ml.experiment import metric_rows, provenance
from src.ch02_ml.protocol import (
    BASE,
    CACHE,
    DATASETS,
    IMPLEMENTATIONS,
    METRICS,
    MODELS,
    SOURCE_FILES,
    check_sources,
    ref,
)
from src.ch02_ml.test_gate import EvaluationGate, atomic_json
from src.ch02_ml.workflow import checked_reference, selections
from src.common.artifact_core import ArtifactStore, write_once
from src.common.contracts import ROOT, canonical_sha256, read_json, validate_document
from src.common.data_access import DatasetView
from src.common.eda_artifacts import read_rows
from src.common.metric_core import classification_metrics, regression_metrics
from src.common.numpy_engine import NumpyNetwork
from src.common.training_core import batch_order


def check_xml(path):
    suites = list(ET.parse(path).getroot().iter("testsuite"))
    if not suites or any(int(s.get(key, "0")) for s in suites for key in ("failures", "errors", "skipped")):
        raise ValueError(f"Missing/failing/skipped tests: {path.name}")
    return sum(int(s.get("tests", "0")) for s in suites)


def recompute(rows, task):
    y = np.asarray([row["target"] for row in rows])
    p = np.asarray([row["prediction"] for row in rows])
    if task == "binary":
        values = classification_metrics(y.astype(int), p)
        info = calibration(y, p[:, 1])
        values.update({key: {"value": info[key], "undefined_reason": None} for key in ("brier", "ece")})
    else:
        values = regression_metrics(y, p[:, 0])
        nonzero = np.all(np.abs(y) > 1e-8)
        values["mape"] = {
            "value": float(np.mean(np.abs(p[:, 0] - y) / np.abs(y)) * 100) if nonzero else None,
            "undefined_reason": None if nonzero else "Zero/near-zero true targets",
        }
    return metric_rows(values, task)


def audit_predictions(entry, selected, split, targets_by_dataset):
    path = (
        checked_reference(selected["validation_predictions"])
        if split == "validation"
        else checked_reference(
            read_json(BASE / "test_seals" / entry["dataset_id"] / (entry["run_id"] + ".result.json"))[
                "predictions"
            ]
        )
    )
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    view = DatasetView(entry["dataset_id"])
    contract = read_json(view.split_dir / "split_contract.json")
    expected = next(row for row in contract["partitions"] if row["name"] == split)
    ids = read_rows(checked_reference(expected["ids"]))
    if [row["id"] for row in rows] != ids:
        raise ValueError("Prediction IDs do not match complete frozen split")
    labels = canonical_sha256([row["target"] for row in rows])
    key = (entry["dataset_id"], split)
    if key in targets_by_dataset and targets_by_dataset[key] != labels:
        raise ValueError("Ground truth changed between methods")
    targets_by_dataset[key] = labels
    config = read_json(checked_reference(entry["config"]))
    metrics = read_json(METRICS / split / (entry["run_id"] + ".json"))
    if entry["method"] in IMPLEMENTATIONS:
        validate_document("run", metrics, publish=True)
    actual = {row["name"]: row for row in metrics["metrics"]}
    for row in recompute(rows, config["task"]):
        other = actual[row["name"]]
        if row["value"] is None:
            if other["value"] is not None or not other["undefined_reason"]:
                raise ValueError("Undefined metric lost")
        elif not np.isclose(row["value"], other["value"], rtol=1e-10, atol=1e-10):
            raise ValueError("Saved prediction/metric mismatch")
    return len(rows)


def verify(pretest=False, create_lock=False):
    dependency = verify_core()
    release = check_sources()
    artifacts = selections(release)
    tests = {
        name: check_xml(BASE / filename)
        for name, filename in (("torch", "unit-torch.xml"), ("keras", "unit-keras.xml"))
    }
    coverage = read_json(BASE / "coverage_combined.json")
    if coverage["totals"]["percent_covered"] < 80:
        raise ValueError("Phase26 coverage below 80%")
    targets = {}
    prediction_counts = {}
    neural = 0
    for entry in release["runs"]:
        selected = read_json(BASE / "runs" / entry["run_id"] / "selection.json")
        config = read_json(checked_reference(entry["config"]))
        weights = ArtifactStore(MODELS / entry["run_id"]).load_checkpoint(
            "best",
            provenance(entry, config),
            expected_manifest_sha256=selected["checkpoint_metadata"]["sha256"],
        )
        if entry["method"] in IMPLEMENTATIONS:
            neural += 1
            model = read_json(checked_reference(entry["model_contract"]))
            if sum(layer["parameter_count"] > 0 for layer in model["layers"]) < 6:
                raise ValueError("MLP below six learnable layers")
            if model["parameter_count"] != sum(v.size for v in weights.values()):
                raise ValueError("Parameter count mismatch")
            history = read_json(checked_reference(selected["history"]))
            best = min(history, key=lambda row: row["validation_loss"])["epoch"]
            if selected["best_epoch"] != best:
                raise ValueError("Not the minimum validation-loss checkpoint")
            for row in history:
                size = read_json(BASE / "data" / (entry["dataset_id"] + ".json"))["training_ids"]
                if row["batch_order_sha256"] != canonical_sha256(
                    batch_order(size, 32, entry["seed"], row["epoch"])
                ):
                    raise ValueError("Batch schedule changed")
            demo = read_json(checked_reference(selected["cpu_demo"]))
            with np.load(CACHE / f"{entry['dataset_id']}_development.npz", allow_pickle=False) as data:
                output = NumpyNetwork(config["plan"], weights).forward(data["train_x"][:4])
            np.testing.assert_allclose(output, demo["raw_output"], rtol=1e-6, atol=1e-6)
        for split in ("validation",) if pretest else ("validation", "test"):
            count = audit_predictions(entry, selected, split, targets)
            prediction_counts[entry["dataset_id"] + "_" + split] = count
    seals = {}
    if not pretest:
        for dataset in DATASETS:
            gate = EvaluationGate(BASE / "test_seals" / dataset)
            state = gate.state()
            if (
                state["state"] != "evaluated"
                or state["evaluation_count"] != 1
                or len(state["approved_run_ids"]) != 18
            ):
                raise ValueError("Incomplete or repeated TEST batch")
            validate_document("seal", state)
            seals[dataset] = {
                "state": state["state"],
                "evaluation_count": state["evaluation_count"],
                "runs": 18,
            }
            for run in state["approved_run_ids"]:
                if not (gate.root / (run + ".claimed")).exists():
                    raise ValueError("Unclaimed TEST result")
    result = {
        "phase": 26,
        "status": "PASS",
        "stage": "pretest" if pretest else "final",
        "at": datetime.now(UTC).isoformat(),
        "code_sha256": release["code"]["dirty_tree_sha256"],
        "neural_runs": neural,
        "classical_runs": len(release["runs"]) - neural,
        "tests": tests,
        "coverage_percent": coverage["totals"]["percent_covered"],
        "prediction_counts": prediction_counts,
        "test_seals": seals,
        "dependency_phase25_status": dependency["status"],
        "ch5_test_run_count": dependency["ch5_test_run_count"],
        "test_model_forward_executed_by_verifier": False,
    }
    lock = BASE / "experiment_lock.json"
    if create_lock or lock.exists():
        paths = [ROOT / row["path"] for row in artifacts] + [ROOT / path for path in SOURCE_FILES]
        paths += list((BASE / "test_seals").rglob("*")) + list((METRICS / "test").glob("*.json"))
        paths += list((ROOT / "artifacts/predictions/phase26/test").glob("*.gz"))
        paths += list((ROOT / "tests/ch02_ml").glob("*.py"))
        paths += [
            BASE / "release.json",
            BASE / "pretest_verification.json",
            BASE / "unit-torch.xml",
            BASE / "unit-keras.xml",
            BASE / "coverage_combined.json",
        ]
        paths += [ROOT / "docs/phase26_report.md", ROOT / "report/sections/v3/ch02_ml.md"]
        paths += list((ROOT / "artifacts/figures/phase26").glob("*.png")) + list(
            (ROOT / "artifacts/metrics/phase26/tables").glob("*.csv")
        )
        records = [ref(path) for path in sorted({path for path in paths if path.is_file()})]
        document = {"phase": 26, "files": records, "test_model_forward_by_verifier": False}
        if lock.exists():
            if read_json(lock) != document:
                raise ValueError("Phase26 changed after lock; revision required")
        else:
            if pretest:
                raise ValueError("Cannot lock incomplete TEST evidence")
            write_once(lock, document)
        result["locked_files"] = len(records)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretest", action="store_true")
    parser.add_argument("--lock", action="store_true")
    args = parser.parse_args()
    result = verify(args.pretest, args.lock)
    target = BASE / ("pretest_verification.json" if args.pretest else "verification.json")
    if args.pretest:
        write_once(target, result)
    else:
        atomic_json(target, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
