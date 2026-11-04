"""Post-TEST QA reads stored results, executes TRAIN-only portable notebooks."""

import re
import sys

import nbformat
import numpy as np

from src.ch03_cnn.protocol import BASE, DATASETS, METRICS
from src.common.artifact_core import sha256_file
from src.common.contracts import ROOT, read_json, validate_document
from src.common.model_core import render_functions


def test_derived_tables_and_chapter_images():
    rows = read_json(METRICS / "tables/runs.json")
    summary = read_json(METRICS / "tables/aggregate.json")
    assert len(rows) == 72 and len(summary) == 288
    for item in summary:
        selected = [r for r in rows if all(r[key] == item[key] for key in ("dataset_id", "method", "split"))]
        assert {r["seed"] for r in selected} == {17, 42, 73}
        values = [r[item["metric"]] for r in selected if r[item["metric"]] is not None]
        assert len(values) == item["n"]
        if values:
            np.testing.assert_allclose(item["mean"], np.mean(values), rtol=1e-12, atol=1e-12)
            np.testing.assert_allclose(item["sample_std"], np.std(values, ddof=1), rtol=1e-12, atol=1e-12)
        else:
            assert item["mean"] is None and item["undefined_reason"]
    assert len(read_json(METRICS / "tables/per_class_recall.json")) == 75
    active = read_json(BASE / "active_report.json")
    generation = read_json(ROOT / active["generation"]["path"])
    assert sha256_file(ROOT / active["generation"]["path"]) == active["generation"]["sha256"]
    assert generation["revision"] == "r2" and generation["test_forward_executed"] is False
    original = read_json(BASE / "report_generation.json")
    for item in [original["manuscript"], *original["figures"], *original["tables"]]:
        assert sha256_file(ROOT / item["path"]) == item["sha256"]
    for item in [generation["manuscript"], *generation["figures"]]:
        assert sha256_file(ROOT / item["path"]) == item["sha256"]
    assert generation["tables"] == original["tables"]
    assert len(generation["figures"]) == 14
    path = ROOT / generation["manuscript"]["path"]
    text = path.read_text(encoding="utf-8")
    images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    assert len(images) == 10 and all((path.parent / name).resolve().is_file() for name in images)
    assert "TODO" not in text and "PLACEHOLDER" not in text
    assert all(
        label in text
        for label in (
            "scratch",
            "Keras",
            "PyTorch",
            "IDRiD",
            "EuroSAT",
            "CIFAR-10",
            "7 lớp",
            "3.6. Triển khai",
        )
    )


def test_api_jobs_and_train_only_saliency():
    export = read_json(BASE / "demo/export.json")
    registry = read_json(BASE / "trained_contract_registry.json")
    assert export["status"] == "PASS" and len(export["datasets"]) == 3
    assert len(registry["models"]) == 36
    for model in registry["models"]:
        if model["family"] != "cnn":
            continue
        contract = read_json(ROOT / model["model_contract"]["path"])
        validate_document("model", contract, publish=True)
        assert (
            sum(
                layer["kind"] in {"conv2d", "dense"} and layer["parameter_count"] > 0
                for layer in contract["layers"]
            )
            == 7
        )
        rendered = render_functions(contract)
        assert read_json(BASE / "runs" / model["model_id"] / "functions.json") == {
            k: v for k, v in rendered.items() if k != "markdown"
        }
    for dataset in DATASETS:
        job = read_json(BASE / "demo" / f"{dataset}_job.json")
        validate_document("api#job", job)
        assert job["comparison_valid"] and {r["actual_backend"] for r in job["results"]} == {"numpy"}
        assert {r["actual_device"] for r in job["results"]} == {"cpu"}
        for method in ("scratch", "keras", "pytorch"):
            data = read_json(BASE / "saliency" / f"{dataset}_cnn_{method}_s42.json")
            heat = np.asarray(data["map"])
            assert data["input_split"] == "train" and np.isfinite(heat).all()
            assert 0 <= heat.min() <= heat.max() <= 1


def test_notebooks_execute_without_native_frameworks_or_test_forward():
    export = read_json(BASE / "demo/export.json")
    for row in export["datasets"]:
        path = ROOT / row["notebook"]["path"]
        assert sha256_file(path) == row["notebook"]["sha256"]
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        namespace = {}
        assert len(notebook.cells) == 6
        assert "không phải ba native GPU runtime" in notebook.cells[0].source
        assert "sample_request" in notebook.cells[2].source
        assert "TEST was not executed" in notebook.cells[-1].source
        for cell in notebook.cells:
            if cell.cell_type == "code":
                # Execute only the reviewed producer output pinned by export manifest.
                exec(compile(cell.source, str(path), "exec"), namespace)  # noqa: S102
        assert namespace["job"]["comparison_valid"]
        assert len(namespace["rows"]) == 12
    assert not any(name in sys.modules for name in ("torch", "tensorflow", "keras"))
