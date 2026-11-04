"""Acceptance guards use synthetic states only, not fabricated dataset evidence."""

import pytest

from scripts.verify_phase23 import check_acquisition_state, check_provenance_lock
from src.common.acquisition import AcquisitionError


@pytest.mark.parametrize("state", ["declared", "pending_user_download", "rejected"])
def test_automatic_source_cannot_be_accepted_before_ready(state):
    with pytest.raises(AcquisitionError, match="ready"):
        check_acquisition_state({"chapter": 3, "dataset_id": "ch3_cifar10", "status": state, "files": []})


def test_automatic_ready_source_is_accepted():
    check_acquisition_state({"chapter": 2, "dataset_id": "ch2_ames_housing", "status": "ready", "files": []})


def test_only_idrid_can_have_explicit_manual_deferral():
    check_acquisition_state(
        {"chapter": 3, "dataset_id": "ch3_idrid", "status": "pending_user_download", "files": []}
    )


def test_pending_manual_source_cannot_claim_file_evidence():
    with pytest.raises(AcquisitionError):
        check_acquisition_state(
            {
                "chapter": 3,
                "dataset_id": "ch3_idrid",
                "status": "pending_user_download",
                "files": [{"path": "unverified.zip"}],
            }
        )


def test_agent_view_must_remain_declared_and_not_duplicate_raw():
    check_acquisition_state(
        {"chapter": 6, "dataset_id": "ch6_house_tasks", "status": "declared", "files": []}
    )
    with pytest.raises(AcquisitionError):
        check_acquisition_state(
            {"chapter": 6, "dataset_id": "ch6_house_tasks", "status": "ready", "files": []}
        )


def test_lock_created_once_and_unchanged_rerun_does_not_rewrite(tmp_path):
    path = tmp_path / "lock.json"
    files = [{"path": "data/registry.yaml", "sha256": "a" * 64, "size_bytes": 5}]
    check_provenance_lock(path, files, create_lock=True)
    before = path.read_bytes()
    check_provenance_lock(path, files, create_lock=True)
    assert path.read_bytes() == before


def test_lock_mismatch_is_not_replaced_even_with_lock_flag(tmp_path):
    path = tmp_path / "lock.json"
    check_provenance_lock(path, [], create_lock=True)
    before = path.read_bytes()
    with pytest.raises(AcquisitionError, match="changed"):
        check_provenance_lock(path, [{"path": "tampered"}], create_lock=True)
    assert path.read_bytes() == before


def test_absent_lock_requires_explicit_first_acceptance(tmp_path):
    path = tmp_path / "missing.json"
    with pytest.raises(AcquisitionError, match="first"):
        check_provenance_lock(path, [], create_lock=False)
    assert not path.exists()


def test_provenance_text_paths_keep_lf_on_windows_checkout():
    import subprocess

    from src.common.contracts import ROOT

    paths = [
        "data/registry.yaml",
        "artifacts/manifests/datasets/ch3_eurosat/archive_members.jsonl",
        "artifacts/manifests/datasets/ch3_eurosat.json",
        "report/references/dataset_cards/v3/ch3_eurosat.md",
    ]
    result = subprocess.run(
        ["git", "check-attr", "eol", "--", *paths], cwd=ROOT, text=True, capture_output=True, check=True
    )
    assert all(line.endswith(": eol: lf") for line in result.stdout.splitlines())
    assert len(result.stdout.splitlines()) == len(paths)
