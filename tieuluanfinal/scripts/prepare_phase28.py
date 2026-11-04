"""Declare all main/rolling RNN runs and baselines before measured training."""

import json

from src.ch04_rnn_lstm.protocol import (
    BASE,
    DATASETS,
    FOLDS,
    IMPLEMENTATIONS,
    SEEDS,
    SOURCE_FILES,
    check_sources,
    code_info,
    label,
    ref,
    run_id,
)
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.artifact_core import write_once
from src.common.contracts import PROTOCOL, ROOT, canonical_sha256, read_json
from src.common.model_core import build_plan, canonical_weights, make_contract, render_functions


def prepare():
    if (BASE / "release.json").exists():
        return check_sources()
    for method in IMPLEMENTATIONS:
        probe_name = "preflight_keras_xla_v1.json" if method == "keras" else f"preflight_{method}.json"
        if read_json(BASE / probe_name)["status"] != "PASS":
            raise ValueError("Missing real-shape recurrent feasibility/parity probe")
    if read_json(BASE / "dependency_audit.json")["status"] != "PASS":
        raise ValueError("Dependency audit missing")
    protocol, code, entries = read_json(PROTOCOL), code_info(), []
    for dataset in DATASETS:
        for fold in FOLDS:
            data = WindowData(dataset, fold)
            suffix = f"{dataset}_{label(fold)}"
            data_path = BASE / "data" / f"{suffix}.json"
            write_once(data_path, data.contract())
            adapter_path = BASE / "adapters" / f"{suffix}.json"
            write_once(adapter_path, data.view.contract())
            plan = build_plan("rnn", [data.lookback, data.features.shape[1]], len(data.horizons))
            for seed in SEEDS:
                path = BASE / "configs" / f"{suffix}_s{seed}.json"
                config = {
                    "phase": 28,
                    "dataset_id": dataset,
                    "fold": fold,
                    "seed": seed,
                    "task": "mse",
                    "plan": plan,
                    "track": "matched_subset",
                    "code": code,
                    "provenance": data.provenance,
                    "adapter": ref(adapter_path),
                    "data_contract": ref(data_path),
                    "environment_sha256": ref(ROOT / "uv.lock")["sha256"],
                    "protocol_sha256": ref(PROTOCOL)["sha256"],
                    "training": {
                        **protocol["training"],
                        "batch_size": protocol["training"]["batch_size"]["rnn"],
                    },
                    "canonical_initial_weights_sha256": canonical_sha256(
                        {key: value.tolist() for key, value in canonical_weights(plan, seed).items()}
                    ),
                    "horizons": data.horizons,
                    "primary_metric": data.view.spec["primary_metric"],
                    "unit": {
                        "ch4_gold_pink_sheet": "USD/troy ounce",
                        "ch4_bis_house_prices": "index 2010=100",
                        "ch4_household_power": "kW",
                    }[dataset],
                    "test_policy": "NO TEST in Phase28; joint RNN/LSTM TEST only in Phase29 after both families locked",
                    "validation_policy": "Every origin uses only observed history; all horizons within partition; rolling folds use their own frozen scaler and matched IDs",
                    "execution_policy": {
                        "scratch": "NumPy CPU manual BPTT/Adam",
                        "keras": "Keras TensorFlow GPU tf.function with XLA JIT; host validation plus canonical Adam",
                        "pytorch": "PyTorch GPU eager, frozen zero second recurrent bias",
                    },
                    "baseline_policy": data.contract()["baseline_policy"],
                    "gradient_diagnostic_policy": "first four fixed TRAIN IDs, selected weights, normalized MSE input gradient; no causal/TEST claims",
                }
                write_once(path, config)
                group = canonical_sha256(config)
                methods = (
                    (*IMPLEMENTATIONS, "last_value", "seasonal_naive") if seed == 42 else IMPLEMENTATIONS
                )
                for method in methods:
                    run = run_id(dataset, method, seed, fold)
                    folder = BASE / "runs" / run
                    if method in IMPLEMENTATIONS:
                        contract = make_contract(
                            plan,
                            method,
                            "measured",
                            {
                                "dataset_id": dataset,
                                "config_sha256": ref(path)["sha256"],
                                "dataset_sha256": data.provenance["dataset_sha256"],
                                "comparison_group_sha256": group,
                                "preprocessing": data.view.contract()["preprocessing"],
                            },
                        )
                        contract["model_id"] = run
                        functions = render_functions(contract)
                        write_once(
                            folder / "functions.json", {k: v for k, v in functions.items() if k != "markdown"}
                        )
                    else:
                        contract = {
                            "schema_version": "phase28.causal_baseline.1",
                            "model_id": run,
                            "dataset_id": dataset,
                            "method": method,
                            "family": "classical",
                            "config": ref(path),
                            "layer_count_applicable": False,
                        }
                    write_once(folder / "model_contract.json", contract)
                    entries.append(
                        {
                            "run_id": run,
                            "dataset_id": dataset,
                            "fold": fold,
                            "method": method,
                            "seed": seed,
                            "config": ref(path),
                            "model_contract": ref(folder / "model_contract.json"),
                            "comparison_group_sha256": group,
                        }
                    )
    release = {
        "phase": 28,
        "status": "declared_before_training",
        "code": code,
        "source_files": [ref(ROOT / name) for name in SOURCE_FILES],
        "protocol": ref(PROTOCOL),
        "environment": ref(ROOT / "uv.lock"),
        "dependency_audit": ref(BASE / "dependency_audit.json"),
        "preflight": [
            ref(BASE / name)
            for name in ("preflight_scratch.json", "preflight_pytorch.json", "preflight_keras_xla_v1.json")
        ],
        "runs": entries,
        "neural_runs": 108,
        "baseline_runs": 24,
        "main_neural_runs": 27,
        "rolling_neural_runs": 81,
        "test_evaluation_executed": False,
        "test_owner_phase": 29,
    }
    write_once(BASE / "release.json", release)
    return {
        "status": "PASS",
        "runs": len(entries),
        "neural_runs": 108,
        "baseline_runs": 24,
        "test_executed": False,
    }


if __name__ == "__main__":
    print(json.dumps(prepare(), ensure_ascii=False, indent=2))
