"""Acceptance checks for Phase 3 artifacts, models, notebook, and manuscript."""

import hashlib
import json
import re
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from PIL import Image

from term_paper.src.common.ch2_metrics import metrics_from_prediction_csv
from term_paper.src.keras_impl.mlp import KerasMLP
from term_paper.src.pytorch_impl.mlp import TorchMLP
from term_paper.src.scratch.mlp import NumpyMLP


ROOT = Path(__file__).resolve().parents[2]
DATASETS = {
    "ch2_diabetes_binary": {"task": "binary", "test": 13812, "input": 21},
    "ch2_vietnam_housing": {"task": "regression", "test": 6045, "input": 143},
    "ch2_ecommerce_behavior": {"task": "binary", "test": 2000, "input": 368},
}
FRAMEWORKS = {"numpy": NumpyMLP, "keras": KerasMLP, "pytorch": TorchMLP}
SEEDS = {42, 52, 62}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def required_files():
    paths = [
        ROOT / "term_paper/src/scratch/mlp.py",
        ROOT / "term_paper/src/keras_impl/mlp.py",
        ROOT / "term_paper/src/pytorch_impl/mlp.py",
        ROOT / "term_paper/src/common/ch2_data.py",
        ROOT / "term_paper/src/common/run_ch2_experiments.py",
        ROOT / "term_paper/notebooks/ch2_ml_framework_comparison.ipynb",
        ROOT / "term_paper/report/sections/02_ml_co_ban.md",
        ROOT / "term_paper/artifacts/metrics/ch2_framework_comparison.csv",
        ROOT / "term_paper/artifacts/metrics/ch2_framework_summary.csv",
        ROOT / "term_paper/artifacts/metrics/ch2_classical_baselines.csv",
        ROOT / "term_paper/artifacts/metrics/ch2_best_vs_classical.csv",
        ROOT / "term_paper/artifacts/metrics/ch2_dataset_summary.csv",
        ROOT / "term_paper/config/ch2_experiment.json",
    ]
    paths.extend(sorted((ROOT / "term_paper/tests").glob("test_ch2_*.py")))
    for path in paths:
        require(path.is_file() and path.stat().st_size > 0, f"Missing or empty file: {path}")


def verify_notebook():
    path = ROOT / "term_paper/notebooks/ch2_ml_framework_comparison.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    require(notebook["nbformat"] == 4, "Notebook must use nbformat 4")
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    require(len(code_cells) >= 5, "Notebook needs at least five code cells")
    require(all(cell.get("execution_count") is not None for cell in code_cells), "Notebook is not fully executed")
    errors = [
        output
        for cell in code_cells
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]
    require(not errors, "Notebook contains error output")


def verify_comparison_and_predictions():
    path = ROOT / "term_paper/artifacts/metrics/ch2_framework_comparison.csv"
    comparison = pd.read_csv(path)
    require(len(comparison) == 27, f"Expected 27 run rows, found {len(comparison)}")
    require(set(comparison["dataset_id"]) == set(DATASETS), "Dataset set mismatch")
    require(set(comparison["framework"]) == set(FRAMEWORKS), "Framework set mismatch")
    require(set(comparison["seed"].astype(int)) == SEEDS, "Seed set mismatch")
    require(
        not comparison.duplicated(["dataset_id", "framework", "seed"]).any(),
        "Duplicate dataset/framework/seed row",
    )
    for dataset_id, spec in DATASETS.items():
        group = comparison[comparison["dataset_id"] == dataset_id]
        require(len(group) == 9, f"{dataset_id} must have nine runs")
        for column in ("split_sha256", "processed_sha256", "preprocessor_sha256"):
            require(group[column].nunique() == 1, f"{dataset_id} has inconsistent {column}")
        expected_parameters = (
            (spec["input"] * 64 + 64) + (64 * 32 + 32) + (32 * 1 + 1)
        )
        require(
            set(group["parameter_count"].astype(int)) == {expected_parameters},
            f"{dataset_id} parameter count mismatch",
        )
        split_path = (
            ROOT
            / "term_paper/artifacts/manifests/ch2"
            / f"{dataset_id}_split_keys.csv"
        )
        split_frame = pd.read_csv(split_path, dtype={"sample_key": str})
        test_keys = (
            split_frame[split_frame["split"] == "test"]
            .sort_values("row_order")["sample_key"]
            .astype(str)
            .tolist()
        )
        require(len(test_keys) == spec["test"], f"{dataset_id} TEST manifest size mismatch")
        metadata_path = (
            ROOT / "term_paper/artifacts/manifests/ch2" / f"{dataset_id}_metadata.json"
        )
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        preprocessor_path = ROOT / metadata["preprocessor"]
        require(sha256_file(preprocessor_path) == metadata["preprocessor_sha256"], "Preprocessor hash mismatch")
        joblib.load(preprocessor_path)
        processed_path = ROOT / metadata["processed_npz"]
        require(sha256_file(processed_path) == metadata["processed_sha256"], "Processed hash mismatch")
        with np.load(processed_path, allow_pickle=False) as arrays:
            x_sample = arrays["x_test"][:32]
        for _, row in group.iterrows():
            prediction_path = ROOT / row["prediction_path"]
            model_path = ROOT / row["model_path"]
            require(prediction_path.is_file(), f"Missing prediction: {prediction_path}")
            require(model_path.is_file(), f"Missing model: {model_path}")
            require(sha256_file(prediction_path) == row["prediction_sha256"], "Prediction hash mismatch")
            require(sha256_file(model_path) == row["model_sha256"], "Model hash mismatch")
            predictions = pd.read_csv(prediction_path, dtype={"sample_key": str})
            require(len(predictions) == spec["test"], "Prediction sample count mismatch")
            require(predictions["sample_key"].astype(str).tolist() == test_keys, "Prediction keys/order mismatch")
            require(not predictions["sample_key"].duplicated().any(), "Duplicate prediction key")
            recomputed = metrics_from_prediction_csv(prediction_path)
            for metric, value in recomputed.items():
                require(
                    np.isclose(float(row[metric]), float(value), atol=1e-12, rtol=0),
                    f"Metric mismatch {dataset_id}/{row['framework']}/{row['seed']}/{metric}",
                )
            model = FRAMEWORKS[row["framework"]].load(model_path)
            loaded_output = model.predict_score(x_sample)
            if spec["task"] == "binary":
                expected = predictions["y_score"].to_numpy(dtype=float)[:32]
            else:
                transform = metadata["target_transform"]
                expected = np.expm1(
                    loaded_output * float(transform["std"]) + float(transform["mean"])
                )
                expected = np.maximum(expected, 0.0)
                loaded_output = expected
                expected = predictions["y_pred"].to_numpy(dtype=float)[:32]
            require(
                np.allclose(loaded_output, expected, atol=1e-5, rtol=1e-6),
                f"Saved-model prediction parity failed: {model_path}",
            )
    return comparison


