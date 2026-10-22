"""Exercise complete pre-TEST workflow with synthetic references, never real TEST."""

import pytest

from src.ch02_ml import workflow
from src.common.artifact_core import write_once


def test_complete_matrix_reference_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "ROOT", tmp_path)
    monkeypatch.setattr(workflow, "BASE", tmp_path / "manifests")
    monkeypatch.setattr(
        workflow,
        "ref",
        lambda path: {"path": path.relative_to(tmp_path).as_posix(), "sha256": workflow.sha256_file(path)},
    )
    runs = workflow.run_ids()
    entries = []

    def put(path, document):
        write_once(path, document)
        return {"path": path.relative_to(tmp_path).as_posix(), "sha256": workflow.sha256_file(path)}

    config = put(tmp_path / "config.json", {"provenance": {"split_sha256": "a" * 64}})
    contract = put(tmp_path / "contract.json", {"synthetic_fixture": True})
    demo = put(tmp_path / "demo.json", {"status": "PASS", "input_split": "train"})
    for run in runs:
        dataset = next(ds for ds in workflow.DATASETS if run.startswith(ds))
        entry = {
            "run_id": run,
            "method": "synthetic_classical_fixture",
            "dataset_id": dataset,
            "config": config,
            "model_contract": contract,
        }
        metric = put(tmp_path / (run + ".json"), {"run_id": run, "split": "validation"})
        selection = {
            "run_id": run,
            "status": "succeeded",
            "selection_split": "validation",
            "inference_ready": True,
            "config": config,
            "model_contract": contract,
            "validation_metrics": metric,
            "cpu_demo": demo,
        }
        put(workflow.BASE / "runs" / run / "selection.json", selection)
        entries.append(entry)
    release = {"runs": entries, "expected_run_ids": runs, "code": {"dirty_tree_sha256": "b" * 64}}
    assert len(workflow.selections(release)) >= 54
    monkeypatch.setattr(workflow, "check_sources", lambda: release)
    put(workflow.BASE / "release.json", release)
    put(workflow.BASE / "pretest_verification.json", {"status": "PASS", "code_sha256": "b" * 64})
    assert workflow.lock_tests()["approved_runs"] == 54
    assert workflow.lock_tests()["status"] == "PASS"
    # Changing one approved CPU-demo status invalidates the selected group.
    (tmp_path / "demo.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        workflow.selections(release)
