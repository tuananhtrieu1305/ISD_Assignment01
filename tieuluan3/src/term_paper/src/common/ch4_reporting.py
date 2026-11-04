"""Reproduce Chapter 4 metrics, import A06 evidence and create report figures."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_curve

from term_paper.src.common.ch4_data import A06_ROOT, WORKSPACE_ROOT
from term_paper.src.common.ch4_experiment import sha256_file
from term_paper.src.common.ch4_metrics import binary_metrics, regression_metrics


TERM_ROOT = WORKSPACE_ROOT / "term_paper"
METRIC_DIR = TERM_ROOT / "artifacts" / "metrics"
FIGURE_DIR = TERM_ROOT / "artifacts" / "figures" / "ch4"
MANIFEST_DIR = TERM_ROOT / "artifacts" / "manifests" / "ch4"


def aggregate_framework_results(frame):
    base_metrics = ["primary_metric", "secondary_metric", "training_seconds", "inference_ms_per_sample"]
    detail_metrics = ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc", "mae", "rmse", "r2"]
    rows = []
    for (dataset_id, framework), group in frame.groupby(["dataset_id", "framework"]):
        row = {"dataset_id": dataset_id, "framework": framework, "run_count": int(len(group)),
               "parameter_count": int(group["parameter_count"].iloc[0])}
        for metric in base_metrics + detail_metrics:
            if metric not in group:
                continue
            values = pd.to_numeric(group[metric], errors="coerce").dropna()
            if len(values):
                row[f"{metric}_mean"] = float(values.mean())
                row[f"{metric}_std"] = float(values.std(ddof=1)) if len(values) > 1 else 0.0
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["dataset_id", "framework"]).reset_index(drop=True)


def reproduce_metrics(comparison, repair=False):
    repaired = comparison.copy()
    repaired_indices = set()
    for index, row in comparison.iterrows():
        path = TERM_ROOT / row["prediction_path"]
        frame = pd.read_csv(path)
        if row["task"] == "binary":
            reproduced = binary_metrics(frame["y_true"], frame["score_or_prediction"], frame["threshold"].iloc[0])
        else:
            reproduced = regression_metrics(frame["y_true"], frame["score_or_prediction"])
            naive = regression_metrics(frame["y_true"], frame["naive_last_close"])
            reproduced.update({f"naive_{key}": value for key, value in naive.items()})
        for key, value in reproduced.items():
            if not np.isclose(float(row[key]), float(value), atol=1e-12, rtol=0):
                if not repair:
                    raise AssertionError(f"metric mismatch {path}: {key}")
                repaired.at[index, key] = value
                repaired_indices.add(index)
                if key == "f1" and row["task"] == "binary":
                    repaired.at[index, "primary_metric"] = value
                if key == "pr_auc" and row["task"] == "binary":
                    repaired.at[index, "secondary_metric"] = value
                if key == "rmse" and row["task"] == "regression":
                    repaired.at[index, "primary_metric"] = value
                if key == "mae" and row["task"] == "regression":
                    repaired.at[index, "secondary_metric"] = value
        if sha256_file(path) != row["prediction_sha256"]:
            raise AssertionError(f"prediction hash mismatch: {path}")
    if repair:
        for index in repaired.index:
            row = repaired.loc[index]
            prediction_name = str(row["prediction_path"]).split("/")[-1]
            run_path = METRIC_DIR / prediction_name.replace("_test.csv", "_run.json")
            if run_path.exists():
                payload = json.loads(run_path.read_text(encoding="utf-8"))
                for key in ("primary_metric", "secondary_metric", "accuracy", "precision", "recall",
                            "f1", "roc_auc", "pr_auc", "tn", "fp", "fn", "tp", "mae", "rmse", "r2",
                            "naive_mae", "naive_rmse", "naive_r2"):
                    if key in repaired.columns and pd.notna(row.get(key)):
                        payload[key] = float(row[key])
                run_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return repaired


def import_a06_reference():
    source = A06_ROOT / "results" / "metrics" / "framework_comparison.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = []
    for name, data in payload["customer"]["models"].items():
        rows.append({"dataset_id": "customer_full_a06", "model": name, "hidden_size": 64,
                     **data["metrics"], "parameter_count": data["parameter_count"],
                     "training_seconds": data["training_duration_seconds"]})
    for name, data in payload["stock"]["models"].items():
        rows.append({"dataset_id": "aapl_full_a06", "model": name,
                     "hidden_size": 64 if "RNN" in name else np.nan, **data})
    result = pd.DataFrame(rows)
    result["source_sha256"] = sha256_file(source)
    result.to_csv(METRIC_DIR / "ch4_a06_reference.csv", index=False)
    (MANIFEST_DIR / "a06_reference_provenance.json").write_text(
        json.dumps({"path": str(source.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                    "sha256": sha256_file(source), "retraining_performed": False}, indent=2),
        encoding="utf-8",
    )
    return result


def create_dataset_summary():
    customer_meta = json.loads((MANIFEST_DIR / "ch4_online_retail_customer_week_metadata.json").read_text(encoding="utf-8"))
    stock_meta = json.loads((MANIFEST_DIR / "ch4_aapl_next_close_metadata.json").read_text(encoding="utf-8"))
    result = pd.DataFrame([
        {"dataset_id": customer_meta["dataset_id"], "source_samples": 350864,
         "sequence": "8×5 customer-week", "task": "binary classification",
         **{f"matched_{key}": value for key, value in customer_meta["split_sizes"].items()}},
        {"dataset_id": stock_meta["dataset_id"], "source_samples": 2736,
         "sequence": "30×5 trading-day", "task": "next-Close regression",
         **{f"matched_{key}": value for key, value in stock_meta["split_sizes"].items()}},
    ])
    result.to_csv(METRIC_DIR / "ch4_dataset_summary.csv", index=False)
    return result


def _seed42_frame(comparison, dataset, framework):
    row = comparison[(comparison["dataset_id"] == dataset) & (comparison["framework"] == framework) & (comparison["seed"] == 42)].iloc[0]
    return pd.read_csv(TERM_ROOT / row["prediction_path"])


def _plot_dataset_overview():
    customer = np.load(MANIFEST_DIR / "ch4_online_retail_customer_week_processed.npz", allow_pickle=False)
    stock = np.load(MANIFEST_DIR / "ch4_aapl_next_close_processed.npz", allow_pickle=False)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    labels = ["Không mua", "Có mua"]
    counts = [int(np.sum(customer["y_train"] == value)) for value in (0, 1)]
    axes[0].bar(labels, counts, color=["#3566A8", "#D27B29"])
    axes[0].set_title("Online Retail II — TRAIN benchmark"); axes[0].set_ylabel("Số customer-week")
    dates = pd.to_datetime(stock["dates_test"].astype(str))
    axes[1].plot(dates, stock["y_test_real"], color="#3566A8", label="Close thực")
    axes[1].plot(dates, stock["naive_test"], color="#888888", alpha=.75, label="Last Close")
    axes[1].set_title("AAPL — TEST theo thời gian"); axes[1].set_ylabel("USD"); axes[1].legend(); axes[1].grid(alpha=.2)
    fig.tight_layout(); fig.savefig(FIGURE_DIR / "ch4_dataset_overview.png", dpi=180); plt.close(fig)


def _plot_customer_metrics(summary):
    subset = summary[summary["dataset_id"] == "ch4_online_retail_customer_week"].set_index("framework")
    frameworks = ["numpy", "keras", "pytorch"]; metrics = ["f1", "roc_auc", "pr_auc"]
    fig, axis = plt.subplots(figsize=(9, 5)); x = np.arange(len(metrics)); width = .25
    for index, framework in enumerate(frameworks):
        means = [subset.loc[framework, f"{metric}_mean"] for metric in metrics]
        errors = [subset.loc[framework, f"{metric}_std"] for metric in metrics]
        axis.bar(x + (index - 1) * width, means, width, yerr=errors, capsize=3, label=framework)
    axis.set_xticks(x, ["F1", "ROC-AUC", "PR-AUC"]); axis.set_ylim(0, .85)
    axis.set_ylabel("Mean ± SD qua 3 seed"); axis.set_title("Customer next-week purchase")
    axis.legend(); axis.grid(axis="y", alpha=.2); fig.tight_layout()
    fig.savefig(FIGURE_DIR / "ch4_customer_metrics.png", dpi=180); plt.close(fig)


def _plot_customer_curves(comparison):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for framework in ("numpy", "keras", "pytorch"):
        frame = _seed42_frame(comparison, "ch4_online_retail_customer_week", framework)
        fpr, tpr, _ = roc_curve(frame["y_true"], frame["score_or_prediction"])
        precision, recall, _ = precision_recall_curve(frame["y_true"], frame["score_or_prediction"])
        axes[0].plot(fpr, tpr, label=framework); axes[1].plot(recall, precision, label=framework)
    axes[0].plot([0, 1], [0, 1], "--", color="#888888"); axes[0].set_title("ROC — seed 42")
    axes[0].set_xlabel("False positive rate"); axes[0].set_ylabel("True positive rate")
    axes[1].set_title("Precision–Recall — seed 42"); axes[1].set_xlabel("Recall"); axes[1].set_ylabel("Precision")
    for axis in axes: axis.legend(); axis.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(FIGURE_DIR / "ch4_customer_roc_pr.png", dpi=180); plt.close(fig)


def _plot_customer_confusions(comparison):
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for axis, framework in zip(axes, ("numpy", "keras", "pytorch")):
        frame = _seed42_frame(comparison, "ch4_online_retail_customer_week", framework)
        matrix = confusion_matrix(frame["y_true"], frame["y_pred"], labels=[0, 1]); image = axis.imshow(matrix, cmap="Blues")
        for row in range(2):
            for column in range(2): axis.text(column, row, str(matrix[row, column]), ha="center", va="center")
        axis.set_title(framework); axis.set_xlabel("Dự đoán"); axis.set_ylabel("Thực"); axis.set_xticks([0, 1]); axis.set_yticks([0, 1])
    fig.colorbar(image, ax=axes.ravel().tolist(), shrink=.78)
    fig.savefig(FIGURE_DIR / "ch4_customer_confusion_matrices.png", dpi=180, bbox_inches="tight"); plt.close(fig)


def _plot_stock_predictions(comparison):
    fig, axis = plt.subplots(figsize=(12, 5))
    reference = _seed42_frame(comparison, "ch4_aapl_next_close", "numpy"); dates = pd.to_datetime(reference["sample_key"])
    axis.plot(dates, reference["y_true"], color="#111111", linewidth=2, label="Actual")
    axis.plot(dates, reference["naive_last_close"], color="#888888", alpha=.8, label="Naive last Close")
    for framework in ("numpy", "keras", "pytorch"):
        frame = _seed42_frame(comparison, "ch4_aapl_next_close", framework)
        axis.plot(dates, frame["score_or_prediction"], alpha=.75, label=framework)
    axis.set_title("AAPL TEST — dự báo next Close, seed 42"); axis.set_ylabel("USD"); axis.legend(ncol=3); axis.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(FIGURE_DIR / "ch4_stock_actual_vs_predicted.png", dpi=180); plt.close(fig)


def _plot_stock_rmse_and_histories(comparison, summary):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    subset = summary[summary["dataset_id"] == "ch4_aapl_next_close"].set_index("framework")
    frameworks = ["numpy", "keras", "pytorch"]
    means = [subset.loc[name, "rmse_mean"] for name in frameworks]; errors = [subset.loc[name, "rmse_std"] for name in frameworks]
    naive = comparison[comparison["dataset_id"] == "ch4_aapl_next_close"]["naive_rmse"].iloc[0]
    axes[0].bar(frameworks + ["naive"], means + [naive], yerr=errors + [0], capsize=3,
                color=["#3566A8", "#D27B29", "#4F8A5B", "#888888"])
    axes[0].set_ylabel("RMSE (USD)"); axes[0].set_title("AAPL: RNN so với naive"); axes[0].grid(axis="y", alpha=.2)
    for framework in frameworks:
        history = pd.read_csv(METRIC_DIR / f"ch4_ch4_aapl_next_close_{framework}_history.csv")
        axes[1].plot(history["epoch"], history["val_loss"], marker="o", label=framework)
    axes[1].set_title("Validation MSE — seed 42"); axes[1].set_xlabel("Epoch"); axes[1].set_ylabel("MSE trên training scale")
    axes[1].legend(); axes[1].grid(alpha=.2); fig.tight_layout()
    fig.savefig(FIGURE_DIR / "ch4_stock_rmse_and_validation.png", dpi=180); plt.close(fig)


def main():
    METRIC_DIR.mkdir(parents=True, exist_ok=True); FIGURE_DIR.mkdir(parents=True, exist_ok=True); MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    comparison_path = METRIC_DIR / "ch4_framework_comparison.csv"
    comparison = reproduce_metrics(pd.read_csv(comparison_path), repair=True)
    comparison.to_csv(comparison_path, index=False)
    reproduce_metrics(comparison)
    summary = aggregate_framework_results(comparison); summary.to_csv(METRIC_DIR / "ch4_framework_summary.csv", index=False)
    import_a06_reference(); create_dataset_summary()
    _plot_dataset_overview(); _plot_customer_metrics(summary); _plot_customer_curves(comparison)
    _plot_customer_confusions(comparison); _plot_stock_predictions(comparison); _plot_stock_rmse_and_histories(comparison, summary)
    manifest = [{"path": str(path.relative_to(TERM_ROOT)).replace("\\", "/"), "sha256": sha256_file(path), "bytes": path.stat().st_size} for path in sorted(FIGURE_DIR.glob("*.png"))]
    (MANIFEST_DIR / "figure_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Chapter 4 reporting complete: {len(comparison)} runs, {len(manifest)} figures")


if __name__ == "__main__":
    main()