def verify_aggregates_and_figures(comparison):
    summary = pd.read_csv(ROOT / "term_paper/artifacts/metrics/ch2_framework_summary.csv")
    require(len(summary) == 9, "Framework summary must have nine rows")
    require(set(summary["seed_count"].astype(int)) == {3}, "Every summary row needs three seeds")
    classical = pd.read_csv(ROOT / "term_paper/artifacts/metrics/ch2_classical_baselines.csv")
    for source, group in classical.groupby("source_path"):
        source_path = ROOT / source
        require(source_path.is_file(), f"Missing classical source: {source_path}")
        require(group["source_sha256"].nunique() == 1, "Classical source hash inconsistent")
        require(sha256_file(source_path) == group["source_sha256"].iloc[0], "Classical source hash mismatch")
    figures = sorted((ROOT / "term_paper/artifacts/figures/ch2").glob("*.png"))
    require(len(figures) == 4, f"Expected four Chapter 2 figures, found {len(figures)}")
    for path in figures:
        require(path.stat().st_size > 50_000, f"Figure too small: {path}")
        with Image.open(path) as image:
            require(image.width >= 2000 and image.height >= 700, f"Figure resolution too low: {path}")


def verify_manuscript():
    path = ROOT / "term_paper/report/sections/02_ml_co_ban.md"
    text = path.read_text(encoding="utf-8")
    words = re.findall(r"[\wÀ-ỹ]+(?:[-–][\wÀ-ỹ]+)*", re.sub(r"\[@[^\]]+\]", " ", text))
    require(5500 <= len(words) <= 7000, f"Chapter 2 word count outside range: {len(words)}")
    for prefix in [f"## 2.{index}." for index in range(1, 9)]:
        require(re.search(r"^" + re.escape(prefix), text, flags=re.MULTILINE), f"Missing heading {prefix}")
    for prefix in (
        "### 2.1.1.", "### 2.1.2.", "### 2.2.1.", "### 2.2.2.",
        "### 2.2.3.", "### 2.2.4.", "### 2.3.1.", "### 2.3.2.",
        "### 2.4.1.", "### 2.4.2.", "### 2.4.3.", "### 2.5.1.",
        "### 2.5.2.", "### 2.5.3.", "### 2.6.1.", "### 2.6.2.",
        "### 2.6.3.", "### 2.7.1.", "### 2.7.2.",
    ):
        require(re.search(r"^" + re.escape(prefix), text, flags=re.MULTILINE), f"Missing heading {prefix}")
    require(len(re.findall(r"^\*\*Bảng 2\.", text, flags=re.MULTILINE)) == 5, "Expected five tables")
    require(len(re.findall(r"^!\[Hình 2\.", text, flags=re.MULTILINE)) == 4, "Expected four figures")
    require(not re.search(r"https?://", text), "Raw URL found in Chapter 2")
    require(not re.search(r"(?i)\b(TODO|TBD|FIXME|XXX)\b", text), "Placeholder found")
    require(not re.search(r"[A-Za-z]:\\", text), "Absolute local path found")
    bibliography = (ROOT / "term_paper/sources/bibliography.bib").read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"^@[A-Za-z]+\{([^,]+),", bibliography, flags=re.MULTILINE))
    citation_keys = set(re.findall(r"@([A-Za-z0-9_-]+)", text))
    require(citation_keys.issubset(bib_keys), f"Missing citation keys: {citation_keys - bib_keys}")
    return len(words), len(citation_keys)


def main():
    required_files()
    verify_notebook()
    comparison = verify_comparison_and_predictions()
    verify_aggregates_and_figures(comparison)
    word_count, citation_count = verify_manuscript()
    print("PHASE 3 VERIFICATION: PASS")
    print(f"Run rows: {len(comparison)}")
    print(f"Prediction rows: {sum(int(value) for value in comparison['sample_count'])}")
    print("Saved models load-checked: 27")
    print("Figures: 4")
    print(f"Chapter 2 words: {word_count}")
    print(f"Chapter 2 citation keys: {citation_count}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"PHASE 3 VERIFICATION: FAIL: {exc}", file=sys.stderr)
        raise

