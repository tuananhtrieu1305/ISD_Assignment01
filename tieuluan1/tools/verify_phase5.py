"""End-to-end acceptance verifier for Phase 5."""

import json
import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from term_paper.src.common.ch4_data import WORKSPACE_ROOT
from term_paper.src.common.ch4_experiment import sha256_file
from term_paper.src.common.ch4_metrics import binary_metrics, regression_metrics
from term_paper.src.common.run_ch4_experiments import _load_model, validate_matched_prediction_keys


TERM_ROOT = WORKSPACE_ROOT / "term_paper"
METRIC_DIR = TERM_ROOT / "artifacts" / "metrics"
MANIFEST_DIR = TERM_ROOT / "artifacts" / "manifests" / "ch4"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def verify_runs():
    comparison = pd.read_csv(METRIC_DIR / "ch4_framework_comparison.csv")
    require(len(comparison) == 18, f"expected 18 runs, found {len(comparison)}")
    require(set(comparison["framework"]) == {"numpy", "keras", "pytorch"}, "frameworks")
    require(set(comparison["seed"].astype(int)) == {42, 52, 62}, "seeds")
    require(set(comparison["parameter_count"].astype(int)) == {1249}, "parameter parity")
    prediction_count = 0
    load_count = 0
    for dataset_id, dataset_rows in comparison.groupby("dataset_id"):
        metadata = json.loads((MANIFEST_DIR / f"{dataset_id}_metadata.json").read_text(encoding="utf-8"))
        require(dataset_rows["split_sha256"].nunique() == 1, f"split drift {dataset_id}")
        require(dataset_rows["preprocessor_sha256"].nunique() == 1, f"preprocessor drift {dataset_id}")
        processed = np.load(MANIFEST_DIR / f"{dataset_id}_processed.npz", allow_pickle=False)
        target_scaler = None
        if dataset_id == "ch4_aapl_next_close":
            target_scaler = joblib.load(WORKSPACE_ROOT / "A06/models/preprocessing/stock_target_scaler.joblib")
        for seed, seed_rows in dataset_rows.groupby("seed"):
            frames = {}
            for _, row in seed_rows.iterrows():
                prediction_path = TERM_ROOT / row["prediction_path"]
                model_path = TERM_ROOT / row["model_path"]
                require(sha256_file(prediction_path) == row["prediction_sha256"], "prediction hash")
                require(sha256_file(model_path) == row["model_sha256"], "model hash")
                frame = pd.read_csv(prediction_path); frames[row["framework"]] = frame
                if row["task"] == "binary":
                    metrics = binary_metrics(frame["y_true"], frame["score_or_prediction"], frame["threshold"].iloc[0])
                else:
                    metrics = regression_metrics(frame["y_true"], frame["score_or_prediction"])
                    naive = regression_metrics(frame["y_true"], frame["naive_last_close"])
                    metrics.update({f"naive_{key}": value for key, value in naive.items()})
                for key, value in metrics.items():
                    require(np.isclose(float(row[key]), float(value), atol=1e-12, rtol=0), f"metric {key}")
                model = _load_model(row["framework"], model_path)
                raw = model.predict_score(processed["x_test"][:8])
                prediction = raw if target_scaler is None else target_scaler.inverse_transform(raw.reshape(-1, 1)).reshape(-1)
                tolerance = 1e-6 if target_scaler is None else 1e-4
                np.testing.assert_allclose(prediction, frame["score_or_prediction"].to_numpy()[:8], atol=tolerance, rtol=0)
                prediction_count += len(frame); load_count += 1
            validate_matched_prediction_keys(frames)
        require(dataset_rows["split_sha256"].iloc[0] == metadata["split_sha256"], "metadata split hash")
    stock = comparison[comparison["task"] == "regression"]
    require((stock["rmse"] > stock["naive_rmse"]).all(), "AAPL failure result changed")
    return comparison, prediction_count, load_count


def verify_reporting():
    figures = sorted((TERM_ROOT / "artifacts/figures/ch4").glob("*.png"))
    require(len(figures) == 6, f"expected 6 figures, found {len(figures)}")
    require(all(path.stat().st_size > 20_000 for path in figures), "small figure")
    reference = pd.read_csv(METRIC_DIR / "ch4_a06_reference.csv")
    require(len(reference) == 5, "A06 reference rows")
    provenance = json.loads((MANIFEST_DIR / "a06_reference_provenance.json").read_text())
    require(sha256_file(WORKSPACE_ROOT / provenance["path"]) == provenance["sha256"], "A06 reference changed")
    return len(figures)


def verify_notebook_and_chapter():
    notebook = json.loads((TERM_ROOT / "notebooks/ch4_rnn_framework_comparison.ipynb").read_text(encoding="utf-8"))
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    require(code_cells and all(cell.get("execution_count") is not None for cell in code_cells), "unexecuted notebook")
    require(not [output for cell in code_cells for output in cell.get("outputs", []) if output.get("output_type") == "error"], "notebook error")
    chapter = (TERM_ROOT / "report/sections/04_rnn.md").read_text(encoding="utf-8")
    words = len(re.findall(r"\b[\wÀ-ỹ–-]+\b", chapter, flags=re.UNICODE))
    require(5200 <= words <= 7200, f"chapter word count {words}")
    require(len(re.findall(r"^## 4\.[1-8]\.", chapter, flags=re.MULTILINE)) == 8, "H2 coverage")
    require(len(re.findall(r"^### 4\.", chapter, flags=re.MULTILINE)) >= 16, "H3 coverage")
    require(len(re.findall(r"^!\[", chapter, flags=re.MULTILINE)) == 6, "figure references")
    require("không phải khuyến nghị" in chapter.lower(), "financial warning")
    keys = set()
    for group in re.findall(r"\[(@[^\]]+)\]", chapter):
        keys.update(part.strip().lstrip("@") for part in group.split(";"))
    bibliography = (TERM_ROOT / "sources/bibliography.bib").read_text(encoding="utf-8")
    bibliography_keys = set(re.findall(r"@\w+\{([^,]+),", bibliography))
    require(keys.issubset(bibliography_keys), f"missing citations {keys-bibliography_keys}")
    return words, len(keys)


def main():
    comparison, predictions, loaded = verify_runs()
    figures = verify_reporting()
    words, citations = verify_notebook_and_chapter()
    require(len(pd.read_csv(METRIC_DIR / "ch4_framework_summary.csv")) == 6, "summary rows")
    print("PHASE 5 VERIFICATION: PASS")
    print(f"Run rows: {len(comparison)}")
    print(f"Prediction rows: {predictions}")
    print(f"Saved models load-checked: {loaded}")
    print(f"Figures: {figures}")
    print(f"Chapter 4 words: {words}")
    print(f"Chapter 4 citation keys: {citations}")


if __name__ == "__main__":
    main()
