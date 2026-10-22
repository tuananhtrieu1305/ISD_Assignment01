"""Independent rejection tests for frozen EDA data contracts."""

import pandas as pd
import pytest

from scripts.verify_phase24 import audit_window_index, check_preprocessor, write_lock_once
from src.common.data_v3 import causal_windows, fit_tabular, temporal_boundaries


def fixture():
    dates = pd.date_range("2000-01-01", periods=100, freq="MS")
    frame = pd.DataFrame({"time": dates, "series": "X", "target": range(100), "x": range(100)})
    cuts = temporal_boundaries(dates)
    windows, _ = causal_windows(frame, ["x"], 4, [1, 3], cuts)
    return frame, cuts, windows


def test_phase24_lock_is_atomic_and_never_overwritten(tmp_path):
    path = tmp_path / "data_lock.json"
    write_lock_once(path, {"files": ["initial"]})
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_lock_once(path, {"files": ["changed"]})
    assert path.read_bytes() == original


def test_window_index_matches_real_series_offsets():
    frame, cuts, windows = fixture()
    assert audit_window_index(windows, frame, 4, [1, 3], cuts)["target_time_overlap_count"] == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("context_end", "2099-01-01T00:00:00"),
        ("target_indices", [1, 2]),
        ("partition", "test"),
        ("series", "OTHER"),
    ],
)
def test_forged_window_index_rejected(field, value):
    frame, cuts, windows = fixture()
    windows[0][field] = value
    with pytest.raises(ValueError):
        audit_window_index(windows, frame, 4, [1, 3], cuts)


def test_preprocessor_fit_ids_must_be_exactly_train_selection():
    frame = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
    prep = fit_tabular(frame, ["a", "b", "c"])
    check_preprocessor(prep, frame, ["a", "b", "c"])
    with pytest.raises(ValueError):
        check_preprocessor(prep, frame, ["a", "b", "TEST"])


def test_preprocessor_cannot_use_heldout_numeric_or_vocabulary():
    frame = pd.DataFrame({"x": [1.0, 2.0, 3.0], "cat": ["A", "B", "A"]})
    prep = fit_tabular(frame, ["a", "b", "c"])
    prep["numeric"]["x"]["median"] = 999
    with pytest.raises(ValueError):
        check_preprocessor(prep, frame, ["a", "b", "c"])
    prep = fit_tabular(frame, ["a", "b", "c"])
    prep["categorical"]["cat"].append("TEST_ONLY")
    with pytest.raises(ValueError):
        check_preprocessor(prep, frame, ["a", "b", "c"])
