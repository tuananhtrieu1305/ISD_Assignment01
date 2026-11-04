"""Portable CPU RNN comparison; engineered raw feature sequences, never TEST."""

import argparse
import json
import sys
import time
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd

from src.ch02_ml.experiment import provenance
from src.ch02_ml.protocol import array_sha256
from src.ch04_rnn_lstm.protocol import BASE, DATASETS, IMPLEMENTATIONS, MODELS, check_sources, checked
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.artifact_core import ArtifactStore
from src.common.contracts import canonical_sha256, read_json, validate_document
from src.common.data_access import DatasetView
from src.common.numpy_engine import NumpyNetwork


def decode_request(request):
    validate_document("api", request)
    if (
        request["chapter"] != 4
        or request["family"] != "rnn"
        or request["dataset_id"] not in DATASETS
        or request["implementations"] != list(IMPLEMENTATIONS)
        or request["input"]["kind"] != "sequence"
    ):
        raise ValueError("Not an RNN sequence comparison request")
    view = DatasetView(request["dataset_id"])
    values = np.asarray(request["input"]["values"], dtype="float64")
    columns = view.adapter.output_feature_names
    if values.shape != (view.spec["lookback"], len(columns)) or not np.isfinite(values).all():
        raise ValueError("Sequence length/feature order/finite values mismatch")
    if request["dataset_id"] == "ch4_bis_house_prices":
        country = values[:, 2:]
        if (
            not np.isin(country, [0, 1]).all()
            or not np.all(country.sum(axis=1) == 1)
            or not np.all(country == country[0])
        ):
            raise ValueError("Require one fixed country encoding throughout the window")
    x = view.adapter.transform(pd.DataFrame(values, columns=columns))[None]
    return x, view.adapter


def sample_request(dataset):
    data = WindowData(dataset)
    key = data.train_ids[0]
    row = data.rows[key]
    frame = data.frame.iloc[row["start_index"] : row["origin_index"] + 1][
        data.adapter.output_feature_names
    ].copy()
    for name in frame:
        frame[name] = frame[name].fillna(data.adapter.state["numeric"][name]["median"])
    return {
        "schema_version": "3.0.0",
        "chapter": 4,
        "dataset_id": dataset,
        "family": "rnn",
        "implementations": list(IMPLEMENTATIONS),
        "input": {
            "kind": "sequence",
            "values": frame.to_numpy(dtype="float64").tolist(),
            "as_of": row["context_end"] + "+00:00",
        },
    }, key


def infer(request, seed=42):
    if seed not in {17, 42, 73}:
        raise ValueError("Undeclared seed")
    release = check_sources()
    x, adapter = decode_request(request)
    input_hash, results, metrics = array_sha256(x), [], []
    for method in IMPLEMENTATIONS:
        entry = next(
            e
            for e in release["runs"]
            if e["dataset_id"] == request["dataset_id"]
            and e["fold"] is None
            and e["seed"] == seed
            and e["method"] == method
        )
        selected = read_json(BASE / "runs" / entry["run_id"] / "selection.json")
        config = read_json(checked(entry["config"]))
        weights = ArtifactStore(MODELS / entry["run_id"]).load_checkpoint(
            "best",
            provenance(entry, config),
            expected_manifest_sha256=selected["checkpoint_metadata"]["sha256"],
        )
        model = NumpyNetwork(config["plan"], weights)
        tick = time.perf_counter()
        values = adapter.inverse_target(model.forward(x))[0]
        elapsed = (time.perf_counter() - tick) * 1000
        result = {
            "implementation": method,
            "status": "succeeded",
            "model_id": entry["run_id"],
            "actual_device": "cpu",
            "actual_backend": "numpy",
            "inference_ms": elapsed,
            "artifact_sha256": selected["checkpoint"]["sha256"],
            "prediction": {
                "kind": "regression",
                "values": values.tolist(),
                "unit": config["unit"],
                "horizons": config["horizons"],
            },
            "error": None,
            "input_sha256": input_hash,
            "comparison_group_sha256": entry["comparison_group_sha256"],
        }
        validate_document("api#result", result)
        results.append(result)
        metrics.append(selected["validation_metrics"])
    now = datetime.now(UTC)
    suffix = canonical_sha256(request)[:16]
    job = {
        "schema_version": "3.0.0",
        "request_id": f"rnn_request_{suffix}",
        "job_id": f"rnn_demo_{suffix}",
        "request_sha256": canonical_sha256(request),
        "status": "succeeded",
        "dataset_id": request["dataset_id"],
        "family": "rnn",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "results": results,
        "comparison_valid": True,
        "comparison_blockers": [],
        "trace_ids": [],
        "metric_artifacts": metrics,
        "input_sha256": input_hash,
    }
    validate_document("api#job", job)
    return job


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=DATASETS, required=True)
    parser.add_argument("--seed", choices=(17, 42, 73), type=int, default=42)
    args = parser.parse_args()
    request, key = sample_request(args.dataset)
    job = infer(request, args.seed)
    if any(name in sys.modules for name in ("torch", "keras", "tensorflow")):
        raise RuntimeError("Portable inference unexpectedly imported a native framework")
    print(
        json.dumps(
            {
                "input_split": "train",
                "id": key,
                "job": job,
                "warning": "Academic retrospective demo, not investment advice or household-general evidence; actual serving is NumPy CPU",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
