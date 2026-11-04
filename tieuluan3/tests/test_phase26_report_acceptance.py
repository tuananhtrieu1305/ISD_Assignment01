"""Post-evaluation report QA over saved metrics and TRAIN-only demo notebooks."""

import csv
import re
import sys

import nbformat
import numpy as np

from src.ch02_ml.protocol import DATASETS, METRICS
from src.common.contracts import ROOT


def test_derived_tables_and_manuscript_images():
    with (METRICS / "tables/runs.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    with (METRICS / "tables/aggregate.csv").open(encoding="utf-8", newline="") as stream:
        summary = list(csv.DictReader(stream))
    assert len(rows) == 108 and len(summary) == 564
    for item in summary:
        values = [
            float(row[item["metric"]])
            for row in rows
            if all(row[key] == item[key] for key in ("dataset_id", "method", "split"))
            and row[item["metric"]] != ""
        ]
        assert len(values) == int(item["n"]) == 3
        np.testing.assert_allclose(float(item["mean"]), np.mean(values), rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(float(item["sample_std"]), np.std(values, ddof=1), rtol=1e-12, atol=1e-12)
    path = ROOT / "report/sections/v3/ch02_ml.md"
    text = path.read_text(encoding="utf-8")
    images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    assert len(images) == 5 and all((path.parent / name).resolve().is_file() for name in images)
    assert "TODO" not in text and "PLACEHOLDER" not in text
    assert "scratch" in text and "Keras" in text and "PyTorch" in text


def test_three_notebooks_execute_train_only_without_importing_gpu_frameworks():
    before = set(sys.modules)
    for dataset in DATASETS:
        path = ROOT / "experiments/notebooks/v3/ch02_ml" / (dataset + ".ipynb")
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        namespace = {}
        expected = "\n".join(
            [
                "from pathlib import Path",
                "import os",
                "repo = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / 'TIEU_LUAN_AI_V3_EXECUTION_PLAN.md').exists())",
                "os.chdir(repo)",
                "from scripts.demo_phase26 import demo",
                f"result = demo('{dataset}', seed=42)",
                "result",
            ]
        )
        for cell in notebook.cells:
            if cell.cell_type == "code":
                assert cell.source == expected
                # Execute the reviewed literal test program, never arbitrary notebook content.
                exec(compile(expected, str(path), "exec"), namespace)  # noqa: S102
        result = namespace["result"]
        assert result["dataset_id"] == dataset and result["input_split"] == "train"
        assert len(result["models"]) == 6
    added = set(sys.modules) - before
    assert not any(
        name == prefix or name.startswith(prefix + ".")
        for name in added
        for prefix in ("tensorflow", "torch")
    )
