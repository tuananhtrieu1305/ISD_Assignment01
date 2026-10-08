"""Run the Phase 3 matched MLP experiment and materialize auditable artifacts."""

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn

from term_paper.src.common.ch2_data import prepare_dataset
from term_paper.src.common.ch2_experiment import (
    artifact_suffix,
    build_prediction_frame,
    select_binary_threshold,
    sha256_file,
)
from term_paper.src.common.ch2_metrics import metrics_from_prediction_csv
from term_paper.src.keras_impl.mlp import KerasMLP
from term_paper.src.pytorch_impl.mlp import TorchMLP
from term_paper.src.scratch.mlp import NumpyMLP


DATASET_IDS = (
    "ch2_diabetes_binary",
    "ch2_vietnam_housing",
    "ch2_ecommerce_behavior",
)
FRAMEWORKS = ("numpy", "keras", "pytorch")
MODEL_CLASSES = {"numpy": NumpyMLP, "keras": KerasMLP, "pytorch": TorchMLP}
MODEL_EXTENSIONS = {"numpy": ".npz", "keras": ".keras", "pytorch": ".pt"}


def json_safe(value):
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def write_json(path, payload):
    Path(path).write_text(
        json.dumps(json_safe(payload), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def file_hashes(paths):
    return {str(Path(path)): sha256_file(path) for path in paths}


def binary_cross_entropy(y_true, score):
    y_true = np.asarray(y_true, dtype=float).reshape(-1)
    score = np.clip(np.asarray(score, dtype=float).reshape(-1), 1e-7, 1.0 - 1e-7)
    return float(-np.mean(y_true * np.log(score) + (1.0 - y_true) * np.log(1.0 - score)))


def validation_loss(task, y_true, score):
    if task == "binary":
        return binary_cross_entropy(y_true, score)
    return float(np.mean((np.asarray(score) - np.asarray(y_true)) ** 2))


def save_prepared_dataset(dataset, workspace):
    manifest_dir = workspace / "term_paper" / "artifacts" / "manifests" / "ch2"
    model_dir = workspace / "term_paper" / "artifacts" / "models" / "ch2"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = manifest_dir / f"{dataset.dataset_id}_metadata.json"
    existing_metadata = None
    if metadata_path.exists():
        existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    processed_path = manifest_dir / f"{dataset.dataset_id}_processed.npz"
    np.savez_compressed(
        processed_path,
        x_train=dataset.x["train"],
        x_val=dataset.x["val"],
        x_test=dataset.x["test"],
        y_model_train=dataset.y_model["train"],
        y_model_val=dataset.y_model["val"],
        y_model_test=dataset.y_model["test"],
        y_true_train=dataset.y_true["train"],
        y_true_val=dataset.y_true["val"],
        y_true_test=dataset.y_true["test"],
        keys_train=dataset.keys["train"],
        keys_val=dataset.keys["val"],
        keys_test=dataset.keys["test"],
    )
    split_rows = []
    for split in ("train", "val", "test"):
        for row_order, (key, target) in enumerate(
            zip(dataset.keys[split], dataset.y_true[split])
        ):
            split_rows.append(
                {
                    "dataset_id": dataset.dataset_id,
                    "split": split,
                    "row_order": row_order,
                    "sample_key": key,
                    "y_true": target,
                }
            )
    split_path = manifest_dir / f"{dataset.dataset_id}_split_keys.csv"
    pd.DataFrame(split_rows).to_csv(split_path, index=False)
    preprocessor_path = model_dir / f"{dataset.dataset_id}_preprocessor.joblib"
    processed_sha256 = sha256_file(processed_path)
    can_reuse_preprocessor = (
        preprocessor_path.exists()
        and existing_metadata is not None
        and existing_metadata.get("processed_sha256") == processed_sha256
    )
    if not can_reuse_preprocessor:
        joblib.dump(dataset.preprocessor, preprocessor_path)
    metadata = {
        "dataset_id": dataset.dataset_id,
        "task": dataset.task,
        "seed": 42,
        "split_sizes": {name: len(dataset.keys[name]) for name in ("train", "val", "test")},
        "x_shapes": {name: list(dataset.x[name].shape) for name in ("train", "val", "test")},
        "raw_feature_count": len(dataset.raw_feature_names),
        "transformed_feature_count": len(dataset.transformed_feature_names),
        "raw_feature_names": dataset.raw_feature_names,
        "transformed_feature_names": dataset.transformed_feature_names,
        "class_weight": dataset.class_weight,
        "target_transform": dataset.target_transform,
        "split_sha256": dataset.split_sha256,
        "processed_npz": str(processed_path.relative_to(workspace)).replace("\\", "/"),
        "processed_sha256": processed_sha256,
        "split_manifest": str(split_path.relative_to(workspace)).replace("\\", "/"),
        "split_manifest_sha256": sha256_file(split_path),
        "preprocessor": str(preprocessor_path.relative_to(workspace)).replace("\\", "/"),
        "preprocessor_sha256": sha256_file(preprocessor_path),
        "source_sha256": file_hashes(dataset.source_paths),
    }
    write_json(metadata_path, metadata)
    return metadata, preprocessor_path


def create_model(framework, dataset, config, learning_rate, seed):
    return MODEL_CLASSES[framework](
        input_dim=dataset.x["train"].shape[1],
        task=dataset.task,
        hidden=tuple(config["hidden_units"]),
        seed=seed,
        learning_rate=learning_rate,
        l2=config["l2"],
    )


def train_one(dataset, framework, seed, config, workspace, dataset_metadata):
    candidates = []
    trained_models = []
    histories = []
    total_search_start = time.perf_counter()
    for learning_rate in config["learning_rate_candidates"]:
        print(
            f"TRAIN dataset={dataset.dataset_id} framework={framework} seed={seed} lr={learning_rate}",
            flush=True,
        )
        model = create_model(framework, dataset, config, learning_rate, seed)
        start = time.perf_counter()
        history = model.fit(
            dataset.x["train"],
            dataset.y_model["train"],
            dataset.x["val"],
            dataset.y_model["val"],
            epochs=config["max_epochs"],
            batch_size=config["batch_size"],
            patience=config["patience"],
            min_delta=config["min_delta"],
            class_weight=dataset.class_weight,
        )
        seconds = time.perf_counter() - start
        val_score = model.predict_score(dataset.x["val"])
        measured_val_loss = validation_loss(
            dataset.task, dataset.y_model["val"], val_score
        )
        best_epoch = int(np.argmin(history["val_loss"])) + 1
        candidates.append(
            {
                "learning_rate": learning_rate,
                "measured_val_loss": measured_val_loss,
                "history_best_val_loss": float(np.min(history["val_loss"])),
                "best_epoch": best_epoch,
                "epochs_run": len(history["val_loss"]),
                "training_seconds": seconds,
            }
        )
        trained_models.append(model)
        histories.append(history)
        print(
            f"DONE dataset={dataset.dataset_id} framework={framework} seed={seed} lr={learning_rate} "
            f"val_loss={measured_val_loss:.6f} epochs={len(history['val_loss'])} seconds={seconds:.2f}",
            flush=True,
        )
    selected_index = int(np.argmin([row["measured_val_loss"] for row in candidates]))
    model = trained_models[selected_index]
    history = histories[selected_index]
    selected = candidates[selected_index]
    threshold = None
    threshold_table = None
    if dataset.task == "binary":
        val_score = model.predict_score(dataset.x["val"])
        threshold, threshold_table = select_binary_threshold(
            dataset.y_true["val"], val_score
        )
    model_dir = workspace / "term_paper" / "artifacts" / "models" / "ch2"
    model_path = model_dir / (
        f"{dataset.dataset_id}_{framework}_seed{seed}"
        + MODEL_EXTENSIONS[framework]
    )
    model.save(model_path)
    model_sha = sha256_file(model_path)
    warmup_count = min(512, len(dataset.x["test"]))
    model.predict_score(dataset.x["test"][:warmup_count])
    inference_start = time.perf_counter()
    test_score_model = model.predict_score(dataset.x["test"])
    inference_seconds = time.perf_counter() - inference_start
    if dataset.task == "binary":
        y_score = test_score_model
        y_pred = (y_score >= threshold).astype(int)
        y_true = dataset.y_true["test"].astype(int)
    else:
        y_score = None
        y_pred = np.maximum(dataset.inverse_target(test_score_model), 0.0)
        y_true = dataset.y_true["test"]
    prediction_frame = build_prediction_frame(
        dataset_id=dataset.dataset_id,
        framework=framework,
        task=dataset.task,
        keys=dataset.keys["test"],
        y_true=y_true,
        y_score=y_score,
        y_pred=y_pred,
        threshold=threshold,
        model_sha256=model_sha,
        preprocessor_sha256=dataset_metadata["preprocessor_sha256"],
        split_sha256=dataset.split_sha256,
        seed=seed,
    )
    prediction_dir = workspace / "term_paper" / "artifacts" / "predictions"
    prediction_dir.mkdir(parents=True, exist_ok=True)
    suffix = artifact_suffix(seed)
    prediction_path = prediction_dir / f"ch2_{dataset.dataset_id}_{framework}{suffix}_test.csv"
    prediction_frame.to_csv(prediction_path, index=False)
    metrics = metrics_from_prediction_csv(prediction_path)
    history_dir = workspace / "term_paper" / "artifacts" / "metrics"
    history_path = history_dir / f"ch2_{dataset.dataset_id}_{framework}{suffix}_history.csv"
    pd.DataFrame(
        {
            "epoch": np.arange(1, len(history["train_loss"]) + 1),
            "train_loss": history["train_loss"],
            "val_loss": history["val_loss"],
        }
    ).to_csv(history_path, index=False)
    candidate_path = history_dir / f"ch2_{dataset.dataset_id}_{framework}{suffix}_lr_search.csv"
    pd.DataFrame(candidates).to_csv(candidate_path, index=False)
    threshold_path = None
    if threshold_table is not None:
        threshold_path = history_dir / f"ch2_{dataset.dataset_id}_{framework}{suffix}_threshold.csv"
        threshold_table.to_csv(threshold_path, index=False)
    metric_row = {
        "chapter": 2,
        "dataset_id": dataset.dataset_id,
        "framework": framework,
        "seed": seed,
        "split": "test",
        "task": dataset.task,
        "topology_id": "mlp_64_32_1",
        "input_dim": dataset.x["train"].shape[1],
        "parameter_count": model.parameter_count,
        "optimizer": config["optimizer"],
        "learning_rate": selected["learning_rate"],
        "batch_size": config["batch_size"],
        "epochs_run": selected["epochs_run"],
        "best_epoch": selected["best_epoch"],
        "training_seconds": selected["training_seconds"],
        "search_seconds": time.perf_counter() - total_search_start,
        "inference_seconds": inference_seconds,
        "inference_ms_per_sample": inference_seconds * 1000.0 / len(y_true),
        "sample_count": len(y_true),
        "threshold": threshold,
        "prediction_path": str(prediction_path.relative_to(workspace)).replace("\\", "/"),
        "prediction_sha256": sha256_file(prediction_path),
        "model_path": str(model_path.relative_to(workspace)).replace("\\", "/"),
        "model_sha256": model_sha,
        "preprocessor_sha256": dataset_metadata["preprocessor_sha256"],
        "processed_sha256": dataset_metadata["processed_sha256"],
        "split_sha256": dataset.split_sha256,
        **metrics,
    }
    run_metadata = {
        "metric_row": metric_row,
        "learning_rate_candidates": candidates,
        "selected_candidate_index": selected_index,
        "history_path": str(history_path.relative_to(workspace)).replace("\\", "/"),
        "threshold_path": (
            str(threshold_path.relative_to(workspace)).replace("\\", "/")
            if threshold_path
            else None
        ),
    }
    run_metadata_path = history_dir / f"ch2_{dataset.dataset_id}_{framework}{suffix}_run.json"
    write_json(run_metadata_path, run_metadata)
    return metric_row


def consolidate_classical_baselines(workspace):
    sources = {
        "ch2_diabetes_binary": workspace / "pipeline" / "diabetes" / "final_comparison.csv",
        "ch2_vietnam_housing": workspace / "pipeline" / "house_price" / "final_comparison.csv",
        "ch2_ecommerce_behavior": workspace
        / "pipeline"
        / "customer_behavior"
        / "final_comparison.csv",
    }
    rows = []
    for dataset_id, path in sources.items():
        frame = pd.read_csv(path)
        frame = frame[frame["Model"] != "Improved DNN"].copy()
        frame.insert(0, "dataset_id", dataset_id)
        frame["source_path"] = str(path.relative_to(workspace)).replace("\\", "/")
        frame["source_sha256"] = sha256_file(path)
        rows.append(frame)
    output = pd.concat(rows, ignore_index=True, sort=False)
    output_path = workspace / "term_paper" / "artifacts" / "metrics" / "ch2_classical_baselines.csv"
    output.to_csv(output_path, index=False)
    return output_path


def create_figures(workspace, metric_frame):
    figure_dir = workspace / "term_paper" / "artifacts" / "figures" / "ch2"
    figure_dir.mkdir(parents=True, exist_ok=True)
    display_names = {
        "ch2_diabetes_binary": "CDC Diabetes",
        "ch2_vietnam_housing": "Vietnam Housing",
        "ch2_ecommerce_behavior": "E-Commerce Churn",
    }
    framework_names = {"numpy": "NumPy scratch", "keras": "Keras", "pytorch": "PyTorch"}
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    for axis, dataset_id in zip(axes, DATASET_IDS):
        subset = metric_frame[metric_frame["dataset_id"] == dataset_id].copy()
        metric = "RMSE" if dataset_id == "ch2_vietnam_housing" else "F1"
        grouped = subset.groupby("framework")[metric].agg(["mean", "std"]).reindex(FRAMEWORKS)
        grouped["std"] = grouped["std"].fillna(0.0)
        bars = axis.bar(
            [framework_names[name] for name in FRAMEWORKS],
            grouped["mean"].values,
            yerr=grouped["std"].values,
            capsize=4,
            color=["#2F75B5", "#E69F00", "#009E73"],
        )
        axis.set_title(display_names[dataset_id])
        axis.set_ylabel(metric + (" (tỷ VND)" if metric == "RMSE" else ""))
        axis.tick_params(axis="x", rotation=20)
        for bar, value in zip(bars, grouped["mean"].values):
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
    fig.suptitle("Matched MLP: metric chính trên TEST")
    fig.tight_layout()
    metric_path = figure_dir / "ch2_framework_primary_metrics.png"
    fig.savefig(metric_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    for axis, dataset_id in zip(axes, DATASET_IDS):
        for framework in FRAMEWORKS:
            history_path = (
                workspace
                / "term_paper"
                / "artifacts"
                / "metrics"
                / f"ch2_{dataset_id}_{framework}_history.csv"
            )
            history = pd.read_csv(history_path)
            axis.plot(history["epoch"], history["val_loss"], label=framework_names[framework])
        axis.set_title(display_names[dataset_id])
        axis.set_xlabel("Epoch")
        axis.set_ylabel("Validation loss")
    axes[-1].legend(loc="best", fontsize=8)
    fig.suptitle("Validation loss của learning rate được chọn")
    fig.tight_layout()
    history_figure_path = figure_dir / "ch2_validation_loss_curves.png"
    fig.savefig(history_figure_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return [metric_path, history_figure_path]


def environment_payload():
    import keras
    import tensorflow as tf
    import torch

    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "tensorflow": tf.__version__,
        "keras": keras.__version__,
        "torch": torch.__version__,
        "torch_device": "cpu",
        "tensorflow_devices": [device.name for device in tf.config.list_physical_devices()],
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=str(Path.cwd()))
    parser.add_argument("--datasets", nargs="+", choices=DATASET_IDS, default=list(DATASET_IDS))
    parser.add_argument("--frameworks", nargs="+", choices=FRAMEWORKS, default=list(FRAMEWORKS))
    parser.add_argument("--seeds", nargs="+", type=int, default=None)
    args = parser.parse_args(argv)
    workspace = Path(args.workspace).resolve()
    config_path = workspace / "term_paper" / "config" / "ch2_experiment.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    seeds = args.seeds if args.seeds is not None else config.get("seeds", [config["seed"]])
    metrics_dir = workspace / "term_paper" / "artifacts" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        workspace / "term_paper" / "artifacts" / "manifests" / "ch2" / "environment.json",
        environment_payload(),
    )
    run_start = time.perf_counter()
    rows = []
    for dataset_id in args.datasets:
        print(f"PREPARE dataset={dataset_id}", flush=True)
        dataset = prepare_dataset(workspace, dataset_id)
        dataset_metadata, _ = save_prepared_dataset(dataset, workspace)
        print(
            f"PREPARED dataset={dataset_id} shapes={dataset_metadata['x_shapes']} "
            f"split_sha256={dataset.split_sha256}",
            flush=True,
        )
        for framework in args.frameworks:
            for seed in seeds:
                rows.append(
                    train_one(dataset, framework, int(seed), config, workspace, dataset_metadata)
                )
    new_metrics = pd.DataFrame(rows)
    comparison_path = metrics_dir / "ch2_framework_comparison.csv"
    if comparison_path.exists():
        previous = pd.read_csv(comparison_path)
        keys = set(
            zip(new_metrics["dataset_id"], new_metrics["framework"], new_metrics["seed"])
        )
        previous = previous[
            ~previous.apply(
                lambda row: (row["dataset_id"], row["framework"], row["seed"]) in keys,
                axis=1,
            )
        ]
        new_metrics = pd.concat([previous, new_metrics], ignore_index=True)
    new_metrics.sort_values(["dataset_id", "framework"]).to_csv(comparison_path, index=False)
    consolidate_classical_baselines(workspace)
    if set(DATASET_IDS).issubset(set(new_metrics["dataset_id"])) and set(FRAMEWORKS).issubset(
        set(new_metrics["framework"])
    ):
        figure_paths = create_figures(workspace, new_metrics)
    else:
        figure_paths = []
    summary = {
        "protocol_version": config["protocol_version"],
        "config_path": str(config_path.relative_to(workspace)).replace("\\", "/"),
        "config_sha256": sha256_file(config_path),
        "elapsed_seconds": time.perf_counter() - run_start,
        "datasets": list(args.datasets),
        "frameworks": list(args.frameworks),
        "seeds": [int(seed) for seed in seeds],
        "comparison_path": str(comparison_path.relative_to(workspace)).replace("\\", "/"),
        "comparison_sha256": sha256_file(comparison_path),
        "figures": [str(path.relative_to(workspace)).replace("\\", "/") for path in figure_paths],
    }
    write_json(metrics_dir / "ch2_run_summary.json", summary)
    print(f"CH2 RUN COMPLETE seconds={summary['elapsed_seconds']:.2f}", flush=True)


if __name__ == "__main__":
    main()
