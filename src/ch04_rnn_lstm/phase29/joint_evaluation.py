"""Joint main RNN/LSTM TEST membership and consumed-job validation.

Model execution/controller are added only after synthetic checks; no implicit TEST.
"""

import copy
import gzip
import json
import time
from datetime import UTC, datetime
from itertools import product

import numpy as np

from src.ch04_rnn_lstm.phase29.protocol import (
    BASE,
    DATASETS,
    FOLDS,
    IMPLEMENTATIONS,
    METRICS,
    PREDICTIONS,
    SEEDS,
    checked,
    ref,
)
from src.common.artifact_core import ArtifactStore, write_once
from src.common.contracts import read_json, validate_document
from src.common.metric_core import regression_metrics
from src.common.tensor_adapters import TensorAdapter


def approved_members(rnn_release, lstm_release):
    members = []
    for family, release in (("rnn", rnn_release), ("lstm", lstm_release)):
        expected = set(product(DATASETS, FOLDS, IMPLEMENTATIONS, SEEDS))
        if family == "rnn":
            expected |= {
                (d, f, m, 42) for d, f, m in product(DATASETS, FOLDS, ("last_value", "seasonal_naive"))
            }
        keys = [(r["dataset_id"], r["fold"], r["method"], r["seed"]) for r in release["runs"]]
        if (
            len(keys) != len(set(keys))
            or set(keys) != expected
            or len({r["run_id"] for r in release["runs"]}) != len(keys)
        ):
            raise ValueError("Incomplete/duplicate/unsupported recurrent declaration")
        for entry in release["runs"]:
            if entry["fold"] is None:
                members.append(
                    {
                        **entry,
                        "family": family if entry["method"] in IMPLEMENTATIONS else "classical",
                        "owner_phase": 28 if family == "rnn" else 29,
                    }
                )
    if len(members) != 60 or len({m["run_id"] for m in members}) != 60:
        raise ValueError("Joint TEST requires exactly 60 distinct main checkpoints")
    return members


def pending(gate, code):
    state, manifest = gate._check(code, {"evaluating", "evaluated"})
    result = []
    for run in manifest["approved_run_ids"]:
        claimed = (gate.root / (run + ".claimed")).exists()
        path = gate.root / (run + ".result.json")
        if path.exists():
            row = read_json(path)
            if not claimed or row.get("status") != "PASS":
                raise ValueError("Invalid TEST result journal")
            names = ("metrics", "predictions", "details")
            if manifest.get("evidence_kind", "measured") != "synthetic_fixture" and not all(
                k in row for k in names
            ):
                raise ValueError("Measured TEST result lacks artifacts")
            for name in names:
                if name in row:
                    checked(row[name])
        elif claimed:
            raise ValueError("Interrupted consumed TEST claim; never repeat")
        elif state["state"] == "evaluated":
            raise ValueError("Terminal TEST seal lacks results")
        else:
            result.append(run)
    return result


def make_native(member, config, weights):
    # Each call lives in the native framework's isolated worker environment.
    if member["family"] == "lstm":
        from src.ch04_rnn_lstm.phase29.experiment import make_trainer
    elif member["family"] == "rnn":
        from src.ch04_rnn_lstm.experiment import make_trainer
    else:
        raise ValueError("Native neural family required")
    return make_trainer(member["method"], config["plan"], weights)


def save_test_predictions(run, cache, predictions):
    targets = cache.targets(cache.ids)
    if predictions.shape != targets.shape or not np.isfinite(predictions).all():
        raise ValueError("Invalid TEST output shape/values")
    path = PREDICTIONS / "test" / (run + ".jsonl.gz")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream, gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as packed:
        for key, target, prediction in zip(cache.ids, targets, predictions, strict=True):
            row = {
                "id": key,
                "series": cache.rows[key]["series"],
                "target_times": cache.rows[key]["target_times"],
                "target": target.tolist(),
                "prediction": prediction.tolist(),
            }
            packed.write((json.dumps(row, sort_keys=True, allow_nan=False) + "\n").encode())
    return ref(path)


