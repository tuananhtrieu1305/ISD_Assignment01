"""CPU-only CNN inference contract and fixed TRAIN saliency, never TEST."""

import argparse
import base64
import binascii
import io
import json
import sys
import time
from datetime import UTC, datetime, timedelta

import numpy as np
from PIL import Image, UnidentifiedImageError

from src.ch02_ml.experiment import provenance
from src.ch02_ml.protocol import array_sha256
from src.ch03_cnn.experiment import checked
from src.ch03_cnn.image_cache import development_cache
from src.ch03_cnn.protocol import BASE, DATASETS, IMPLEMENTATIONS, MODELS, check_sources
from src.ch03_cnn.training import probabilities
from src.common.artifact_core import ArtifactStore
from src.common.contracts import canonical_sha256, read_json, validate_document
from src.common.data_access import DatasetView
from src.common.numpy_engine import NumpyNetwork
from src.common.tensor_adapters import image_batch


def decode_request(request):
    validate_document("api", request)
    if (
        request["chapter"] != 3
        or request["family"] != "cnn"
        or request["dataset_id"] not in DATASETS
        or request["implementations"] != list(IMPLEMENTATIONS)
        or request["input"]["kind"] != "image"
    ):
        raise ValueError("Not a CNN image comparison request")
    try:
        encoded = base64.b64decode(request["input"]["data"], validate=True)
        if len(encoded) > 4_718_592:
            raise ValueError("Image exceeds decoded input budget")
        with Image.open(io.BytesIO(encoded)) as image:
            expected = {"image/png": "PNG", "image/jpeg": "JPEG"}[request["input"]["media_type"]]
            if image.format != expected or image.mode != "RGB" or image.width * image.height > 20_000_000:
                raise ValueError("Require budgeted RGB PNG/JPEG with matching media type")
            view = DatasetView(request["dataset_id"])
            pixels = np.asarray(
                image.resize(tuple(view.preprocessing["input_shape_hwc"][:2]), Image.Resampling.BILINEAR)
            )
        return image_batch(pixels[None], "scratch")
    except (UnidentifiedImageError, OSError, binascii.Error, Image.DecompressionBombError) as error:
        raise ValueError("Invalid or unsafe encoded image") from error


def infer(request, seed=42):
    if seed not in {17, 42, 73}:
        raise ValueError("Undeclared seed")
    release = check_sources()
    x = decode_request(request)
    input_hash = array_sha256(x)
    results = []
    metric_artifacts = []
    for method in IMPLEMENTATIONS:
        entry = next(
            e
            for e in release["runs"]
            if e["dataset_id"] == request["dataset_id"] and e["seed"] == seed and e["method"] == method
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
        p = probabilities(model.forward(x))[0]
        inference_ms = (time.perf_counter() - tick) * 1000
        names = config["class_names"]
        result = {
            "implementation": method,
            "status": "succeeded",
            "model_id": entry["run_id"],
            "actual_device": "cpu",
            "actual_backend": "numpy",
            "inference_ms": inference_ms,
            "artifact_sha256": selected["checkpoint"]["sha256"],
            "prediction": {
                "kind": "classification",
                "label": names[str(int(p.argmax()))],
                "probabilities": [
                    {"label": names[str(i)], "value": float(value)} for i, value in enumerate(p)
                ],
            },
            "error": None,
            "input_sha256": input_hash,
            "comparison_group_sha256": entry["comparison_group_sha256"],
        }
        validate_document("api#result", result)
        results.append(result)
        metric_artifacts.append(selected["validation_metrics"])
    now = datetime.now(UTC)
    suffix = canonical_sha256(request)[:16]
    job = {
        "schema_version": "3.0.0",
        "request_id": f"cnn_request_{suffix}",
        "job_id": f"cnn_demo_{suffix}",
        "request_sha256": canonical_sha256(request),
        "status": "succeeded",
        "dataset_id": request["dataset_id"],
        "family": "cnn",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "results": results,
        "comparison_valid": True,
        "comparison_blockers": [],
        "trace_ids": [],
        "metric_artifacts": metric_artifacts,
        "input_sha256": input_hash,
    }
    validate_document("api#job", job)
    return job


def sample_request(dataset):
    cache, view = development_cache(dataset)
    key = view.ids("train")[0]
    pixels = cache.pixels[cache.positions[key]]
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")
    return {
        "schema_version": "3.0.0",
        "chapter": 3,
        "dataset_id": dataset,
        "family": "cnn",
        "implementations": list(IMPLEMENTATIONS),
        "input": {
            "kind": "image",
            "encoding": "base64",
            "media_type": "image/png",
            "data": base64.b64encode(buffer.getvalue()).decode(),
        },
    }, key


def saliency(plan, weights, x):
    if len(x) != 1:
        raise ValueError("Saliency requires one fixed TRAIN example")
    model = NumpyNetwork(plan, weights)
    logits = model.forward(x)
    chosen = int(logits[0].argmax())
    dy = np.zeros_like(logits)
    dy[0, chosen] = 1
    _, dx = model.backward(dy)
    heat = np.abs(dx[0]).max(axis=-1)
    maximum = float(heat.max())
    if maximum > 0:
        heat = heat / maximum
    return {
        "predicted_class_id": chosen,
        "map": heat,
        "definition": "max-channel absolute gradient of predicted logit, divided by image maximum; zero map stays zero",
        "warning": "Sensitivity illustration on fixed TRAIN image, not lesion segmentation, causality or clinical explanation",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=DATASETS, required=True)
    parser.add_argument("--seed", type=int, choices=(17, 42, 73), default=42)
    args = parser.parse_args()
    request, key = sample_request(args.dataset)
    result = infer(request, args.seed)
    if any(name in sys.modules for name in ("torch", "tensorflow", "keras")):
        raise RuntimeError("Portable demo unexpectedly imported a GPU framework")
    print(
        json.dumps(
            {
                "input_split": "train",
                "id": key,
                "serving_backend": "numpy_cpu_portable",
                "training_implementations": list(IMPLEMENTATIONS),
                "warning": "Academic comparison, not clinical diagnosis",
                "job": result,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
