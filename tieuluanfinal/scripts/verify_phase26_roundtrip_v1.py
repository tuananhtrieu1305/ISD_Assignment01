"""Versioned read-only auditor: restore serialized probability dtype for ECE.

Training, prediction evaluator, sealed configs and metric artifacts are unchanged.
The original auditor remains immutable. Comparisons retain rtol=atol=1e-10.
"""

from __future__ import annotations

import argparse
import gzip
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from scripts.verify_phase25 import verify as verify_core
from scripts.verify_phase26 import check_xml, recompute
from src.ch02_ml.diagnostics import calibration
from src.ch02_ml.experiment import provenance
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
from src.ch02_ml.workflow import checked_reference, pending_test_runs, selections
from src.common.artifact_core import ArtifactStore, sha256_file, write_once
from src.common.contracts import ROOT, canonical_sha256, read_json, validate_document
from src.common.data_access import DatasetView
from src.common.eda_artifacts import read_rows
from src.common.numpy_engine import NumpyNetwork
from src.common.training_core import batch_order


def recompute_typed(rows, task, dtype):
    values = recompute(rows, task)
    if task == "binary":
        y = np.asarray([r["target"] for r in rows], dtype=float)
        p = np.asarray([r["prediction"] for r in rows], dtype=dtype)
        info = calibration(y, p[:, 1])
        for row in values:
            if row["name"] in {"brier", "ece"}:
                row["value"] = info[row["name"]]
    return values


def prediction_dtype(entry, selected):
    if entry["method"] in IMPLEMENTATIONS:
        return "float32"
    metadata = read_json(checked_reference(selected["checkpoint_metadata"]))["arrays"]
    if entry["method"] == "logistic_regression":
        return str(np.result_type("float32", metadata["coef"]["dtype"], metadata["intercept"]["dtype"]))
    if entry["method"] == "majority":
        return metadata["constant"]["dtype"]
    return "float64"  # Portable forest accumulator / original-unit regression.


def audit_predictions(entry, selected, split, targets):
    result = None
    if split == "test":
        result = read_json(BASE / "test_seals" / entry["dataset_id"] / (entry["run_id"] + ".result.json"))
        for key in ("metrics", "predictions", "details"):
            checked_reference(result[key])
    path = checked_reference(
        selected["validation_predictions"] if split == "validation" else result["predictions"]
    )
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    view = DatasetView(entry["dataset_id"])
    contract = read_json(view.split_dir / "split_contract.json")
    partition = next(row for row in contract["partitions"] if row["name"] == split)
    ids = read_rows(checked_reference(partition["ids"]))
    if [row["id"] for row in rows] != ids:
        raise ValueError("Prediction IDs differ from full frozen split")
    key = (entry["dataset_id"], split)
    label_hash = canonical_sha256([r["target"] for r in rows])
    if key in targets and targets[key] != label_hash:
        raise ValueError("Ground truth differs between runs")
    targets[key] = label_hash
    config = read_json(checked_reference(entry["config"]))
    metric_path = METRICS / split / (entry["run_id"] + ".json")
    metric = read_json(metric_path)
    if entry["method"] in IMPLEMENTATIONS:
        validate_document("run", metric, publish=True)
    actual = {row["name"]: row for row in metric["metrics"]}
    for row in recompute_typed(rows, config["task"], prediction_dtype(entry, selected)):
        other = actual[row["name"]]
        if row["value"] is None:
            if other["value"] is not None or not other["undefined_reason"]:
                raise ValueError("Undefined metric lost")
        elif not np.isclose(row["value"], other["value"], rtol=1e-10, atol=1e-10):
            raise ValueError(
                f"Saved metric mismatch: {entry['run_id']}/{row['name']} {row['value']} != {other['value']}"
            )
    return len(rows)


