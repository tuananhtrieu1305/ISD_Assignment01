"""Inference adapters over pinned trained weights. No training or TEST loaders."""

import base64
import binascii
import io
import time

import numpy as np
import pandas as pd
from PIL import Image, UnidentifiedImageError

from apps.api.v3.registry import ArtifactError
from src.common.artifact_core import ArtifactStore
from src.common.contracts import canonical_sha256, validate_document
from src.common.numpy_engine import NumpyNetwork
from src.common.tensor_adapters import TensorAdapter, image_batch

METHODS = ["scratch", "keras", "pytorch"]


def load_model(registry, spec):
    for record in spec["assets"]:
        registry.checked(record)
    config = registry.json(spec["config"])
    adapter_spec = registry.json(config["adapter"])
    preprocessing = registry.json(adapter_spec["preprocessing"])
    adapter = None if spec["family"] == "cnn" else TensorAdapter(preprocessing)
    if adapter and adapter.output_feature_names != adapter_spec["output_feature_names"]:
        raise ArtifactError("Feature order mismatch")
    metadata = registry.json(spec["checkpoint_metadata"])
    weights = ArtifactStore(
        registry.checked(spec["checkpoint"]).parent, max_bytes=8 * 1024**2
    ).load_checkpoint(
        "best", metadata["provenance"], expected_manifest_sha256=spec["checkpoint_metadata"]["sha256"]
    )
    return config, adapter_spec, adapter, weights


def decode_input(registry, request):
    validate_document("api", request)
    specs = [
        m
        for m in registry.models.values()
        if m["dataset_id"] == request["dataset_id"] and m["family"] == request["family"]
    ]
    if not specs:
        raise ValueError("Unsupported dataset/family")
    if request["chapter"] >= 5:
        text = request["input"]["text"]
        if len(text) > 500 or not text.strip():
            raise ValueError("Question must contain 1–500 characters")
        if request["chapter"] == 5:
            if len(" ".join(text.split())) < 3:
                raise ValueError("Question must contain at least3 characters")
            domain = {
                "ch5_medquad_diabetes": "medical",
                "ch5_finqa": "finance",
                "ch5_wikidata_subgraphs": "auto",
            }[request["dataset_id"]]
            if request["input"]["domain"] not in {domain, "auto"}:
                raise ValueError("Dataset/domain mismatch")
        else:
            from src.ch06_multi_agent.service import decode_question

            domain = request["dataset_id"].removeprefix("ch6_").removesuffix("_tasks")
            if request["input"]["domain"] != domain:
                raise ValueError("Domain mismatch")
            decode_question(domain, text)
        return None
    config = registry.json(specs[0]["config"])
    adapter_spec = registry.json(config["adapter"])
    preprocessing = registry.json(adapter_spec["preprocessing"])
    family, payload = request["family"], request["input"]
    if family == "cnn":
        try:
            content = base64.b64decode(payload["data"], validate=True)
            if len(content) > 4_718_592:
                raise ValueError("Image byte budget exceeded")
            with Image.open(io.BytesIO(content)) as image:
                expected = {"image/png": "PNG", "image/jpeg": "JPEG"}[payload["media_type"]]
                if image.format != expected or image.mode != "RGB" or image.width * image.height > 4_000_000:
                    raise ValueError("Require RGB PNG/JPEG, matching MIME and at most4M pixels")
                h, w, _ = config["plan"]["input_shape"]
                pixels = np.asarray(image.resize((w, h), Image.Resampling.BILINEAR))
            return image_batch(pixels[None], "scratch")
        except (UnidentifiedImageError, OSError, binascii.Error, Image.DecompressionBombError) as error:
            raise ValueError("Invalid encoded image") from error
    adapter = TensorAdapter(preprocessing)
    if family == "mlp":
        features = payload["features"]
        if any(isinstance(v, str) and len(v) > 256 for v in features.values()):
            raise ValueError("Feature string too long")
        frame = pd.DataFrame([features])
        for name in adapter.numeric_names:
            value = features.get(name)
            if value is not None and (
                not isinstance(value, (int, float)) or not np.isfinite(value) or abs(value) > 1e12
            ):
                raise ValueError("Numeric feature must be finite and bounded")
        return adapter.transform(frame)
    values = np.asarray(payload["values"], dtype="float64")
    if (
        tuple(values.shape) != tuple(config["plan"]["input_shape"])
        or not np.isfinite(values).all()
        or np.abs(values).max() > 1e12
    ):
        raise ValueError("Sequence shape/finite/budget mismatch")
    if request["dataset_id"] == "ch4_bis_house_prices":
        country = values[:, 2:]
        if (
            not np.isin(country, [0, 1]).all()
            or not np.all(country.sum(axis=1) == 1)
            or not np.all(country == country[0])
        ):
            raise ValueError("Require one fixed country throughout the sequence")
    return adapter.transform(pd.DataFrame(values, columns=adapter.output_feature_names))[None]


