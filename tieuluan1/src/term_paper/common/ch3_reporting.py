"""Recompute Chapter 3 metrics, import A05 evidence and generate report figures."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix

from term_paper.src.common.ch3_data import A05_ROOT, WORKSPACE_ROOT
from term_paper.src.common.ch3_experiment import sha256_file
from term_paper.src.common.ch3_metrics import multiclass_metrics


TERM_ROOT = WORKSPACE_ROOT / "term_paper"
METRIC_DIR = TERM_ROOT / "artifacts" / "metrics"
PREDICTION_DIR = TERM_ROOT / "artifacts" / "predictions"
FIGURE_DIR = TERM_ROOT / "artifacts" / "figures" / "ch3"
MANIFEST_DIR = TERM_ROOT / "artifacts" / "manifests" / "ch3"


def aggregate_framework_results(frame):
    metrics = [
        "accuracy",
        "macro_precision",
        "macro_recall",
        "macro_f1",
        "training_seconds",
        "inference_ms_per_sample",
    ]
    recall_columns = sorted(
        column for column in frame.columns if column.startswith("recall_class_")
    )
    rows = []
    for (dataset_id, framework), group in frame.groupby(["dataset_id", "framework"]):
        row = {
            "dataset_id": dataset_id,
            "framework": framework,
            "run_count": int(len(group)),
            "parameter_count": int(group["parameter_count"].iloc[0]),
        }
        for metric in metrics + recall_columns:
            if metric not in group:
                continue
            values = pd.to_numeric(group[metric], errors="coerce")
            if values.notna().any():
                row[f"{metric}_mean"] = float(values.mean())
                row[f"{metric}_std"] = float(values.std(ddof=1)) if len(values) > 1 else 0.0
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["dataset_id", "framework"]).reset_index(drop=True)


def reproduce_metrics(comparison):
    for _, row in comparison.iterrows():
        prediction_path = TERM_ROOT / row["prediction_path"]
        frame = pd.read_csv(prediction_path)
        class_columns = sorted(
            [column for column in frame if column.startswith("prob_")],
            key=lambda value: int(value.split("_")[1]),
        )
        probabilities = frame[class_columns].to_numpy(dtype=float)
        np.testing.assert_allclose(probabilities.sum(axis=1), 1.0, atol=1e-6)
        np.testing.assert_array_equal(frame["y_pred"], np.argmax(probabilities, axis=1))
        metrics = multiclass_metrics(
            frame["y_true"], frame["y_pred"], labels=range(len(class_columns))
        )
        for key, value in metrics.items():
            if key in comparison.columns:
                if not np.isclose(float(row[key]), float(value), atol=1e-12):
                    raise AssertionError(f"metric mismatch {prediction_path}: {key}")
        if sha256_file(prediction_path) != row["prediction_sha256"]:
            raise AssertionError(f"prediction hash mismatch: {prediction_path}")


def import_a05_ablation():
    rows = []
    provenance = []
    for dataset in ("eurosat", "oxford_pets", "diabetes"):
        path = A05_ROOT / "results" / "metrics" / f"{dataset}_models.csv"
        frame = pd.read_csv(path)
        provenance.append(
            {
                "artifact": str(path.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
        )
        for _, source in frame.iterrows():
            if str(source.get("key")) == "majority_baseline":
                continue
            rows.append(
                {
                    "dataset_id": f"a05_{dataset}",
                    "model_family": source["model_family"],
                    "key": source["key"],
                    "test_accuracy": float(source.get("test_accuracy", np.nan)),
                    "macro_precision": float(
                        source.get("macro_precision", source.get("test_macro_precision", np.nan))
                    ),
                    "macro_recall": float(
                        source.get("macro_recall", source.get("test_macro_recall", np.nan))
                    ),
                    "macro_f1": float(
                        source.get("macro_f1", source.get("test_macro_f1", np.nan))
                    ),
                    "parameter_count": int(source["trainable_parameter_count"]),
                    "training_seconds": float(source["training_time_seconds"]),
                    "prediction_path": source["prediction_path"],
                    "source_sha256": provenance[-1]["sha256"],
                }
            )
    result = pd.DataFrame(rows)
    result.to_csv(METRIC_DIR / "ch3_a05_architecture_ablation.csv", index=False)
    (MANIFEST_DIR / "a05_ablation_provenance.json").write_text(
        json.dumps(provenance, indent=2), encoding="utf-8"
    )
    return result


def create_dataset_summary():
    rows = [
        {
            "dataset_id": "ch3_eurosat",
            "full_samples": 27000,
            "classes": 10,
            "input": "64×64×3 RGB",
            "matched_train": 500,
            "matched_val": 150,
            "matched_test": 150,
            "role": "matched + A05 full-data ablation",
        },
        {
            "dataset_id": "ch3_oxford_pets",
            "full_samples": 7349,
            "classes": 37,
            "input": "RGB resized 96×96",
            "matched_train": np.nan,
            "matched_val": np.nan,
            "matched_test": np.nan,
            "role": "A05 Keras case study",
        },
        {
            "dataset_id": "ch3_diabetes_012",
            "full_samples": 253680,
            "classes": 3,
            "input": "21×1 standardized features",
            "matched_train": 6000,
            "matched_val": 1500,
            "matched_test": 1500,
            "role": "matched + A05 full-data ablation",
        },
    ]
    result = pd.DataFrame(rows)
    result.to_csv(METRIC_DIR / "ch3_dataset_summary.csv", index=False)
    return result


def _plot_dataset_distributions():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    euro = pd.concat(
        [
            pd.read_csv(A05_ROOT / "results" / "splits" / f"eurosat_{split}.csv")
            for split in ("train", "val", "test")
        ]
    )
    euro["class_name"].value_counts().sort_values().plot.barh(ax=axes[0], color="#3566A8")
    axes[0].set_title("EuroSAT: 27.000 ảnh")
    axes[0].set_xlabel("Số ảnh")
    axes[0].set_ylabel("Lớp")
    oxford = pd.concat(
        [
            pd.read_csv(A05_ROOT / "results" / "splits" / f"oxford_pets_{split}.csv")
            for split in ("train", "val", "test")
        ]
    )
    label_column = "class_name" if "class_name" in oxford else "breed"
    oxford[label_column].value_counts().sort_values().plot.bar(
        ax=axes[1], color="#D27B29", width=0.8
    )
    axes[1].set_title("Oxford Pets: 37 giống")
    axes[1].set_ylabel("Số ảnh")
    axes[1].set_xlabel("37 lớp (ẩn nhãn để dễ đọc)")
    axes[1].tick_params(axis="x", labelbottom=False)
    diabetes_path = (
        A05_ROOT / "datasets" / "diabetes" / "diabetes_012_health_indicators_BRFSS2015.csv"
    )
    diabetes = pd.read_csv(diabetes_path, usecols=["Diabetes_012"])
    diabetes["Diabetes_012"].value_counts().sort_index().plot.bar(
        ax=axes[2], color=["#4F8A5B", "#E0A12A", "#B54B4B"]
    )
    axes[2].set_title("CDC Diabetes: lệch lớp")
    axes[2].set_xlabel("Lớp 0 / 1 / 2")
    axes[2].set_ylabel("Số bản ghi")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "ch3_dataset_distributions.png", dpi=180)
    plt.close(fig)


def _plot_matched_metrics(summary):
    datasets = ["ch3_eurosat", "ch3_diabetes_012"]
    frameworks = ["numpy", "keras", "pytorch"]
    colors = ["#3566A8", "#D27B29", "#4F8A5B"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    for axis, dataset in zip(axes, datasets):
        selected = summary[summary["dataset_id"] == dataset].set_index("framework")
        means = [selected.loc[name, "macro_f1_mean"] for name in frameworks]
        errors = [selected.loc[name, "macro_f1_std"] for name in frameworks]
        axis.bar(frameworks, means, yerr=errors, capsize=4, color=colors)
        axis.set_ylim(0, max(0.55, max(means) + max(errors) + 0.08))
        axis.set_title("EuroSAT benchmark" if dataset.endswith("eurosat") else "CDC benchmark")
        axis.set_ylabel("Macro-F1 (mean ± SD)")
        axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "ch3_matched_macro_f1.png", dpi=180)
    plt.close(fig)


def _plot_histories():
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for axis, dataset in zip(axes, ("ch3_eurosat", "ch3_diabetes_012")):
        for framework in ("numpy", "keras", "pytorch"):
            path = METRIC_DIR / f"ch3_{dataset}_{framework}_history.csv"
            history = pd.read_csv(path)
            axis.plot(history["epoch"], history["val_loss"], marker="o", label=framework)
        axis.set_title("EuroSAT — seed 42" if dataset.endswith("eurosat") else "CDC — seed 42")
        axis.set_xlabel("Epoch")
        axis.set_ylabel("Validation loss")
        axis.grid(alpha=0.25)
        axis.legend()
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "ch3_validation_loss_curves.png", dpi=180)
    plt.close(fig)


def _plot_confusions(comparison, summary):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for axis, dataset in zip(axes, ("ch3_eurosat", "ch3_diabetes_012")):
        selected = summary[summary["dataset_id"] == dataset].sort_values(
            "macro_f1_mean", ascending=False
        ).iloc[0]
        framework = selected["framework"]
        frames = []
        for _, row in comparison[
            (comparison["dataset_id"] == dataset)
            & (comparison["framework"] == framework)
        ].iterrows():
            frames.append(pd.read_csv(TERM_ROOT / row["prediction_path"]))
        predictions = pd.concat(frames, ignore_index=True)
        labels = sorted(predictions["y_true"].unique())
        matrix = confusion_matrix(predictions["y_true"], predictions["y_pred"], labels=labels)
        normalized = matrix / np.maximum(matrix.sum(axis=1, keepdims=True), 1)
        image = axis.imshow(normalized, cmap="Blues", vmin=0, vmax=1)
        axis.set_title(f"{dataset.replace('ch3_', '')} — {framework}")
        axis.set_xlabel("Lớp dự đoán")
        axis.set_ylabel("Lớp thật")
        axis.set_xticks(range(len(labels)))
        axis.set_yticks(range(len(labels)))
        if len(labels) <= 3:
            for row in range(len(labels)):
                for column in range(len(labels)):
                    axis.text(column, row, f"{normalized[row, column]:.2f}", ha="center", va="center")
    fig.colorbar(image, ax=axes.ravel().tolist(), shrink=0.82, label="Tỷ lệ theo lớp thật")
    fig.savefig(FIGURE_DIR / "ch3_matched_confusion_matrices.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def _plot_ablation(ablation):
    pivot = ablation.pivot(index="key", columns="dataset_id", values="macro_f1")
    order = ["basic", "alexnet_inspired", "vgg_inspired", "resnet_inspired"]
    pivot = pivot.reindex(order)
    axis = pivot.plot.bar(figsize=(12, 5), color=["#3566A8", "#4F8A5B", "#D27B29"])
    axis.set_ylabel("Macro-F1")
    axis.set_xlabel("CNN family trong A05")
    axis.set_title("A05 full-data/common-protocol architecture ablation")
    axis.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "ch3_a05_architecture_ablation.png", dpi=180)
    plt.close()


def main():
    METRIC_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    comparison = pd.read_csv(METRIC_DIR / "ch3_framework_comparison.csv")
    reproduce_metrics(comparison)
    summary = aggregate_framework_results(comparison)
    summary.to_csv(METRIC_DIR / "ch3_framework_summary.csv", index=False)
    ablation = import_a05_ablation()
    create_dataset_summary()
    _plot_dataset_distributions()
    _plot_matched_metrics(summary)
    _plot_histories()
    _plot_confusions(comparison, summary)
    _plot_ablation(ablation)
    figure_manifest = []
    for path in sorted(FIGURE_DIR.glob("*.png")):
        figure_manifest.append(
            {
                "path": str(path.relative_to(TERM_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    (MANIFEST_DIR / "figure_manifest.json").write_text(
        json.dumps(figure_manifest, indent=2), encoding="utf-8"
    )
    print(f"Chapter 3 reporting complete: {len(comparison)} runs, {len(figure_manifest)} figures")


if __name__ == "__main__":
    main()
