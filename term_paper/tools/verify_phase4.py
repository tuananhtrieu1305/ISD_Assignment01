"""End-to-end acceptance verifier for Phase 4."""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from term_paper.src.common.ch3_data import WORKSPACE_ROOT
from term_paper.src.common.ch3_experiment import sha256_file
from term_paper.src.common.ch3_metrics import multiclass_metrics
from term_paper.src.common.run_ch3_experiments import (
    _load_model,
    validate_matched_prediction_keys,
)


TERM_ROOT = WORKSPACE_ROOT / "term_paper"
METRIC_DIR = TERM_ROOT / "artifacts" / "metrics"
MANIFEST_DIR = TERM_ROOT / "artifacts" / "manifests" / "ch3"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def verify_runs():
    comparison = pd.read_csv(METRIC_DIR / "ch3_framework_comparison.csv")
    require(len(comparison) == 18, f"expected 18 run rows, found {len(comparison)}")
    require(set(comparison["dataset_id"]) == {"ch3_eurosat", "ch3_diabetes_012"}, "datasets")
    require(set(comparison["framework"]) == {"numpy", "keras", "pytorch"}, "frameworks")
    require(set(comparison["seed"].astype(int)) == {42, 52, 62}, "seeds")
    prediction_count = 0
    load_count = 0
    for dataset_id, dataset_rows in comparison.groupby("dataset_id"):
        metadata = json.loads(
            (MANIFEST_DIR / f"{dataset_id}_metadata.json").read_text(encoding="utf-8")
        )
        require(dataset_rows["split_sha256"].nunique() == 1, f"split hash drift: {dataset_id}")
        require(
            dataset_rows["preprocessor_sha256"].nunique() == 1,
            f"preprocessor hash drift: {dataset_id}",
        )
        require(
            dataset_rows["split_sha256"].iloc[0] == metadata["split_sha256"],
            f"metadata split mismatch: {dataset_id}",
        )
        require(
            dataset_rows["preprocessor_sha256"].iloc[0] == metadata["preprocessor_sha256"],
            f"metadata preprocessor mismatch: {dataset_id}",
        )
        for seed, seed_rows in dataset_rows.groupby("seed"):
            frames = {}
            require(seed_rows["parameter_count"].nunique() == 1, "parameter count mismatch")
            for _, row in seed_rows.iterrows():
                prediction_path = TERM_ROOT / row["prediction_path"]
                model_path = TERM_ROOT / row["model_path"]
                require(prediction_path.exists(), str(prediction_path))
                require(model_path.exists(), str(model_path))
                require(sha256_file(prediction_path) == row["prediction_sha256"], "prediction hash")
                require(sha256_file(model_path) == row["model_sha256"], "model hash")
                frame = pd.read_csv(prediction_path)
                frames[row["framework"]] = frame
                probability_columns = sorted(
                    [column for column in frame if column.startswith("prob_")],
                    key=lambda value: int(value.split("_")[1]),
                )
                probabilities = frame[probability_columns].to_numpy(dtype=float)
                np.testing.assert_allclose(probabilities.sum(axis=1), 1.0, atol=1e-6)
                np.testing.assert_array_equal(frame["y_pred"], np.argmax(probabilities, axis=1))
                reproduced = multiclass_metrics(
                    frame["y_true"], frame["y_pred"], labels=range(len(probability_columns))
                )
                for key, value in reproduced.items():
                    if key in comparison.columns:
                        require(np.isclose(float(row[key]), float(value), atol=1e-12), f"{key}")
                with np.load(MANIFEST_DIR / f"{dataset_id}_processed.npz", allow_pickle=False) as data:
                    sample_x = data["x_test"][:8]
                model = _load_model(row["framework"], model_path)
                loaded_probability = model.predict_proba(sample_x)
                np.testing.assert_allclose(
                    loaded_probability, probabilities[:8], atol=1e-6, rtol=0
                )
                prediction_count += len(frame)
                load_count += 1
            validate_matched_prediction_keys(frames)
    return comparison, prediction_count, load_count


def verify_a05_and_figures():
    ablation = pd.read_csv(METRIC_DIR / "ch3_a05_architecture_ablation.csv")
    require(len(ablation) == 12, "A05 ablation must contain 12 CNN rows")
    euro_deep = ablation[
        (ablation["dataset_id"] == "a05_eurosat") & (ablation["key"] != "basic")
    ]
    require((euro_deep["macro_f1"] <= 0.0200001).all(), "EuroSAT collapse not preserved")
    oxford = ablation[ablation["dataset_id"] == "a05_oxford_pets"]
    require((oxford["macro_f1"] < 0.021).all(), "Oxford near-random result changed")
    manifest = json.loads((MANIFEST_DIR / "a05_ablation_provenance.json").read_text())
    for entry in manifest:
        path = WORKSPACE_ROOT / entry["artifact"]
        require(sha256_file(path) == entry["sha256"], f"A05 source changed: {path}")
    figures = sorted((TERM_ROOT / "artifacts" / "figures" / "ch3").glob("*.png"))
    require(len(figures) >= 5, "expected at least five Chapter 3 figures")
    for figure in figures:
        require(figure.stat().st_size > 20_000, f"figure too small: {figure}")
    return len(figures)


def verify_notebook_and_chapter():
    notebook_path = TERM_ROOT / "notebooks" / "ch3_cnn_framework_comparison.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    require(code_cells, "notebook has no code")
    require(all(cell.get("execution_count") is not None for cell in code_cells), "unexecuted cell")
    errors = [
        output
        for cell in code_cells
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]
    require(not errors, "notebook contains error output")
    chapter_path = TERM_ROOT / "report" / "sections" / "03_cnn.md"
    chapter = chapter_path.read_text(encoding="utf-8")
    words = len(re.findall(r"\b[\wÀ-ỹ–-]+\b", chapter, flags=re.UNICODE))
    require(5200 <= words <= 7200, f"Chapter 3 word count out of range: {words}")
    require(len(re.findall(r"^## 3\.[1-8]\.", chapter, flags=re.MULTILINE)) == 8, "H2 coverage")
    require(len(re.findall(r"^### 3\.", chapter, flags=re.MULTILINE)) >= 18, "H3 coverage")
    require(len(re.findall(r"^!\[", chapter, flags=re.MULTILINE)) >= 5, "figure references")
    require("collapse" in chapter.lower() and "Oxford" in chapter, "failure results omitted")
    citation_groups = re.findall(r"\[(@[^\]]+)\]", chapter)
    citation_keys = set()
    for group in citation_groups:
        citation_keys.update(part.strip().lstrip("@").strip() for part in group.split(";") if part.strip())
    bibliography = (TERM_ROOT / "sources" / "bibliography.bib").read_text(encoding="utf-8")
    bibliography_keys = set(re.findall(r"@\w+\{([^,]+),", bibliography))
    require(citation_keys.issubset(bibliography_keys), f"missing citations: {citation_keys-bibliography_keys}")
    return words, len(citation_keys)


def main():
    comparison, predictions, loaded = verify_runs()
    figures = verify_a05_and_figures()
    words, citations = verify_notebook_and_chapter()
    summary = pd.read_csv(METRIC_DIR / "ch3_framework_summary.csv")
    require(len(summary) == 6, "summary rows")
    print("PHASE 4 VERIFICATION: PASS")
    print(f"Run rows: {len(comparison)}")
    print(f"Prediction rows: {predictions}")
    print(f"Saved models load-checked: {loaded}")
    print(f"Figures: {figures}")
    print(f"Chapter 3 words: {words}")
    print(f"Chapter 3 citation keys: {citations}")


if __name__ == "__main__":
    main()