def empty_slot(method, input_hash, code):
    return {
        "implementation": method,
        "status": "unavailable",
        "model_id": None,
        "actual_device": "not_run",
        "actual_backend": "not_run",
        "inference_ms": None,
        "artifact_sha256": None,
        "prediction": None,
        "error": {"code": code, "message": "Inference unavailable"},
        "input_sha256": input_hash,
        "comparison_group_sha256": None,
    }


def failure_job(request, code):
    value = canonical_sha256(request["input"])
    return {
        "status": "failed",
        "results": [empty_slot(m, value, code) for m in request.get("implementations", METHODS)],
        "comparison_valid": False,
        "comparison_blockers": [code],
        "input_sha256": value,
        "trace_ids": [],
        "metric_artifacts": [],
    }


def prediction_from(raw, config, adapter, adapter_spec):
    raw = np.asarray(raw, dtype="float64")
    if not np.isfinite(raw).all():
        raise ValueError("Nonfinite model output")
    family = config["plan"]["family"]
    if family == "cnn" or config.get("task") in {"binary", "binary_classification"}:
        if family == "cnn":
            p = np.exp(raw[0] - raw[0].max())
            p /= p.sum()
        else:
            positive = float(1 / (1 + np.exp(-np.clip(raw[0, 0], -60, 60))))
            p = np.asarray([1 - positive, positive])
        names = adapter_spec["class_names"]
        return {
            "kind": "classification",
            "label": names[str(int(p.argmax()))],
            "probabilities": [{"label": names[str(i)], "value": float(v)} for i, v in enumerate(p)],
        }
    return {
        "kind": "regression",
        "values": adapter.inverse_target(raw)[0].reshape(-1).tolist(),
        "unit": config.get("unit", "USD"),
        "horizons": config.get("horizons", [1]),
    }


def neural_compare(registry, request, mode="cpu"):
    x = decode_input(registry, request)
    input_hash = canonical_sha256({"shape": list(x.shape), "values": x.tolist(), "dtype": str(x.dtype)})
    results = []
    for method in METHODS:
        spec = next(
            m
            for m in registry.models.values()
            if m["dataset_id"] == request["dataset_id"]
            and m["family"] == request["family"]
            and m["implementation"] == method
        )
        try:
            config, adapter_spec, adapter, weights = load_model(registry, spec)
            if mode == "local_gpu" and method != "scratch":
                from apps.api.v3.native import invoke_native

                raw, elapsed, backend, device = invoke_native(registry, spec, x)
            else:
                model = NumpyNetwork(config["plan"], weights)
                started = time.perf_counter()
                raw = model.forward(x)
                elapsed, backend, device = (time.perf_counter() - started) * 1000, "numpy", "cpu"
            row = {
                "implementation": method,
                "status": "succeeded",
                "model_id": spec["model_id"],
                "actual_device": device,
                "actual_backend": backend,
                "inference_ms": elapsed,
                "artifact_sha256": spec["checkpoint"]["sha256"],
                "prediction": prediction_from(raw, config, adapter, adapter_spec),
                "error": None,
                "input_sha256": input_hash,
                "comparison_group_sha256": spec["comparison_group_sha256"],
            }
            validate_document("api#result", row)
        except (OSError, ValueError, RuntimeError, ImportError, KeyError):
            row = empty_slot(method, input_hash, "artifact_or_backend_unavailable")
        results.append(row)
    succeeded = sum(r["status"] == "succeeded" for r in results)
    groups = {r["comparison_group_sha256"] for r in results}
    valid = succeeded == 3 and len(groups) == 1 and None not in groups
    return {
        "status": "succeeded" if succeeded == 3 else "partial_failed" if succeeded else "failed",
        "results": results,
        "input_sha256": input_hash,
        "comparison_valid": valid,
        "comparison_blockers": [] if valid else ["unavailable_or_unmatched"],
        "trace_ids": [],
        "metric_artifacts": [],
    }, {
        "scope": "inference_only",
        "serving_mode": mode,
        "warning": "Academic retrospective demo; not diagnosis, investment advice or current appraisal. NumPy timing is not native framework timing.",
        "historical_test_evaluation_executed": False,
    }


