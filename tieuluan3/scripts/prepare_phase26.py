"""Predeclare all Chapter2 runs before training or opening TEST."""

from __future__ import annotations

import json

from src.ch02_ml.protocol import (
    BASE,
    DATASETS,
    IMPLEMENTATIONS,
    SEEDS,
    SOURCE_FILES,
    baseline_names,
    cache_data,
    code_info,
    dataset_spec,
    ref,
    run_ids,
    task_for,
)
from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import PROTOCOL, ROOT, canonical_sha256, read_json
from src.common.data_access import DatasetView
from src.common.model_core import build_plan, canonical_weights, make_contract, render_functions


def prepare():
    if (BASE / "release.json").exists():
        from src.ch02_ml.protocol import check_sources

        return check_sources()
    protocol = read_json(PROTOCOL)
    code = code_info()
    entries = []
    for dataset in DATASETS:
        cache_data(dataset)
        view = DatasetView(dataset)
        spec = dataset_spec(dataset)
        write_once(BASE / "adapters" / f"{dataset}.json", view.contract())
        plan = build_plan("mlp", [view.preprocessing["output_width"]], 1)
        for seed in SEEDS:
            config = {
                "phase": 26,
                "dataset_id": dataset,
                "seed": seed,
                "task": task_for(dataset),
                "plan": plan,
                "track": "matched_subset",
                "provenance": view.provenance,
                "adapter": ref(BASE / "adapters" / f"{dataset}.json"),
                "code": code,
                "environment_sha256": sha256_file(ROOT / "uv.lock"),
                "protocol_sha256": sha256_file(PROTOCOL),
                "training": {**protocol["training"], "batch_size": protocol["training"]["batch_size"]["mlp"]},
                "canonical_initial_weights_sha256": canonical_sha256(
                    {k: v.tolist() for k, v in canonical_weights(plan, seed).items()}
                ),
                "class_weights": view.preprocessing.get("class_weights"),
                "classification_threshold": 0.5,
                "positive_when": "p > threshold, ties class 0; inherited Phase25 convention",
                "baselines": spec["baselines"],
                "forest": {"n_estimators": 200, "max_depth": 12, "min_samples_leaf": 5, "n_jobs": 2},
                "logistic": {"C": 1.0, "solver": "lbfgs", "max_iter": 1000},
                "ridge": {"alpha": 1.0},
                "calibration": {"bins": 10, "refit": False},
                "group_diagnostics": {
                    "ch2_cdc_diabetes": "sex source codes 0/1; descriptive, not clinical fairness certification",
                    "ch2_bank_marketing": "age <60 versus >=60, descriptive demographic proxy",
                    "ch2_ames_housing": "year_built <1980 versus >=1980, structural error analysis not protected-group fairness",
                }[dataset],
                "test_policy": "Only after every validation selection/checkpoint/config/code is frozen; all approved models evaluated once; no TEST tuning",
                "efficiency_policy": "Train wall includes validation/checkpoint progress I/O. Inference batch1/5warmup/30repeat includes host transfer; preprocessing reported separately. RAM is isolated process high-water RSS.",
                "execution_policy": {
                    "scratch": "NumPy CPU eager",
                    "pytorch": "native CUDA eager",
                    "keras": "Keras/TensorFlow CUDA tf.function, canonical Adam, XLA disabled",
                },
            }
            config_path = BASE / "configs" / f"{dataset}_s{seed}.json"
            write_once(config_path, config)
            group = canonical_sha256(config)
            for method in (*IMPLEMENTATIONS, *baseline_names(dataset)):
                run = f"{dataset}_{'mlp_' + method if method in IMPLEMENTATIONS else method}_s{seed}"
                folder = BASE / "runs" / run
                if method in IMPLEMENTATIONS:
                    contract = make_contract(
                        plan,
                        method,
                        "measured",
                        {
                            "dataset_id": dataset,
                            "config_sha256": sha256_file(config_path),
                            "dataset_sha256": view.provenance["dataset_sha256"],
                            "comparison_group_sha256": group,
                            "preprocessing": view.contract()["preprocessing"],
                        },
                    )
                    contract["model_id"] = run
                    rendered = render_functions(contract)
                    write_once(folder / "model_contract.json", contract)
                    write_once(
                        folder / "functions.json", {k: v for k, v in rendered.items() if k != "markdown"}
                    )
                    write_once(
                        folder / "initialization.json",
                        {
                            "seed": seed,
                            "canonical_weights_sha256": config["canonical_initial_weights_sha256"],
                            "lifecycle": "untrained",
                        },
                    )
                else:
                    write_once(
                        folder / "model_contract.json",
                        {
                            "schema_version": "phase26.classical.1",
                            "model_id": run,
                            "dataset_id": dataset,
                            "family": "classical",
                            "method": method,
                            "backend": "scikit_learn",
                            "input_shape": ["batch", view.preprocessing["output_width"]],
                            "output_shape": ["batch", 2 if task_for(dataset) == "binary" else 1],
                            "layer_count_applicable": False,
                            "config": ref(config_path),
                            "provenance": view.provenance,
                        },
                    )
                entries.append(
                    {
                        "run_id": run,
                        "dataset_id": dataset,
                        "method": method,
                        "seed": seed,
                        "config": ref(config_path),
                        "model_contract": ref(folder / "model_contract.json"),
                        "comparison_group_sha256": group,
                    }
                )
    release = {
        "phase": 26,
        "status": "declared_before_training",
        "code": code,
        "source_files": [ref(ROOT / path) for path in SOURCE_FILES],
        "protocol": ref(PROTOCOL),
        "environment": ref(ROOT / "uv.lock"),
        "phase25_lock": ref(ROOT / "artifacts/manifests/phase25/core_lock.json"),
        "runs": entries,
        "expected_run_ids": run_ids(),
        "test_evaluation_executed": False,
    }
    write_once(BASE / "release.json", release)
    return {
        "status": "PASS",
        "declared_runs": len(entries),
        "neural_runs": 27,
        "classical_runs": 27,
        "test_evaluation_executed": False,
    }


if __name__ == "__main__":
    print(json.dumps(prepare(), ensure_ascii=False, indent=2))
