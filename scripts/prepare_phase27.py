"""Freeze 27 CNN +9 majority runs before any real training."""

import json

from src.ch03_cnn.image_cache import development_cache
from src.ch03_cnn.protocol import (
    BASE,
    DATASETS,
    IMPLEMENTATIONS,
    SEEDS,
    SOURCE_FILES,
    code_info,
    ref,
    run_ids,
)
from src.common.artifact_core import write_once
from src.common.contracts import PROTOCOL, ROOT, canonical_sha256, read_json
from src.common.model_core import build_plan, canonical_weights, make_contract, render_functions


def prepare():
    if (BASE / "release.json").exists():
        from src.ch03_cnn.protocol import check_sources

        return check_sources()
    for method in IMPLEMENTATIONS:
        if read_json(BASE / f"preflight_{method}.json")["status"] != "PASS":
            raise ValueError("CNN feasibility/parity probe missing")
    protocol, code, entries = read_json(PROTOCOL), code_info(), []
    for dataset in DATASETS:
        cache, view = development_cache(dataset)
        write_once(
            BASE / "data" / f"{dataset}.json",
            {
                "dataset_id": dataset,
                "cache_manifest": ref(cache.root / "manifest.json"),
                "provenance": view.provenance,
                "train_count": len(view.ids("train")),
                "validation_count": len(view.ids("validation")),
                "test_accessed": False,
            },
        )
        write_once(BASE / "adapters" / f"{dataset}.json", view.contract())
        plan = build_plan("cnn", view.preprocessing["input_shape_hwc"], view.spec["class_count"])
        for seed in SEEDS:
            config = {
                "phase": 27,
                "dataset_id": dataset,
                "seed": seed,
                "task": "multiclass",
                "plan": plan,
                "track": "matched_subset",
                "provenance": view.provenance,
                "adapter": ref(BASE / "adapters" / f"{dataset}.json"),
                "code": code,
                "environment_sha256": ref(ROOT / "uv.lock")["sha256"],
                "protocol_sha256": ref(PROTOCOL)["sha256"],
                "training": {**protocol["training"], "batch_size": protocol["training"]["batch_size"]["cnn"]},
                "canonical_initial_weights_sha256": canonical_sha256(
                    {k: v.tolist() for k, v in canonical_weights(plan, seed).items()}
                ),
                "class_weights": view.adapter_contract["class_weights_by_id"]
                if dataset == "ch3_idrid"
                else None,
                "augmentation": "none; inherited frozen Phase24 preprocessing, any extra track needs new config",
                "class_names": view.adapter_contract["class_names"],
                "cache_manifest": ref(cache.root / "manifest.json"),
                "majority_policy": "argmax unweighted matched TRAIN class counts; one-hot probabilities; no fitting to validation/TEST",
                "execution_policy": {
                    "scratch": "NumPy CPU manual conv/pool/backward/Adam eager",
                    "keras": "Keras TensorFlow CUDA tf.function canonical Adam, no XLA",
                    "pytorch": "PyTorch native CUDA eager Adam",
                },
                "efficiency_policy": "Train wall includes validation/batch conversion/progress I/O; inference batch1/5warmup/30repeat model+transfer, preprocessing separate; process-lifetime RSS; framework allocator VRAM",
                "saliency_policy": "seed42 first fixed TRAIN image, gradient of predicted logit; illustration only, not clinical interpretation",
                "test_policy": "Full TEST once, only after all validation-selected configurations/checkpoints/evaluator approved; no retry/tuning",
            }
            path = BASE / "configs" / f"{dataset}_s{seed}.json"
            write_once(path, config)
            group = canonical_sha256(config)
            for method in (*IMPLEMENTATIONS, "majority"):
                run = f"{dataset}_{'cnn_' + method if method in IMPLEMENTATIONS else method}_s{seed}"
                folder = BASE / "runs" / run
                if method in IMPLEMENTATIONS:
                    contract = make_contract(
                        plan,
                        method,
                        "measured",
                        {
                            "dataset_id": dataset,
                            "config_sha256": ref(path)["sha256"],
                            "dataset_sha256": view.provenance["dataset_sha256"],
                            "comparison_group_sha256": group,
                            "preprocessing": view.contract()["preprocessing"],
                        },
                    )
                    contract["model_id"] = run
                    rendered = render_functions(contract)
                    write_once(
                        folder / "functions.json", {k: v for k, v in rendered.items() if k != "markdown"}
                    )
                else:
                    contract = {
                        "schema_version": "phase27.majority.1",
                        "model_id": run,
                        "dataset_id": dataset,
                        "family": "classical",
                        "method": method,
                        "output_classes": view.spec["class_count"],
                        "config": ref(path),
                        "provenance": view.provenance,
                        "layer_count_applicable": False,
                    }
                write_once(folder / "model_contract.json", contract)
                entries.append(
                    {
                        "run_id": run,
                        "dataset_id": dataset,
                        "method": method,
                        "seed": seed,
                        "config": ref(path),
                        "model_contract": ref(folder / "model_contract.json"),
                        "comparison_group_sha256": group,
                    }
                )
    write_once(
        BASE / "release.json",
        {
            "phase": 27,
            "status": "declared_before_training",
            "code": code,
            "source_files": [ref(ROOT / p) for p in SOURCE_FILES],
            "protocol": ref(PROTOCOL),
            "environment": ref(ROOT / "uv.lock"),
            "phase25_lock": ref(ROOT / "artifacts/manifests/phase25/core_lock.json"),
            "runs": entries,
            "expected_run_ids": run_ids(),
            "test_evaluation_executed": False,
        },
    )
    return {"status": "PASS", "neural_runs": 27, "majority_runs": 9, "test_accessed": False}


if __name__ == "__main__":
    print(json.dumps(prepare(), ensure_ascii=False, indent=2))