def evaluate_member(gate, code, run, cache):
    from src.ch02_ml.experiment import configure, provenance
    from src.ch04_rnn_lstm.export_r2 import validate_run
    from src.ch04_rnn_lstm.phase29.experiment import metric_rows
    from src.ch04_rnn_lstm.training import predict_windows

    _, manifest = gate._check(code, {"evaluating"})
    rows = [m for m in manifest["members"] if m["run_id"] == run]
    if len(rows) != 1 or run not in manifest["approved_run_ids"]:
        raise ValueError("Run/member not approved for joint TEST")
    member = rows[0]
    config = read_json(checked(member["config"]))
    selected = read_json(checked(member["selection"]))
    if (
        member["fold"] is not None
        or selected["selection_split"] != "validation"
        or selected["status"] != "succeeded"
        or not selected["inference_ready"]
        or selected["config"] != member["config"]
        or selected["model_contract"] != member["model_contract"]
        or cache.metadata["dataset_id"] != member["dataset_id"]
        or cache.metadata["input_shape"] != config["plan"]["input_shape"]
        or list(cache.horizons) != list(config.get("horizons", cache.horizons))
    ):
        raise ValueError("TEST checkpoint/data/config contract mismatch")
    # Consumed before native model construction or any TEST forward; no retry after failure.
    gate.claim(run, code)
    started = datetime.now(UTC).isoformat()
    checkpoint = checked(selected["checkpoint"])
    checked(selected["checkpoint_metadata"])
    weights = ArtifactStore(checkpoint.parent).load_checkpoint(
        "best", provenance(member, config), expected_manifest_sha256=selected["checkpoint_metadata"]["sha256"]
    )
    configure(member["method"], member["seed"])
    begin = time.perf_counter()
    if member["method"] in IMPLEMENTATIONS:
        trainer = make_native(member, config, weights)
        raw = predict_windows(trainer, cache, cache.ids, config["training"]["batch_size"])
        after = trainer.weights()
        if (
            trainer.iterations != 0
            or set(after) != set(weights)
            or any(not np.array_equal(after[k], weights[k]) for k in weights)
        ):
            raise ValueError("TEST inference changed weights or optimizer state")
        adapter = TensorAdapter(read_json(checked(cache.metadata["preprocessing"])))
        output = adapter.inverse_target(raw)
    else:
        if (
            member["family"] != "classical"
            or member["method"] not in {"last_value", "seasonal_naive"}
            or weights["baseline_kind"].tolist() != [int(member["method"] == "seasonal_naive")]
        ):
            raise ValueError("Wrong causal baseline checkpoint")
        output = cache.baseline(cache.ids, member["method"])
    forward_seconds = time.perf_counter() - begin
    output = np.asarray(output, "float64")
    targets = cache.targets(cache.ids)
    values = regression_metrics(targets, output, cache.horizons, cache.series(cache.ids))
    predictions = save_test_predictions(run, cache, output)
    original = read_json(checked(selected["validation_metrics"]))
    details = {
        "run_id": run,
        "metrics": values,
        "evaluator_sha256": code,
        "training_selection": member["selection"],
        "checkpoint": selected["checkpoint"],
        "test_count": len(cache.ids),
        "test_forward_and_model_load_seconds": forward_seconds,
        "optimizer_updates": 0,
        "test_forward_passes_per_window": 1,
        "efficiency_scope": "Train/RAM/VRAM/5warmup30repeat TRAIN-input timing copied byte-value from locked validation metric; not claimed as TEST-only measurements",
        "training_efficiency": original["efficiency"],
        "output_dtype": str(output.dtype),
        "test_seal_manifest_sha256": gate.state()["manifest_sha256"],
    }
    detail_path = BASE / "test_details" / (run + ".json")
    write_once(detail_path, details)
    metric = copy.deepcopy(original)
    metric.update(
        split="test",
        test_seal_id=manifest.get("seal_id", member["dataset_id"] + "_phase29_joint_test_v1"),
        evidence_kind=manifest.get("evidence_kind", "measured"),
        started_at=started,
        finished_at=datetime.now(UTC).isoformat(),
        metrics=metric_rows(values, config["unit"]),
        artifacts=[
            selected["checkpoint"],
            selected["checkpoint_metadata"],
            member["selection"],
            predictions,
            ref(detail_path),
        ],
    )
    metric["warnings"] = [
        w for w in metric["warnings"] if not w.startswith(("Validation only", "Validation-selected"))
    ]
    metric["warnings"].extend(
        [
            "Joint RNN/LSTM main TEST once after frozen validation selection; no optimizer updates or TEST-input timing repeats",
            details["efficiency_scope"],
        ]
    )
    if member["method"] in IMPLEMENTATIONS:
        if metric["evidence_kind"] == "synthetic_fixture":
            validate_document("run", metric, publish=False)
        else:
            validate_run(metric)
    else:
        metric["schema_version"] = "phase29.causal_baseline_test_run.1"
    path = METRICS / "test" / (run + ".json")
    write_once(path, metric)
    result = {
        "status": "PASS",
        "run_id": run,
        "metrics": ref(path),
        "predictions": predictions,
        "details": ref(detail_path),
        "checkpoint": selected["checkpoint"],
        "optimizer_updates": 0,
    }
    gate.record(run, result)
    return result
