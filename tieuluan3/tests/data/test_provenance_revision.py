"""Synthetic metadata fixtures verify immutable parent snapshots, not dataset results."""

import hashlib
import json

import pytest

from src.common.acquisition import AcquisitionError
from src.common.provenance import check_revision_scope, preserve_snapshot, verify_parent_snapshot


def fixture(tmp_path):
    source = tmp_path / "data/registry.yaml"
    source.parent.mkdir()
    source.write_bytes(b"old registry\n")
    lock = tmp_path / "artifacts/manifests/phase23/dataset_lock.json"
    lock.parent.mkdir(parents=True)
    files = [
        {
            "path": "data/registry.yaml",
            "size_bytes": 13,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
    ]
    lock.write_text(json.dumps({"files": files}))
    return lock


def test_parent_snapshot_survives_current_metadata_update(tmp_path):
    lock = fixture(tmp_path)
    parent = preserve_snapshot(tmp_path, lock, "artifacts/manifests/phase23/snapshots/base")
    (tmp_path / "data/registry.yaml").write_text("new registry")
    assert verify_parent_snapshot(tmp_path, parent)["files"][0]["size_bytes"] == 13


def test_parent_lock_tampering_is_detected(tmp_path):
    lock = fixture(tmp_path)
    parent = preserve_snapshot(tmp_path, lock, "artifacts/manifests/phase23/snapshots/base")
    lock.write_text("{}")
    with pytest.raises(AcquisitionError):
        verify_parent_snapshot(tmp_path, parent)


def test_parent_snapshot_tampering_is_detected(tmp_path):
    lock = fixture(tmp_path)
    parent = preserve_snapshot(tmp_path, lock, "artifacts/manifests/phase23/snapshots/base")
    (tmp_path / parent["snapshot_root"] / "data/registry.yaml").write_text("bad")
    with pytest.raises(AcquisitionError):
        preserve_snapshot(tmp_path, lock, parent["snapshot_root"])


def test_changed_current_bytes_cannot_be_blessed_as_parent(tmp_path):
    lock = fixture(tmp_path)
    (tmp_path / "data/registry.yaml").write_text("bad")
    with pytest.raises(AcquisitionError):
        preserve_snapshot(tmp_path, lock, "artifacts/manifests/phase23/snapshots/base")


def test_snapshot_path_cannot_escape_repository(tmp_path):
    lock = fixture(tmp_path)
    with pytest.raises(AcquisitionError):
        preserve_snapshot(tmp_path, lock, "../outside")


def revision_fixture(tmp_path):
    source = tmp_path / "data/registry.yaml"
    source.parent.mkdir()
    registry = {
        "datasets": [
            {"id": "ch3_idrid", "status": "pending_user_download"},
            {"id": "ch2_ames_housing", "status": "ready"},
        ]
    }
    source.write_text(json.dumps(registry))
    protected = tmp_path / "report/protected.md"
    protected.parent.mkdir()
    protected.write_text("unchanged")

    def records():
        return [
            {
                "path": p.relative_to(tmp_path).as_posix(),
                "size_bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in (source, protected)
        ]

    lock = tmp_path / "artifacts/manifests/phase23/dataset_lock.json"
    lock.parent.mkdir(parents=True)
    lock.write_text(json.dumps({"files": records()}))
    parent = preserve_snapshot(tmp_path, lock, "artifacts/manifests/phase23/snapshots/base")
    registry["datasets"][0]["status"] = "ready"
    source.write_text(json.dumps(registry))
    return parent, registry, source, protected, records


def test_revision_changes_only_idrid_entry(tmp_path):
    parent, _, _, _, records = revision_fixture(tmp_path)
    assert check_revision_scope(tmp_path, parent, records()) == 2


def test_revision_rejects_unrelated_metadata_changes(tmp_path):
    parent, _, _, protected, records = revision_fixture(tmp_path)
    protected.write_text("bad")
    with pytest.raises(AcquisitionError, match="Unrelated"):
        check_revision_scope(tmp_path, parent, records())


def test_revision_rejects_changes_to_other_dataset_entries(tmp_path):
    parent, registry, source, _, records = revision_fixture(tmp_path)
    registry["datasets"][1]["status"] = "rejected"
    source.write_text(json.dumps(registry))
    with pytest.raises(AcquisitionError, match="Non-IDRiD"):
        check_revision_scope(tmp_path, parent, records())


def test_revision_only_adds_scoped_idrid_evidence(tmp_path):
    parent, _, _, _, records = revision_fixture(tmp_path)
    new_file = {
        "path": "artifacts/manifests/datasets/ch3_idrid/archive_members.jsonl",
        "size_bytes": 0,
        "sha256": "a" * 64,
    }
    assert check_revision_scope(tmp_path, parent, records() + [new_file]) == 2
    new_file["path"] = "report/unrelated.md"
    with pytest.raises(AcquisitionError, match="Unrelated"):
        check_revision_scope(tmp_path, parent, records() + [new_file])


def test_revision_cannot_remove_previous_evidence(tmp_path):
    parent, _, _, _, records = revision_fixture(tmp_path)
    with pytest.raises(AcquisitionError, match="remove"):
        check_revision_scope(tmp_path, parent, records()[:1])