def compare(registry, request, job_id, mode="cpu"):
    if request["chapter"] < 5:
        return neural_compare(registry, request, mode)
    decode_input(registry, request)
    if request["chapter"] == 5:
        from apps.api.v3.rag_streaming import load_domain_bundle
        from src.ch05_knowledge_rag.service import KgRagService

        domain = {"ch5_medquad_diabetes": "medical", "ch5_finqa": "finance"}.get(request["dataset_id"])
        output = KgRagService(
            loader=lambda: load_domain_bundle(registry, domain, request["input"]["text"])
        ).compare(request)
        job = output.pop("job")
        if request["dataset_id"] == "ch5_wikidata_subgraphs":
            from src.ch05_knowledge_rag.structural import inspect_entity

            output["entity"] = inspect_entity(request["input"]["text"])
        return job, output
    from src.ch06_multi_agent.executor import ProcessExecutor
    from src.ch06_multi_agent.service import AgentService
    from src.ch06_multi_agent.tools import ToolCatalog

    document = registry.json(registry.document["agent_catalog"])
    tools = ToolCatalog(document)
    service = AgentService(ProcessExecutor(tools.call), registry.document["agent_taskset_sha256"])
    output = service.compare(
        {
            "schema_version": "3.0.0",
            "dataset_id": request["dataset_id"],
            "question": request["input"]["text"],
            "variants": request["implementations"],
        }
    )
    results, traces = [], {}
    digest = canonical_sha256(request["input"])
    for method, result in output["outputs"].items():
        trace = result["trace"]
        trace["trace_id"] = "trace_" + job_id[4:] + "_" + method.lower()
        validate_document("agent", trace)
        traces[trace["trace_id"]] = trace
        ok = trace["status"] in {"succeeded", "abstained"}
        results.append(
            {
                "implementation": method,
                "status": "succeeded" if ok else "failed",
                "model_id": request["dataset_id"] + "_" + method.lower(),
                "actual_device": "cpu" if ok else "not_run",
                "actual_backend": "numpy" if ok else "not_run",
                "inference_ms": trace["latency_ms"] if ok else None,
                "artifact_sha256": registry.document["agent_catalog"]["sha256"] if ok else None,
                "prediction": {
                    "kind": "answer",
                    "text": trace["answer"],
                    "abstained": trace["status"] != "succeeded",
                    "citations": trace["citations"],
                }
                if ok
                else None,
                "error": None if ok else {"code": "tool_unavailable", "message": "Agent tool unavailable"},
                "input_sha256": digest,
                "comparison_group_sha256": registry.document["agent_taskset_sha256"],
            }
        )
    ok_count = sum(r["status"] == "succeeded" for r in results)
    return {
        "status": "succeeded" if ok_count == 3 else "partial_failed" if ok_count else "failed",
        "results": results,
        "comparison_valid": ok_count == 3,
        "comparison_blockers": [] if ok_count == 3 else ["agent_failed"],
        "trace_ids": list(traces),
        "metric_artifacts": [],
        "input_sha256": digest,
    }, {
        "traces": traces,
        "agent_outputs": output,
        "warning": "ID-bound deterministic tools, not general reasoning. Node timing0 may be uninstrumented; no clinical/financial advice.",
    }
