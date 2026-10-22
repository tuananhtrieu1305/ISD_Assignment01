"""Offline Phase 22 specification guards, not a training or TEST executor.

jsonschema/referencing are already pinned by the shared uv lock. No network fetch
is registered: unknown external schema URIs fail closed.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime
from functools import lru_cache
from itertools import pairwise
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "src/common/schemas/v3"
PROTOCOL = ROOT / "experiments/configs/v3/protocol_v3.json"
REQUIREMENT_IDS = {f"REQ-{number:02}" for number in range(1, 55)}


class ContractError(ValueError):
    """A structural or semantic specification violation."""


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def canonical_sha256(value) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def load_schemas() -> dict:
    schemas = {
        path.name.removesuffix(".schema.json"): read_json(path) for path in SCHEMAS.glob("*.schema.json")
    }
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    return schemas


def _finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ContractError("All numeric values must be finite; undefined metrics use null with a reason")
    if isinstance(value, dict):
        for child in value.values():
            _finite(child)
    elif isinstance(value, list):
        for child in value:
            _finite(child)


def _backend(document):
    allowed = {"scratch": {"numpy"}, "keras": {"tensorflow", "torch"}, "pytorch": {"torch"}}
    if document["backend"] not in allowed[document["implementation"]]:
        raise ContractError("implementation/backend mismatch")


def _dataset_family(document):
    protocol = read_json(PROTOCOL)
    dataset = next((row for row in protocol["datasets"] if row["dataset_id"] == document["dataset_id"]), None)
    if dataset is None or dataset["chapter"] != protocol["families"][document["family"]]["chapter"]:
        raise ContractError("Model family/dataset mismatch")


def _time(value):
    return datetime.fromisoformat(value)


def _model(document):
    _backend(document)
    _dataset_family(document)
    policy = read_json(PROTOCOL)
    layers = document["layers"]
    eligible = [
        layer
        for layer in layers
        if layer["kind"] in policy["layer_policy"]["counted_kinds"] and layer["parameter_count"] > 0
    ]
    expected = policy["families"][document["family"]]
    if len(eligible) < expected["minimum_learnable_layers"]:
        raise ContractError("Too few learnable layers; pooling/normalization/time steps do not count")
    if [layer["kind"] for layer in eligible] != expected["blocks"]:
        raise ContractError("Learnable layer composition differs from the locked reference architecture")
    if sum(layer["parameter_count"] for layer in layers) != document["parameter_count"]:
        raise ContractError("Total parameter count does not match layers")
    functions = {function["id"]: function for function in document["functions"]}
    if len(functions) != len(document["functions"]) or len({layer["id"] for layer in layers}) != len(layers):
        raise ContractError("Duplicate function/layer IDs")
    if any(name not in functions for name in document["composition"]):
        raise ContractError("Composition references a missing function")
    for layer in layers:
        if layer["function_id"] not in functions:
            raise ContractError("Layer references a missing function")
    if document["family"] in {"rnn", "lstm"} and not document["recurrent_unroll"]:
        raise ContractError("Recurrent model needs a time/layer unroll explanation")


def _split(document):
    partitions = document["partitions"]
    if {part["name"] for part in partitions} != {"train", "validation", "test"}:
        raise ContractError("Each partition must occur exactly once")
    if document["method"] == "temporal":
        for part in partitions:
            if (
                not part["target_start"]
                or not part["target_end"]
                or _time(part["target_start"]) > _time(part["target_end"])
            ):
                raise ContractError("Temporal partition needs a valid target time range")
        by_name = {part["name"]: part for part in partitions}
        times = [
            (_time(by_name[name]["target_start"]), _time(by_name[name]["target_end"]))
            for name in ("train", "validation", "test")
        ]
        if any(left[1] >= right[0] for left, right in pairwise(times)):
            raise ContractError("Temporal target time ranges overlap")


def _run(document):
    _backend(document)
    _dataset_family(document)
    if document["track"] == "matched_subset" and not document["subset_sha256"]:
        raise ContractError("Matched-subset run needs its selected train ID hash")
    if document["split"] == "test" and not document["test_seal_id"]:
        raise ContractError("TEST metrics require a test seal ID")
    if _time(document["started_at"]) > _time(document["finished_at"]):
        raise ContractError("Run finish precedes start")
    efficiency = document["efficiency"]
    if efficiency["inference_p95_ms"] < efficiency["inference_p50_ms"]:
        raise ContractError("Inference p95 cannot be below p50")
    if document["device"] == "cpu" and efficiency["peak_vram_bytes"] != 0:
        raise ContractError("CPU run cannot claim GPU allocator memory")
    for metric in document["metrics"]:
        if (metric["value"] is None) != bool(metric["undefined_reason"]):
            raise ContractError("Undefined metric must use null and an explicit reason")


def _dataset(document):
    if document["status"] == "ready":
        if document["source"]["license_status"] != "approved":
            raise ContractError("Ready dataset requires approved license/access")
        if document["logical_size"]["records"] is None:
            raise ContractError("Ready dataset requires measured logical size")
        if document["kind"] != "task_view" and not document["files"]:
            raise ContractError("Ready dataset needs file hashes")
    if document["kind"] == "task_view" and not document["parent_dataset_ids"]:
        raise ContractError("Task view must reference source datasets")


def _seal(document):
    expected = 1 if document["state"] in {"evaluating", "evaluated", "failed_sealed"} else 0
    if document["evaluation_count"] != expected:
        raise ContractError("Seal state/evaluation count mismatch")
    if len(set(document["approved_run_ids"])) != len(document["approved_run_ids"]):
        raise ContractError("Seal approved run IDs must be unique")


def _artifact(document):
    loaders = {
        "npz": "numpy_no_pickle",
        "keras": "keras_safe_mode",
        "torch_state_dict": "torch_weights_only",
        "legacy_trusted_joblib": "legacy_allowlist",
    }
    expected = loaders.get(document["serialization"], "data_only")
    if document["load_policy"] != expected:
        raise ContractError("Artifact serialization/load policy mismatch")
    if document["kind"] == "checkpoint" and not document["cpu_loadable"]:
        raise ContractError("Deployable checkpoint must support CPU-safe load")


def _api(document):
    datasets = {row["dataset_id"]: row for row in read_json(PROTOCOL)["datasets"]}
    dataset = datasets.get(document["dataset_id"])
    if not dataset or dataset["chapter"] != document["chapter"]:
        raise ContractError("Request dataset/chapter mismatch")
    family = document["family"]
    chapter_families = {2: {"mlp"}, 3: {"cnn"}, 4: {"rnn", "lstm"}, 5: {"kg_rag"}, 6: {"multi_agent"}}
    if family not in chapter_families[document["chapter"]]:
        raise ContractError("Request family/chapter mismatch")
    expected = (
        ["B0", "B1", "B2", "B3", "B4"]
        if family == "kg_rag"
        else ["A0", "A1", "A2"]
        if family == "multi_agent"
        else ["scratch", "keras", "pytorch"]
    )
    if document["implementations"] != expected:
        raise ContractError("Request implementations do not match family")
    kind = document["input"]["kind"]
    if kind != {2: "tabular", 3: "image", 4: "sequence", 5: "question", 6: "question"}[document["chapter"]]:
        raise ContractError("Request payload kind does not match chapter")
    if kind == "sequence" and len({len(row) for row in document["input"]["values"]}) != 1:
        raise ContractError("Sequence rows must have a consistent feature width")


def _job(document):
    results = document["results"]
    expected = (
        {"B0", "B1", "B2", "B3", "B4"}
        if document["family"] == "kg_rag"
        else {"A0", "A1", "A2"}
        if document["family"] == "multi_agent"
        else {"scratch", "keras", "pytorch"}
    )
    names = [result["implementation"] for result in results]
    if len(names) != len(set(names)) or any(name not in expected for name in names):
        raise ContractError("Duplicate or inapplicable result slot")
    if document["status"] in {"succeeded", "partial_failed", "failed"} and set(names) != expected:
        raise ContractError("Terminal job must report every implementation, including unavailable slots")
    all_success = len(results) == len(expected) and all(result["status"] == "succeeded" for result in results)
    if any(result["input_sha256"] != document["input_sha256"] for result in results):
        raise ContractError("Job result input hash differs from the shared input hash")
    groups = {result["comparison_group_sha256"] for result in results}
    if document["comparison_valid"] and (len(groups) != 1 or None in groups):
        raise ContractError("Models do not belong to the same comparison group")
    if document["comparison_valid"] and (not all_success or document["comparison_blockers"]):
        raise ContractError("Incomplete or blocked comparison cannot be valid")
    for result in results:
        if result["status"] == "succeeded" and (
            result["prediction"] is None
            or result["error"] is not None
            or result["actual_device"] == "not_run"
            or not result["artifact_sha256"]
        ):
            raise ContractError("Successful result needs prediction, actual device and artifact hash")
        if result["status"] != "succeeded" and (result["error"] is None or result["prediction"] is not None):
            raise ContractError("Failed result needs explicit error, not a fabricated prediction")
        prediction = result["prediction"]
        if (
            prediction
            and prediction["kind"] == "classification"
            and not math.isclose(sum(row["value"] for row in prediction["probabilities"]), 1.0, abs_tol=1e-5)
        ):
            raise ContractError("Classification probabilities must sum to one")


def _agent(document):
    seen = set()
    agents = set()
    for node in document["nodes"]:
        if node["node_id"] in seen or not set(node["parent_ids"]).issubset(seen):
            raise ContractError("Agent trace must be acyclic and topologically ordered")
        seen.add(node["node_id"])
        agents.add(node["agent"])
    required = {
        "A0": {"direct"},
        "A1": {"router", "specialist"},
        "A2": {"router", "specialist", "verifier", "reporter"},
    }
    if not agents.issubset(required[document["variant"]]):
        raise ContractError("Agent trace uses a role outside its benchmark variant")
    if document["status"] == "succeeded" and not required[document["variant"]].issubset(agents):
        raise ContractError("Agent trace omits required roles")


def _agent_task(document):
    dataset = next(
        (row for row in read_json(PROTOCOL)["datasets"] if row["dataset_id"] == document["dataset_id"]), None
    )
    if not dataset or dataset["chapter"] != 6:
        raise ContractError("Agent task must use a chapter6 task-view dataset")


def validate_document(name: str, document: dict, *, publish: bool = False) -> None:
    schema_name, _, definition = name.partition("#")
    schemas = load_schemas()
    if schema_name not in schemas or (definition and definition not in schemas[schema_name].get("$defs", {})):
        raise ContractError(f"Unknown schema: {name}")
    _finite(document)
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    )
    schema = (
        {"$ref": schemas[schema_name]["$id"] + f"#/$defs/{definition}"}
        if definition
        else schemas[schema_name]
    )
    validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: error.json_path)
    if errors:
        raise ContractError("; ".join(f"{error.json_path}: {error.message}" for error in errors[:5]))
    if publish and document.get("evidence_kind") == "synthetic_fixture":
        raise ContractError("Cannot publish synthetic fixture as measured evidence")
    checks = {
        "dataset": _dataset,
        "split": _split,
        "model": _model,
        "run": _run,
        "seal": _seal,
        "artifact": _artifact,
        "api": _api,
        "api#job": _job,
        "api#agent_task": _agent_task,
        "agent": _agent,
    }
    if name in checks:
        checks[name](document)


def check_seal_transition(seal: dict, target: str, *, config_sha256: str) -> None:
    """Validate a proposed transition; do not change files or authorize TEST execution."""
    validate_document("seal", seal)
    if seal["state"] in {"evaluated", "failed_sealed"}:
        raise ContractError("TEST is sealed; do not reopen it")
    if config_sha256 != seal["locked_config_sha256"]:
        raise ContractError("TEST config hash changed")
    allowed = {"draft": {"locked"}, "locked": {"evaluating"}, "evaluating": {"evaluated", "failed_sealed"}}
    if target not in allowed.get(seal["state"], set()):
        raise ContractError("Invalid TEST seal transition")


def _refs(value):
    if isinstance(value, dict):
        if "$ref" in value:
            yield value["$ref"]
        for child in value.values():
            yield from _refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from _refs(child)


def audit_specification(root: Path) -> dict:
    """Audit frozen design documents; never read dataset contents or execute training."""
    errors = []
    result = {"errors": errors, "requirements": 0, "datasets": 0}
    required = [
        "docs/srs_v3.md",
        "docs/traceability_v3.csv",
        "docs/report_style_v3.md",
        "docs/architecture_v3.mmd",
        "docs/risk_register_v3.csv",
        "docs/adr/0001-v3-sources-and-runtime.md",
        "docs/adr/0002-v3-comparison-and-seals.md",
        "docs/adr/0003-v3-api-and-serving.md",
        "docs/adr/0004-v3-formula-minimal-report.md",
        "experiments/configs/v3/protocol_v3.json",
        "report/outline_v3.json",
        "docs/contracts/v3/openapi.json",
    ]
    for relative in required:
        if not (root / relative).is_file():
            errors.append(f"Missing required specification: {relative}")
    if errors:
        return result
    with (root / "docs/traceability_v3.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    result["requirements"] = len(rows)
    if {row["requirement_id"] for row in rows} != REQUIREMENT_IDS or len(rows) != len(REQUIREMENT_IDS):
        errors.append("Requirement IDs are missing, duplicated or unknown")
    for row in rows:
        if not all(
            row.get(key)
            for key in (
                "origin",
                "requirement",
                "phases",
                "spec_artifact",
                "planned_artifact",
                "acceptance_test",
                "implementation_status",
            )
        ):
            errors.append(f"Incomplete traceability: {row.get('requirement_id')}")
        if not (root / row["spec_artifact"]).is_file():
            errors.append(f"Missing specification artifact for {row['requirement_id']}")
        if any(not token.isdigit() or not 20 <= int(token) <= 35 for token in row["phases"].split(";")):
            errors.append(f"Invalid phase mapping for {row['requirement_id']}")
    protocol = read_json(root / "experiments/configs/v3/protocol_v3.json")
    outline = read_json(root / "report/outline_v3.json")
    datasets = protocol["datasets"]
    result["datasets"] = len(datasets)
    if len(datasets) != 18 or len({row["dataset_id"] for row in datasets}) != 18:
        errors.append("Expected 18 unique dataset/benchmark/view IDs")
    if [row["chapter"] for row in outline["chapters"]] != list(range(1, 7)):
        errors.append("Outline must contain exactly six chapters")
    for chapter in outline["chapters"]:
        expected = {row["dataset_id"] for row in datasets if row["chapter"] == chapter["chapter"]}
        if len(expected) != 3 or set(chapter["dataset_ids"]) != expected:
            errors.append(f"Dataset/outline mismatch: chapter {chapter['chapter']}")
        deploy = [section for section in chapter["sections"] if section["kind"] == "deployment"]
        if chapter["chapter"] >= 2 and (len(deploy) != 1 or deploy[0] != chapter["sections"][-1]):
            errors.append("Deployment must be the last short section, never its own chapter")
    if protocol["ch5"]["new_test_evaluation_allowed"] or protocol["ch5"]["test_run_count"] != 1:
        errors.append("Ch5 TEST must remain sealed at run_count=1")
    if protocol["comparison"]["training_runs_required"] != 4 * 3 * 3 * len(protocol["seeds"]["stability"]):
        errors.append("Neural run matrix count mismatch")
    api_path = root / "docs/contracts/v3/openapi.json"
    api = read_json(api_path)
    if api.get("openapi") != "3.1.1":
        errors.append("OpenAPI version must be explicit")
    for reference in _refs(api):
        relative, _, fragment = reference.partition("#")
        target = (api_path.parent / relative).resolve() if relative else api_path.resolve()
        try:
            target.relative_to(root.resolve())
            content = read_json(target)
            for token in filter(None, fragment.split("/")):
                content = content[token.replace("~1", "/").replace("~0", "~")]
        except (ValueError, KeyError, OSError) as error:
            errors.append(f"Unresolved local API reference {reference}: {error}")
    return result
