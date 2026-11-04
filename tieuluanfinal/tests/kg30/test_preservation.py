"""Paths and hashes are verified before reading or deserializing frozen artifacts."""

import hashlib

import pytest

from src.ch05_knowledge_rag.preservation import checked, verify_records


def test_checked_accepts_only_matching_workspace_bytes(tmp_path):
    path = tmp_path / "frozen.json"
    path.write_bytes(b"frozen")
    row = {"path": "frozen.json", "sha256": hashlib.sha256(b"frozen").hexdigest()}
    assert checked(row, tmp_path) == path
    assert verify_records([row], tmp_path) == 1
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="hash"):
        checked(row, tmp_path)


@pytest.mark.parametrize("path", ["../escape", "/etc/passwd", "a/../b", "C:/secret", "a\\b", ""])
def test_checked_rejects_unsafe_paths(tmp_path, path):
    with pytest.raises(ValueError):
        checked({"path": path, "sha256": "a" * 64}, tmp_path)


def test_missing_artifact_and_duplicate_refs_fail(tmp_path):
    row = {"path": "missing", "sha256": "a" * 64}
    with pytest.raises(ValueError):
        checked(row, tmp_path)
    path = tmp_path / "ok"
    path.write_bytes(b"ok")
    row = {"path": "ok", "sha256": hashlib.sha256(b"ok").hexdigest()}
    with pytest.raises(ValueError, match="Duplicate"):
        verify_records([row, row], tmp_path)
