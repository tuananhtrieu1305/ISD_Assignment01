"""Artifact reproducibility and train-derived descriptive thresholds."""

import numpy as np
import pandas as pd
import pytest

from src.common.eda_artifacts import clean, describe_frame, read_rows, write_rows


@pytest.mark.parametrize("value", [pd.NaT, pd.NA, np.nan, np.inf])
def test_unavailable_values_are_null_not_a_fabricated_zero(value):
    assert clean(value) is None


def test_real_zero_is_preserved():
    assert clean(0.0) == 0.0


def test_compressed_index_is_byte_reproducible(tmp_path):
    first, second = tmp_path / "a.jsonl.gz", tmp_path / "b.jsonl.gz"
    records = [{"id": "x", "value": 1}, {"id": "y", "value": None}]
    write_rows(first, records)
    write_rows(second, records)
    assert first.read_bytes() == second.read_bytes()
    assert read_rows(first) == records


def test_outlier_fence_fitted_only_on_train():
    frame = pd.DataFrame({"x": [0.0, 1.0, 2.0, 3.0, 10000.0]})
    result = describe_frame(frame, ["a", "b", "c", "d", "e"], ["a", "b", "c", "d"])
    assert result["numeric"]["x"]["iqr_upper_train"] == 4.5
    assert result["numeric"]["x"]["outlier_count_full_source"] == 1


def test_all_missing_feature_remains_missing_in_eda():
    result = describe_frame(pd.DataFrame({"x": [float("nan")] * 4}), list("abcd"), list("abc"))
    assert result["missing"]["x"] == 4
    assert result["numeric"]["x"]["median"] is None
