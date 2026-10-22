"""Real generated report/notebook acceptance; reads saved outputs, no TEST forward."""

import csv
import re

from src.ch04_rnn_lstm.phase29.protocol import BASE, checked
from src.common.contracts import ROOT, read_json, validate_document


def test_report_tables_keep300_rows_and_original_orphan_null_cost():
    statistics = read_json(BASE / "report_statistics.json")
    assert statistics["status"] == "PASS" and statistics["run_rows"] == 300
    for record in statistics["tables"] + statistics["figures"]:
        checked(record)
    with (BASE / "tables/runs.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 300 and sum(r["split"] == "test" for r in rows) == 60
    orphan = [r for r in rows if r["run_id"] == "ch4_household_power_rnn_pytorch_s17_main"]
    assert len(orphan) == 2
    assert all(r[k] == "" for r in orphan for k in ("train_seconds", "peak_ram_bytes", "peak_vram_bytes"))


def test_three_executed_notebooks_serve18_independent_cpu_checkpoint_slots():
    export = read_json(BASE / "demo/export.json")
    assert export["status"] == "PASS" and export["models_loaded"] == 18
    assert len(export["notebooks"]) == 3 and not export["new_test_forward_executed"]
    jobs = []
    for record in export["artifacts"]:
        path = checked(record)
        if path.name.endswith("_job.json"):
            job = read_json(path)
            validate_document("api#job", job)
            assert len(job["results"]) == 3 and job["comparison_valid"]
            assert all(r["actual_backend"] == "numpy" and r["actual_device"] == "cpu" for r in job["results"])
            jobs.append(job)
    assert len(jobs) == 6
    for dataset in {j["dataset_id"] for j in jobs}:
        assert len({j["input_sha256"] for j in jobs if j["dataset_id"] == dataset}) == 1


def test_combined_chapter_has_both_families_code_functions_and9_existing_figures():
    manuscript = read_json(BASE / "manuscript_generation.json")["manuscript"]
    text = checked(manuscript).read_text(encoding="utf-8")
    assert text.startswith("# CHƯƠNG 4.") and "RNN–LSTM" in text
    for token in (
        "LSTM6",
        "RNN6",
        "keras.layers.LSTM",
        "lstm_layer",
        "BPTT",
        "hợp các hàm",
        "failed_sealed",
        "17 run",
        "4.9. Triển khai",
    ):
        assert token in text
    figures = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    assert len(figures) == 9
    for path in figures:
        assert ((ROOT / manuscript["path"]).parent / path).resolve().is_file()


def test_final_registry_is_evaluated_not_initialized_and_keeps_default_seed42():
    registry = read_json(BASE / "trained_registry.json")
    assert registry["default_seed"] == 42 and len(registry["models"]) == 60
    for row in registry["models"]:
        checked(row["checkpoint"])
        checked(row["test_result"])
        assert row["inference_ready"] and row["lifecycle"] != "initialized_only"
