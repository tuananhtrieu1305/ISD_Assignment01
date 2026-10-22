"""Append-only provenance revisions: preserve old metadata, never duplicate raw data."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from src.common.acquisition import file_digest, safe_member_name
from src.common.contracts import read_json
from src.common.source_inspection import require

IDRID_CHANGED_PATHS = {
    "data/registry.yaml",
    "artifacts/manifests/datasets/ch3_idrid.json",
    "report/references/dataset_cards/v3/ch3_idrid.md",
}


def repo_path(root, relative):
    root = Path(root).resolve()
    relative = safe_member_name(relative)
    require(
        relative.split("/")[0] in {"data", "artifacts", "report", "experiments"}, "Unexpected provenance path"
    )
    path = root / relative
    require(
        path.resolve().is_relative_to(root) and not path.is_symlink(), "Provenance path escaped repository"
    )
    return path


def matches(path, record):
    return (
        path.is_file()
        and not path.is_symlink()
        and path.stat().st_size == record["size_bytes"]
        and file_digest(path) == record["sha256"]
    )


def verify_parent_snapshot(root, parent):
    lock = repo_path(root, parent["lock_path"])
    require(file_digest(lock) == parent["sha256"], "Parent lock changed")
    document = read_json(lock)
    snapshot = repo_path(root, parent["snapshot_root"])
    for record in document["files"]:
        # First validate the logical path; snapshot resolution is constrained too.
        repo_path(root, record["path"])
        target = snapshot / record["path"]
        require(
            target.resolve().is_relative_to(snapshot.resolve()) and matches(target, record),
            f"Parent metadata snapshot changed: {record['path']}",
        )
    return document


def preserve_snapshot(root, lock_path, snapshot_relative):
    root = Path(root).resolve()
    lock_path = Path(lock_path)
    snapshot = repo_path(root, snapshot_relative)
    document = read_json(lock_path)
    for record in document["files"]:
        require(not record["path"].startswith("data/raw/"), "Never duplicate raw data into metadata snapshot")
        source = repo_path(root, record["path"])
        target = snapshot / record["path"]
        require(target.resolve().is_relative_to(snapshot.resolve()), "Snapshot target escaped")
        if target.exists():
            require(matches(target, record), f"Existing parent snapshot changed: {record['path']}")
            continue
        require(matches(source, record), f"Current bytes do not match old lock: {record['path']}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as incoming, target.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
        require(matches(target, record), "Snapshot copy integrity failed")
    parent = {
        "lock_path": lock_path.relative_to(root).as_posix(),
        "sha256": file_digest(lock_path),
        "snapshot_root": snapshot_relative,
    }
    verify_parent_snapshot(root, parent)
    return parent


def check_revision_scope(root, parent, current_files):
    previous = verify_parent_snapshot(root, parent)
    old = {row["path"]: row for row in previous["files"]}
    current = {row["path"]: row for row in current_files}
    require(set(old) <= set(current), "A provenance revision cannot remove old evidence")
    for path, record in old.items():
        if path not in IDRID_CHANGED_PATHS:
            require(current[path] == record, f"Unrelated evidence changed: {path}")
    old_registry = yaml.safe_load(
        (repo_path(root, parent["snapshot_root"]) / "data/registry.yaml").read_text(encoding="utf-8")
    )
    registry = yaml.safe_load((Path(root) / "data/registry.yaml").read_text(encoding="utf-8"))
    old_entries = {row["id"]: row for row in old_registry["datasets"]}
    entries = {row["id"]: row for row in registry["datasets"]}
    require(set(old_entries) == set(entries), "Dataset matrix changed during IDRiD import")
    require(
        all(entries[key] == row for key, row in old_entries.items() if key != "ch3_idrid"),
        "Non-IDRiD registry entries changed",
    )
    for path in set(current) - set(old):
        require(
            path.startswith(
                ("artifacts/manifests/datasets/ch3_idrid/", "artifacts/manifests/phase23/updates/idrid_")
            ),
            "Unrelated provenance addition",
        )
    return len(old)