def verify(pretest=False, create_lock=False):
    dependency = verify_core()
    release = check_sources()
    artifacts = selections(release)
    original = read_json(ROOT / "artifacts/manifests/phase26/release.json")
    for record in original["source_files"]:
        if (
            sha256_file(ROOT / "artifacts/manifests/phase26/preflight_v1_source" / record["path"])
            != record["sha256"]
        ):
            raise ValueError("Preflight v1 source snapshot changed")
    for dataset in DATASETS:
        receipt = read_json(BASE / "data" / (dataset + ".json"))
        checked_reference(receipt["cache"])
    tests = {
        name: check_xml(BASE / filename)
        for name, filename in (("torch", "unit-torch.xml"), ("keras", "unit-keras.xml"))
    }
    coverage = read_json(BASE / "coverage_combined.json")
    if coverage["totals"]["percent_covered"] < 80:
        raise ValueError("Phase26 coverage below 80%")
    targets = {}
    counts = {}
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
            if sum(layer["parameter_count"] > 0 for layer in model["layers"]) < 6 or model[
                "parameter_count"
            ] != sum(v.size for v in weights.values()):
                raise ValueError("Layer/parameter count mismatch")
            history = read_json(checked_reference(selected["history"]))
            if selected["best_epoch"] != min(history, key=lambda row: row["validation_loss"])["epoch"]:
                raise ValueError("Not minimum validation loss checkpoint")
            size = read_json(BASE / "data" / (entry["dataset_id"] + ".json"))["training_ids"]
            for row in history:
                if row["batch_order_sha256"] != canonical_sha256(
                    batch_order(size, 32, entry["seed"], row["epoch"])
                ):
                    raise ValueError("Batch schedule changed")
            demo = read_json(checked_reference(selected["cpu_demo"]))
            with np.load(CACHE / (entry["dataset_id"] + "_development.npz"), allow_pickle=False) as data:
                output = NumpyNetwork(config["plan"], weights).forward(data["train_x"][:4])
            np.testing.assert_allclose(output, demo["raw_output"], rtol=1e-6, atol=1e-6)
        for split in ("validation",) if pretest else ("validation", "test"):
            counts[entry["dataset_id"] + "_" + split] = audit_predictions(entry, selected, split, targets)
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
                raise ValueError("Incomplete/repeated TEST batch")
            validate_document("seal", state)
            if pending_test_runs(gate):
                raise ValueError("Pending TEST runs")
            for run in state["approved_run_ids"]:
                if not (gate.root / (run + ".claimed")).is_file():
                    raise ValueError("Missing TEST claim")
            seals[dataset] = {"state": "evaluated", "evaluation_count": 1, "runs": 18}
    result = {
        "phase": 26,
        "status": "PASS",
        "stage": "pretest" if pretest else "final",
        "at": datetime.now(UTC).isoformat(),
        "code_sha256": release["code"]["dirty_tree_sha256"],
        "auditor": ref(Path(__file__)),
        "audit_revision": "probability_dtype_roundtrip_v1",
        "metric_rtol": 1e-10,
        "metric_atol": 1e-10,
        "neural_runs": neural,
        "classical_runs": 54 - neural,
        "tests": tests,
        "coverage_percent": coverage["totals"]["percent_covered"],
        "prediction_counts": counts,
        "test_seals": seals,
        "dependency_phase25_status": dependency["status"],
        "ch5_test_run_count": dependency["ch5_test_run_count"],
        "test_model_forward_executed_by_verifier": False,
    }
    lock = BASE / "experiment_lock.json"
    if create_lock or lock.exists():
        if pretest:
            raise ValueError("Cannot lock before TEST evidence")
        visual = read_json(BASE / "visual_qa.json")
        if visual["status"] != "PASS":
            raise ValueError("Visual QA not approved")
        for record in visual["figures"]:
            checked_reference(record)
        paths = (
            [ROOT / row["path"] for row in artifacts]
            + [ROOT / path for path in SOURCE_FILES]
            + [Path(__file__)]
        )
        paths += list((BASE / "test_seals").rglob("*")) + list((BASE / "runs").rglob("*.json"))
        paths += list((METRICS / "test").glob("*.json")) + list(
            (ROOT / "artifacts/predictions/phase26/test").glob("*.gz")
        )
        paths += list((ROOT / "tests/ch02_ml").glob("*.py"))
        paths += [
            BASE / name
            for name in (
                "release.json",
                "audit_revision.json",
                "pretest_verification.json",
                "unit-torch.xml",
                "unit-keras.xml",
                "coverage_combined.json",
                "coverage_final.json",
                "trained_registry.json",
                "report_generation.json",
                "visual_qa.json",
                "regression-tests.xml",
            )
        ]
        paths += [
            ROOT / name
            for name in (
                "docs/phase26_report.md",
                "docs/phase26_operations.md",
                "report/sections/v3/ch02_ml.md",
                "report/sections/v3/ch02_ml_theory.md",
                "scripts/summarize_phase26.py",
                "scripts/demo_phase26.py",
                "scripts/check_phase26.ps1",
                "scripts/finish_phase26.ps1",
                "scripts/diagnose_phase26_metrics.py",
                "artifacts/manifests/phase26/revision_r2.json",
            )
        ]
        for folder, pattern in (
            ("artifacts/figures/phase26", "*.png"),
            ("artifacts/figures/phase26", "*.svg"),
            ("artifacts/metrics/phase26/tables", "*.csv"),
            ("experiments/notebooks/v3/ch02_ml", "*.ipynb"),
            ("report/references/functions/v3_ch2", "*.md"),
            ("artifacts/manifests/phase26/preflight_v1_source", "*"),
        ):
            paths += list((ROOT / folder).rglob(pattern))
        records = [ref(path) for path in sorted({path for path in paths if path.is_file()})]
        document = {
            "phase": 26,
            "audit_revision": "probability_dtype_roundtrip_v1",
            "files": records,
            "test_model_forward_by_verifier": False,
        }
        if lock.exists():
            if read_json(lock) != document:
                raise ValueError("Phase26 changed after lock; versioned revision required")
        else:
            write_once(lock, document)
        result["locked_files"] = len(records)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretest", action="store_true")
    parser.add_argument("--lock", action="store_true")
    args = parser.parse_args()
    result = verify(args.pretest, args.lock)
    path = BASE / ("pretest_verification.json" if args.pretest else "verification.json")
    if args.pretest:
        write_once(path, result)
    else:
        atomic_json(path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
