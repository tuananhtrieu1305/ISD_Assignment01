"""Synthetic end-to-end producer fixture, never part of measured benchmark."""

import numpy as np
import pytest

from src.ch03_cnn import experiment as exp
from src.ch03_cnn.image_cache import ImageCache
from src.ch03_cnn.workflow import CnnEvaluationGate
from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import canonical_sha256
from src.common.data_access import DatasetView
from src.common.model_core import build_plan, canonical_weights


@pytest.mark.parametrize("method", ["scratch", "majority"])
def test_synthetic_train_export_resume_and_reuse(tmp_path, monkeypatch, method):
    tmp_path = tmp_path / "artifacts"
    tmp_path.mkdir()
    view = DatasetView("ch3_cifar10")
    ids = view.ids("train")[:4] + view.ids("validation")[:2]
    view.ids = lambda partition: ids[:4] if partition == "train" else ids[4:]
    cache = ImageCache.create(
        tmp_path / "cache",
        ids,
        np.random.default_rng(9).integers(0, 255, (6, 8, 8, 3), dtype="uint8"),
        [0, 1, 2, 0, 1, 2],
        {},
        free_bytes=10**10,
    )

    def local_ref(path):
        return {"path": path.relative_to(tmp_path.parent).as_posix(), "sha256": sha256_file(path)}

    for key, value in {
        "ROOT": tmp_path.parent,
        "BASE": tmp_path / "manifest",
        "MODELS": tmp_path / "models",
        "METRICS": tmp_path / "metrics",
        "PREDICTIONS": tmp_path / "predictions",
        "ref": local_ref,
        "DatasetView": lambda _: view,
        "configure": lambda *args: "numpy",
        "development_cache": lambda _: (cache, view),
    }.items():
        monkeypatch.setattr(exp, key, value)
    plan = build_plan("cnn", [8, 8, 3], 10, tiny=True)
    config = {
        "task": "multiclass",
        "plan": plan,
        "training": {
            "max_epochs": 1,
            "patience": 6,
            "min_delta": 1e-5,
            "batch_size": 2,
            "wall_time_limit_minutes": 2,
        },
        "provenance": view.provenance,
        "adapter": {"sha256": "a" * 64},
        "code": {"git_commit": "0" * 40, "dirty_tree_sha256": "a" * 64},
        "environment_sha256": "a" * 64,
        "protocol_sha256": "b" * 64,
        "canonical_initial_weights_sha256": canonical_sha256(
            {k: v.tolist() for k, v in canonical_weights(plan, 17).items()}
        ),
        "cache_manifest": local_ref(cache.root / "manifest.json"),
        "class_weights": None,
        "class_names": view.adapter_contract["class_names"],
    }
    config_path = tmp_path / "config.json"
    contract_path = tmp_path / "contract.json"
    write_once(config_path, config)
    write_once(contract_path, {"fixture": "synthetic_not_a_benchmark"})
    run = f"ch3_cifar10_{method}_s17"
    entry = {
        "run_id": run,
        "dataset_id": "ch3_cifar10",
        "seed": 17,
        "method": method,
        "config": local_ref(config_path),
        "model_contract": local_ref(contract_path),
        "comparison_group_sha256": "b" * 64,
    }
    monkeypatch.setattr(exp, "check_sources", lambda: {"runs": [entry], "code": config["code"]})
    first = exp.train_run(run)
    assert first["status"] == "succeeded"
    assert exp.train_run(run)["status"] == "reused"
    if method == "scratch":
        state = exp.load_progress(run, entry["config"]["sha256"])
        assert len(state["history"]) == 1 and state["trainer"]["iterations"] == 2
        with pytest.raises(ValueError):
            exp.load_progress(run, "e" * 64)
    else:
        assert exp.load_progress(run, entry["config"]["sha256"]) is None
    # Entire evaluation path on synthetic heldout pixels in tmp only. No real
    # TEST IDs, labels, images, checkpoints or Phase27 seals are opened here.
    heldout = ImageCache.create(
        tmp_path / "synthetic_holdout",
        ["fixture_holdout_0", "fixture_holdout_1"],
        np.random.default_rng(11).integers(0, 255, (2, 8, 8, 3), dtype="uint8"),
        [0, 2],
        {"fixture": "synthetic_not_public_test"},
        free_bytes=10**10,
    )
    monkeypatch.setattr(exp, "test_partition_cache", lambda *args: (heldout, view, heldout.ids))
    gate = CnnEvaluationGate(exp.BASE / "test_seals" / "ch3_cifar10")
    gate.lock(
        {
            "dataset_id": "ch3_cifar10",
            "split_sha256": view.provenance["split_sha256"],
            "code_sha256": config["code"]["dirty_tree_sha256"],
            "runs": [run],
            "artifacts": [entry["config"], entry["model_contract"]],
        }
    )
    gate.begin(config["code"]["dirty_tree_sha256"])
    result = exp.evaluate_run(run)
    assert result["status"] == "PASS" and result["test_prediction_count"] == 2
    gate.complete()
    assert gate.state()["evaluation_count"] == 1
    with pytest.raises(ValueError):
        exp.evaluate_run(run)
