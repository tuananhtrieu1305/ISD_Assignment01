"""Post-training evidence, functions, portable serving and notebook execution."""

import re
import sys

import nbformat
import numpy as np

from src.ch04_rnn_lstm.protocol import BASE, DATASETS, IMPLEMENTATIONS, METRICS, ROOT, checked
from src.common.contracts import read_json, validate_document
from src.common.model_core import render_functions


def test_validation_tables_figures_and_no_test_claim():
    rows = read_json(METRICS / "tables/runs.json")
    summary = read_json(METRICS / "tables/aggregate.json")
    assert len(rows) == 132 and len(summary) == 660
    assert len(read_json(METRICS / "tables/horizons.json")) == 396
    assert len(read_json(METRICS / "tables/horizon_aggregate.json")) == 540
    for entry in summary:
        selected = [r for r in rows if all(r[k] == entry[k] for k in ("dataset_id", "method", "fold"))]
        expected = {17, 42, 73} if entry["method"] in IMPLEMENTATIONS else {42}
        assert {r["seed"] for r in selected} == expected
        values = [r[entry["metric"]] for r in selected if r.get(entry["metric"]) is not None]
        assert len(values) == entry["n"]
        if values:
            np.testing.assert_allclose(entry["mean"], np.mean(values), rtol=1e-12)
            if len(values) > 1:
                np.testing.assert_allclose(entry["sample_std"], np.std(values, ddof=1), rtol=1e-12)
            else:
                assert entry["sample_std"] is None
        else:
            assert entry["mean"] is None and entry["undefined_reason"]
    manuscript = ROOT / "report/sections/v3/ch04_rnn.md"
    text = manuscript.read_text(encoding="utf-8")
    images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    assert len(images) == 7 and all((manuscript.parent / p).resolve().is_file() for p in images)
    assert "VALIDATION" in text and "chưa phải TEST" in text
    assert "TODO" not in text and "PLACEHOLDER" not in text
    assert not (METRICS / "test").exists() and not (BASE / "test_seals").exists()
    power_torch = [r for r in summary if r["dataset_id"] == "ch4_household_power"
                   and r["method"] == "pytorch" and r["fold"] is None]
    assert all(r["n"] == 2 for r in power_torch if r["metric"] in {"train_seconds", "peak_ram_bytes", "peak_vram_bytes"})
    assert all(r["n"] == 3 for r in power_torch if r["metric"] in {"rmse", "mae", "smape"})


def test_validation_registry_compositions_and_cpu_jobs():
    registry = read_json(BASE / "trained_validation_registry.json")
    assert len(registry["models"]) == 132 and registry["test_evaluation_executed"] is False
    for entry in registry["models"]:
        assert entry["test_evaluation_executed"] is False
        if entry["family"] != "rnn":
            continue
        contract = read_json(checked(entry["model_contract"]))
        validate_document("model", contract, publish=True)
        assert (
            sum(
                layer["kind"] in {"rnn", "dense"} and layer["parameter_count"] > 0
                for layer in contract["layers"]
            )
            == 6
        )
        functions = render_functions(contract)
        assert read_json(BASE / "runs" / entry["model_id"] / "functions.json") == {
            k: v for k, v in functions.items() if k != "markdown"
        }
    handoff = read_json(BASE / "holdout_handoff.json")
    assert len(handoff["rnn_run_ids"]) == 27 and len(handoff["baseline_run_ids"]) == 6
    assert handoff["test_evaluation_executed"] is False
    for dataset in DATASETS:
        job = read_json(BASE / "demo" / f"{dataset}_job.json")
        validate_document("api#job", job)
        assert job["comparison_valid"] and len(job["results"]) == 3
        assert {r["actual_backend"] for r in job["results"]} == {"numpy"}
        assert {r["actual_device"] for r in job["results"]} == {"cpu"}
        assert all(len(r["prediction"]["values"]) == 3 for r in job["results"])
    smoke = read_json(BASE / "cpu_smoke.json")
    assert smoke["status"] == "PASS" and smoke["models_loaded"] == 9


def test_notebooks_execute_train_only_without_native_frameworks():
    export = read_json(BASE / "demo/export.json")
    assert export["status"] == "PASS" and len(export["datasets"]) == 3
    for item in export["datasets"]:
        path = checked(item["notebook"])
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        assert len(notebook.cells) == 6
        namespace = {}
        for cell in notebook.cells:
            if cell.cell_type == "code":
                exec(compile(cell.source, str(path), "exec"), namespace)  # noqa: S102
        assert namespace["job"]["comparison_valid"]
        assert len(namespace["rows"]) == 11
    assert not any(name in sys.modules for name in ("torch", "tensorflow", "keras"))
