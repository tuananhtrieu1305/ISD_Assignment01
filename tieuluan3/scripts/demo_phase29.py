"""Portable NumPy CPU comparison, family toggle, fixed TRAIN sample by default."""

import argparse
import json
import sys
import time
from datetime import UTC, datetime, timedelta

from scripts import demo_phase28 as rnn_demo
from src.ch02_ml.experiment import provenance
from src.ch02_ml.protocol import array_sha256
from src.ch04_rnn_lstm.phase29.protocol import BASE, DATASETS, IMPLEMENTATIONS, check_sources, checked
from src.common.artifact_core import ArtifactStore
from src.common.contracts import canonical_sha256, read_json, validate_document
from src.common.numpy_engine import NumpyNetwork


def sample_request(dataset, family="lstm"):
    if dataset not in DATASETS or family not in {"rnn", "lstm"}:
        raise ValueError("Require a declared recurrent dataset/family")
    request, sample_id = rnn_demo.sample_request(dataset)
    request["family"] = family
    return request, sample_id


def infer(request, seed=42):
    if seed not in {17, 42, 73}:
        raise ValueError("Undeclared seed")
    validate_document("api", request)
    if request["family"] == "rnn":
        return rnn_demo.infer(request, seed)
    if request["family"] != "lstm":
        raise ValueError("Require RNN or LSTM")
    release = check_sources()
    # Same frozen decoder/scaler/order. Only the dispatch label is changed for decoding.
    x, adapter = rnn_demo.decode_request({**request, "family": "rnn"})
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
        checkpoint = checked(selected["checkpoint"])
        checked(selected["checkpoint_metadata"])
        weights = ArtifactStore(checkpoint.parent).load_checkpoint(
            "best",
            provenance(entry, config),
            expected_manifest_sha256=selected["checkpoint_metadata"]["sha256"],
        )
        model = NumpyNetwork(config["plan"], weights)
        started = time.perf_counter()
        prediction = adapter.inverse_target(model.forward(x))[0]
        row = {
            "implementation": method,
            "status": "succeeded",
            "model_id": entry["run_id"],
            "actual_device": "cpu",
            "actual_backend": "numpy",
            "inference_ms": (time.perf_counter() - started) * 1000,
            "artifact_sha256": selected["checkpoint"]["sha256"],
            "prediction": {
                "kind": "regression",
                "values": prediction.tolist(),
                "unit": config["unit"],
                "horizons": config["horizons"],
            },
            "error": None,
            "input_sha256": input_hash,
            "comparison_group_sha256": entry["comparison_group_sha256"],
        }
        validate_document("api#result", row)
        results.append(row)
        metrics.append(selected["validation_metrics"])
    now = datetime.now(UTC)
    suffix = canonical_sha256(request)[:16]
    job = {
        "schema_version": "3.0.0",
        "request_id": f"lstm_request_{suffix}",
        "job_id": f"lstm_demo_{suffix}",
        "request_sha256": canonical_sha256(request),
        "status": "succeeded",
        "dataset_id": request["dataset_id"],
        "family": "lstm",
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
    parser.add_argument("--family", choices=("rnn", "lstm"), default="lstm")
    parser.add_argument("--seed", choices=(17, 42, 73), type=int, default=42)
    args = parser.parse_args()
    request, sample_id = sample_request(args.dataset, args.family)
    job = infer(request, args.seed)
    if any(name in sys.modules for name in ("torch", "tensorflow", "keras")):
        raise ValueError("Portable demo must not import GPU frameworks")
    print(
        json.dumps(
            {
                "sample_id": sample_id,
                "input_split": "train",
                "job": job,
                "warning": "Academic retrospective CPU demo; no financial recommendation; not HTTP/Render live",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
