"""Generate initialized architecture contracts, never trained-model claims."""

from __future__ import annotations

import csv
import io
import json

from jsonschema import Draft202012Validator

from src.common.artifact_core import code_fingerprint, sha256_file
from src.common.contracts import PROTOCOL, ROOT, canonical_sha256, read_json
from src.common.data_access import DatasetView
from src.common.eda_artifacts import reference, write_json
from src.common.model_core import build_plan, canonical_weights, make_contract, render_functions

BASE = ROOT / "artifacts/manifests/phase25"
FUNCTIONS = ROOT / "report/references/functions/v3"
CORE_FILES = [
    f"src/common/{name}.py"
    for name in (
        "artifact_core",
        "backend_models",
        "data_access",
        "device_core",
        "metric_core",
        "model_core",
        "native_training",
        "numpy_engine",
        "parity",
        "tensor_adapters",
        "training_core",
    )
]


def validate_adapter(document):
    schema = read_json(ROOT / "src/common/schemas/phase25/tensor_adapter.schema.json")
    errors = list(Draft202012Validator(schema).iter_errors(document))
    if errors:
        raise ValueError(errors[0].message)
    classes = document["class_names"]
    mapping = document["source_label_to_id"]
    if classes and (
        set(classes) != {str(i) for i in range(len(classes))}
        or set(mapping.values()) != set(range(len(classes)))
    ):
        raise ValueError("Label mapping is not contiguous/bijective")


def architecture_for(view, family):
    if view.kind == "image":
        shape = view.preprocessing["input_shape_hwc"]
        outputs = view.spec["class_count"]
    elif view.kind == "timeseries":
        shape = [view.spec["lookback"], view.preprocessing["output_width"]]
        outputs = len(view.spec["horizons"])
    else:
        shape = [view.preprocessing["output_width"]]
        outputs = 1
    return build_plan(family, shape, outputs)


def prepare():
    if (BASE / "core_lock.json").exists():
        from scripts.verify_phase25 import verify

        return verify()
    protocol = read_json(PROTOCOL)
    entries = []
    adapters = []
    summary = []
    code_sha = code_fingerprint(ROOT, CORE_FILES)
    for row in protocol["datasets"]:
        if row["chapter"] not in {2, 3, 4}:
            continue
        view = DatasetView(row["dataset_id"])
        adapter = view.contract()
        validate_adapter(adapter)
        adapter_path = BASE / "adapters" / f"{view.dataset_id}.json"
        write_json(adapter_path, adapter)
        adapters.append(reference(adapter_path))
        for family in {2: ["mlp"], 3: ["cnn"], 4: ["rnn", "lstm"]}[row["chapter"]]:
            plan = architecture_for(view, family)
            Draft202012Validator(
                read_json(ROOT / "src/common/schemas/phase25/training_plan.schema.json")
            ).validate(plan)
            key = f"{view.dataset_id}_{family}"
            plan_path = BASE / "plans" / f"{key}.json"
            write_json(plan_path, plan)
            init_hashes = {
                str(seed): canonical_sha256({k: v.tolist() for k, v in canonical_weights(plan, seed).items()})
                for seed in protocol["seeds"]["stability"]
            }
            group = {
                "dataset_id": view.dataset_id,
                "family": family,
                "plan_sha256": canonical_sha256(plan),
                "adapter": reference(adapter_path),
                **view.provenance,
                "protocol_sha256": sha256_file(PROTOCOL),
            }
            group_hash = canonical_sha256(group)
            config = {
                "phase": 25,
                "lifecycle": "initialized_only",
                "inference_ready": False,
                "dataset_id": view.dataset_id,
                "family": family,
                "plan": reference(plan_path),
                "adapter": reference(adapter_path),
                "comparison_group_sha256": group_hash,
                "canonical_initial_weights_by_seed_sha256": init_hashes,
                "provenance": view.provenance,
                "code_sha256": code_sha,
                "protocol_sha256": sha256_file(PROTOCOL),
                "environment_sha256": sha256_file(ROOT / "uv.lock"),
                "training": protocol["training"],
                "seeds": protocol["seeds"]["stability"],
                "real_dataset_training_executed": False,
                "test_evaluation_executed": False,
            }
            config_path = BASE / "configs" / f"{key}.json"
            write_json(config_path, config)
            for implementation in protocol["implementation_order"]:
                provenance = {
                    "dataset_id": view.dataset_id,
                    "config_sha256": sha256_file(config_path),
                    "dataset_sha256": view.provenance["dataset_sha256"],
                    "comparison_group_sha256": group_hash,
                    "preprocessing": {k: adapter["preprocessing"][k] for k in ("path", "sha256")},
                }
                contract = make_contract(plan, implementation, "measured", provenance)
                directory = BASE / "contracts" / contract["model_id"]
                contract_path = directory / "model_contract.json"
                write_json(contract_path, contract)
                rendered = render_functions(contract)
                write_json(
                    directory / "functions.json", {k: v for k, v in rendered.items() if k != "markdown"}
                )
                FUNCTIONS.mkdir(parents=True, exist_ok=True)
                (FUNCTIONS / f"{contract['model_id']}.md").write_text(
                    rendered["markdown"], encoding="utf-8", newline="\n"
                )
                buffer = io.StringIO(newline="")
                writer = csv.writer(buffer, lineterminator="\n")
                writer.writerow(
                    [
                        "function",
                        "signature",
                        "role",
                        "input_shape",
                        "output_shape",
                        "parameters",
                        "corner_case",
                        "scratch",
                        "keras",
                        "pytorch",
                    ]
                )
                for f in rendered["functions"]:
                    writer.writerow(
                        [
                            f["id"],
                            f["signature"],
                            f["role"],
                            f["input_shape"],
                            f["output_shape"],
                            f["parameters"],
                            f["corner_case"],
                            *f["mapping"].values(),
                        ]
                    )
                (directory / "functions.csv").write_text(buffer.getvalue(), encoding="utf-8", newline="\n")
                entries.append(
                    {
                        "model_id": contract["model_id"],
                        "dataset_id": view.dataset_id,
                        "family": family,
                        "implementation": implementation,
                        "lifecycle": "initialized_only",
                        "inference_ready": False,
                        "contract": reference(contract_path),
                        "config": reference(config_path),
                        "adapter": reference(adapter_path),
                    }
                )
            summary.append(
                {
                    "dataset_id": view.dataset_id,
                    "family": family,
                    "input_shape": plan["input_shape"],
                    "output_shape": plan["output_shape"],
                    "learnable_layers": len([s for s in contract["layers"] if s["parameter_count"]]),
                    "parameter_count": contract["parameter_count"],
                    "initial_weight_hashes": init_hashes,
                }
            )
    registry = {
        "phase": 25,
        "lifecycle": "initialized_only",
        "inference_ready": False,
        "adapters": adapters,
        "models": entries,
        "architecture_summary": summary,
        "code_sha256": code_sha,
        "code_files": [{"path": p, "sha256": sha256_file(ROOT / p)} for p in CORE_FILES],
        "real_dataset_training_executed": False,
        "test_evaluation_executed": False,
    }
    write_json(BASE / "initialized_contract_registry.json", registry)
    return {
        "status": "PASS",
        "adapters": len(adapters),
        "model_contracts": len(entries),
        "architecture_plans": len(summary),
        "real_dataset_training_executed": False,
        "test_evaluation_executed": False,
    }


def main():
    print(json.dumps(prepare(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
