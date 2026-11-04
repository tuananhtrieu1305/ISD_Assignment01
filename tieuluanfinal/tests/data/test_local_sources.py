"""Optional integration against genuine local snapshots, never downloads substitutes."""

import pytest

from src.common.contracts import ROOT, read_json
from src.common.source_inspection import inspect_source

CATALOG = read_json(ROOT / "experiments/configs/v3/acquisition_sources.json")["sources"]


@pytest.mark.parametrize("dataset_id", CATALOG)
def test_genuine_local_source_schema(dataset_id):
    path = ROOT / CATALOG[dataset_id]["path"]
    if not path.is_file():
        pytest.skip("Genuine source snapshot not downloaded; no network in tests")
    inspection = inspect_source(dataset_id, path)
    assert inspection["records"] > 0
    assert inspection["checks"]


def test_idrid_no_manual_input_is_explicit_pending(tmp_path):
    from scripts.verify_idrid_manual import inspect_idrid

    result = inspect_idrid(tmp_path / "missing")
    assert result["status"] == "pending_user_download"
    assert result["records"] is None and result["files"] == []


def test_offline_mode_missing_file_never_calls_transport(tmp_path, monkeypatch):
    import scripts.acquire_datasets as script

    monkeypatch.setattr(script, "ROOT", tmp_path)
    monkeypatch.setattr(script, "RECEIPTS", tmp_path)
    monkeypatch.setattr(
        script,
        "read_json",
        lambda _: {"sources": {"tiny": {"path": "data.csv", "url": "https://example.org/file"}}},
    )
    monkeypatch.setattr(
        script, "download_file", lambda *a, **k: pytest.fail("Offline must never call transport")
    )
    with pytest.raises(ValueError, match="offline reuse"):
        script.acquire("tiny", offline=True)


def test_genuine_idrid_zip_includes_both_official_splits_and_license():
    from scripts.verify_idrid_manual import MANUAL, inspect_idrid

    if not list(MANUAL.glob("*.zip")):
        pytest.skip("User has not supplied the genuine IDRiD ZIP; never download in tests")
    result = inspect_idrid()
    assert result["records"] == 516 and result["license_status"] == "approved"
    assert result["official_split_counts"] == {"train": 413, "test": 103}
    assert result["native_image_shapes"] == [[4288, 2848, "RGB"]]
    assert "train/IDRiD_001" in result["labels"] and "test/IDRiD_001" in result["labels"]
