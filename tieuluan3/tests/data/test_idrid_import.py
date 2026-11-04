"""Tiny synthetic JPEG/CSV fixtures test import rules, NOT genuine IDRiD evidence."""

import io
import zipfile

import pytest
from PIL import Image

import scripts.verify_idrid_manual as manual
from src.common.acquisition import AcquisitionError


def release_fixture(tmp_path, monkeypatch, *, bad_grade=False, duplicate_label=False, overlap_names=False):
    monkeypatch.setattr(manual, "ROOT", tmp_path)
    directory = tmp_path / "data/raw/ch3/idrid/manual"
    directory.mkdir(parents=True)
    jpeg = io.BytesIO()
    Image.new("RGB", (2, 2), "blue").save(jpeg, format="JPEG")
    archive_path = directory / "synthetic-grading.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for split, indices in (
            ("train", range(1, 414)),
            ("test", range(1, 104) if overlap_names else range(414, 517)),
        ):
            lines = ["Image name,Retinopathy grade"]
            for index in indices:
                key = f"IDRiD_{index:03}"
                archive.writestr(f"{split}/{key}.jpg", jpeg.getvalue())
                lines.append(f"{key},{8 if bad_grade and index == 1 else index % 5}")
            if duplicate_label and split == "train":
                lines.append("IDRiD_001,1")
            archive.writestr(f"{split}_labels.csv", "\n".join(lines) + "\n")
    return directory


def test_synthetic_complete_release_checks_counts_without_extracting(tmp_path, monkeypatch):
    directory = release_fixture(tmp_path, monkeypatch)
    result = manual.inspect_idrid(directory)
    assert result["records"] == 516
    assert result["official_split_counts"] == {"train": 413, "test": 103}
    assert len(result["labels"]) == 516
    assert not list(directory.rglob("*.jpg"))


def test_official_release_can_reuse_image_basename_across_splits(tmp_path, monkeypatch):
    directory = release_fixture(tmp_path, monkeypatch, overlap_names=True)
    result = manual.inspect_idrid(directory)
    assert result["records"] == 516
    assert "train/IDRiD_001" in result["labels"]
    assert "test/IDRiD_001" in result["labels"]
    assert result["identity_policy"] == "official_split/image_stem"


def test_ambiguous_official_split_name_rejected():
    with pytest.raises(AcquisitionError, match="split"):
        manual.official_split("train_test_labels.csv")


@pytest.mark.parametrize("problem", ["bad_grade", "duplicate_label"])
def test_invalid_grading_labels_rejected(tmp_path, monkeypatch, problem):
    directory = release_fixture(tmp_path, monkeypatch, **{problem: True})
    with pytest.raises(AcquisitionError):
        manual.inspect_idrid(directory)


def test_manual_archive_traversal_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(manual, "ROOT", tmp_path)
    with zipfile.ZipFile(tmp_path / "evil.zip", "w") as archive:
        archive.writestr("../outside.csv", "bad")
    with pytest.raises(AcquisitionError, match="Unsafe"):
        manual.inspect_idrid(tmp_path)


def test_incomplete_label_release_is_not_ready(tmp_path, monkeypatch):
    monkeypatch.setattr(manual, "ROOT", tmp_path)
    (tmp_path / "train.csv").write_text("Image name,Retinopathy grade\nIDRiD_001,1\n")
    with pytest.raises(AcquisitionError, match="413/103"):
        manual.inspect_idrid(tmp_path)


def test_manual_external_csv_has_same_small_bound_as_archive_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(manual, "ROOT", tmp_path)
    with (tmp_path / "train.csv").open("wb") as handle:
        handle.truncate(2 * 1024**2 + 1)
    with pytest.raises(AcquisitionError, match="CSV too large"):
        manual.inspect_idrid(tmp_path)


@pytest.mark.parametrize("include_full_text", [False, True])
def test_license_approval_requires_bundled_declaration_and_full_text(
    tmp_path, monkeypatch, include_full_text
):
    directory = release_fixture(tmp_path, monkeypatch)
    with zipfile.ZipFile(directory / "synthetic-grading.zip", "a") as archive:
        archive.writestr(
            "LICENSE.txt",
            "IDRiD dataset licensed under Creative Commons Attribution 4.0 International License.",
        )
        if include_full_text:
            archive.writestr("CC-BY-4.0.txt", "Creative Commons Attribution 4.0 International")
    result = manual.inspect_idrid(directory)
    assert result["license_status"] == ("approved" if include_full_text else "pending")
    assert len(result["license_evidence"]) == (2 if include_full_text else 1)
    assert manual.inspection_summary(result)["records"] == 516


def test_cli_require_ready_reports_pending_without_touching_real_data(tmp_path, monkeypatch):
    import sys

    monkeypatch.setattr(manual, "ROOT", tmp_path)
    monkeypatch.setattr(
        manual, "inspect_idrid", lambda: {"status": "pending_user_download", "files": [], "records": None}
    )
    monkeypatch.setattr(sys, "argv", ["verify_idrid_manual", "--require-ready"])
    assert manual.main() is True
