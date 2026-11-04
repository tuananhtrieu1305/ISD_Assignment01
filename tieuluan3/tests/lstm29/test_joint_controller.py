"""Pretest orchestration cannot open real TEST while the training queue is active."""

import pytest

from scripts import phase29_joint_test
from src.common.artifact_core import write_once


def test_joint_lock_requires_finished_controller_and_all_108_selections(tmp_path, monkeypatch):
    monkeypatch.setattr(phase29_joint_test, "BASE", tmp_path)
    release = {"runs": [{"run_id": f"synthetic_{i}"} for i in range(108)]}
    write_once(tmp_path / "active_controller.json", {"pid": 1234, "status": "running"})
    with pytest.raises(ValueError, match="controller"):
        phase29_joint_test.ensure_training_complete(release)
    (tmp_path / "active_controller.json").write_text('{"pid":null,"status":"finished"}')
    with pytest.raises(ValueError, match="selection"):
        phase29_joint_test.ensure_training_complete(release)
    assert not (tmp_path / "test_seals").exists()


def test_controller_requires_exact_training_matrix(tmp_path, monkeypatch):
    monkeypatch.setattr(phase29_joint_test, "BASE", tmp_path)
    write_once(tmp_path / "active_controller.json", {"pid": None, "status": "finished"})
    with pytest.raises(ValueError, match="108"):
        phase29_joint_test.ensure_training_complete({"runs": []})
