"""Synthetic fixtures test data policy, never substitute for measured EDA."""

import numpy as np
import pandas as pd
import pytest

from src.common.data_v3 import (
    audit_partitions,
    causal_windows,
    fit_tabular,
    grouped_split,
    linked_groups,
    matched_subset,
    rolling_folds,
    temporal_boundaries,
    transform_tabular,
)
from src.common.source_inspection import require


def grouped_fixture():
    ids = [f"r{i:03}" for i in range(120)]
    groups = [f"g{i // 2:03}" for i in range(120)]
    labels = [str(i // 2 % 2) for i in range(120)]
    return ids, groups, labels


def test_duplicate_and_property_linkage_is_transitive():
    assert linked_groups(["a", "a", "b", "c"], ["p", "q", "q", "r"]) == [0, 0, 0, 3]


def test_unknown_property_ids_do_not_link_every_missing_record():
    assert linked_groups(["a", "b"], [None, None]) == [0, 1]


def test_grouped_split_has_no_overlap_and_approximately_expected_ratios():
    ids, groups, labels = grouped_fixture()
    result = grouped_split(ids, groups, labels)
    assert sorted(len(result[name]) for name in ("train", "validation", "test")) == [18, 18, 84]
    assert audit_partitions(result, dict(zip(ids, groups, strict=True)))["group_overlap_count"] == 0


def test_grouped_split_is_order_independent():
    ids, groups, labels = grouped_fixture()
    assert grouped_split(ids, groups, labels) == grouped_split(ids[::-1], groups[::-1], labels[::-1])


def test_official_test_kept_and_train_pixel_duplicates_quarantined():
    ids, groups, labels = grouped_fixture()
    official = ids[-20:]
    groups[0] = groups[-1]
    result = grouped_split(ids, groups, labels, official_test=official, validation_fraction=0.1)
    assert result["test"] == sorted(official)
    assert ids[0] in result["quarantine"]
    assert ids[0] not in result["train"] + result["validation"]
    assert audit_partitions(result, dict(zip(ids, groups, strict=True)))["group_overlap_count"] == 0


def test_mixed_labels_of_identical_features_stay_grouped():
    ids, groups, labels = grouped_fixture()
    labels[1] = "1"
    audit_partitions(grouped_split(ids, groups, labels), dict(zip(ids, groups, strict=True)))


def test_split_rejects_nonunique_ids():
    with pytest.raises(ValueError):
        grouped_split(["x", "x"], ["a", "b"], [0, 1])


def test_audit_detects_group_leakage():
    with pytest.raises(ValueError):
        audit_partitions({"train": ["a"], "validation": ["b"], "test": ["c"]}, {"a": 1, "b": 1, "c": 2})


def test_audit_detects_id_leakage():
    with pytest.raises(ValueError):
        audit_partitions({"train": ["a"], "validation": ["a"], "test": ["c"]}, {"a": 1, "c": 2})


def test_subset_stable_stratified_and_exact_cap():
    ids, _, labels = grouped_fixture()
    result = matched_subset(ids, dict(zip(ids, labels, strict=True)), 20)
    assert len(result) == 20
    assert result == matched_subset(ids[::-1], dict(zip(ids, labels, strict=True)), 20)
    assert sum(int(x[1:]) // 2 % 2 for x in result) == 10


def test_subset_no_cap_keeps_all_train_only():
    assert matched_subset(["b", "a"], {"a": 0, "b": 1}, None) == ["a", "b"]


def test_preprocessing_fit_ignores_heldout_values_and_new_categories():
    train = pd.DataFrame({"x": [1.0, 3.0, np.nan], "city": ["A", "B", None]})
    contract = fit_tabular(train, ["a", "b", "c"])
    heldout = pd.DataFrame({"x": [9999.0, np.nan], "city": ["TEST_ONLY", "A"]})
    transformed = transform_tabular(heldout, contract)
    assert contract["numeric"]["x"]["median"] == 2.0
    assert "TEST_ONLY" not in contract["categorical"]["city"]
    assert transformed.shape[1] == contract["output_width"]
    assert np.isfinite(transformed).all()


def test_all_missing_train_numeric_gets_explicit_zero_fallback():
    contract = fit_tabular(pd.DataFrame({"x": [np.nan, np.nan]}), ["a", "b"])
    assert contract["numeric"]["x"]["all_missing_fallback"] is True
    assert np.array_equal(transform_tabular(pd.DataFrame({"x": [np.nan]}), contract), [[0]])


def test_preprocessing_empty_train_is_rejected():
    with pytest.raises(ValueError):
        fit_tabular(pd.DataFrame({"x": []}), [])


def temporal_fixture():
    dates = pd.date_range("2000-01-01", periods=100, freq="MS")
    frame = pd.DataFrame({"time": dates, "series": "X", "target": np.arange(100.0), "x": np.arange(100.0)})
    return frame, temporal_boundaries(dates)


def test_windows_all_horizons_stay_inside_one_partition():
    frame, cuts = temporal_fixture()
    windows, excluded = causal_windows(frame, ["x"], 4, [1, 3, 6], cuts)
    assert excluded["cross_boundary"] > 0
    for row in windows:
        assert row["context_end"] < min(row["target_times"])
        if row["partition"] == "train":
            assert max(row["target_times"]) <= cuts[0]
        if row["partition"] == "test":
            assert min(row["target_times"]) > cuts[1]


def test_missing_future_labels_are_never_imputed():
    frame, cuts = temporal_fixture()
    frame.loc[10, "target"] = np.nan
    windows, excluded = causal_windows(frame, ["x"], 4, [1], cuts)
    assert excluded["missing_target"] == 1
    assert not any(row["target_times"] == [frame.time[10].isoformat()] for row in windows)


def test_duplicate_series_time_is_rejected():
    frame, cuts = temporal_fixture()
    with pytest.raises(ValueError):
        causal_windows(pd.concat([frame, frame.iloc[[0]]]), ["x"], 4, [1], cuts)


def test_temporal_missing_periods_cannot_be_treated_as_adjacent():
    frame, cuts = temporal_fixture()
    frame = frame.drop(index=20)
    with pytest.raises(ValueError):
        causal_windows(frame, ["x"], 4, [1], cuts)


def test_rolling_folds_never_touch_final_test():
    frame, cuts = temporal_fixture()
    folds = rolling_folds(frame.time, cuts[1])
    assert len(folds) == 3
    assert all(f["train_end"] < f["validation_start"] <= f["validation_end"] <= cuts[1] for f in folds)


def test_require_uses_value_error_contract():
    with pytest.raises(ValueError):
        require(False, "synthetic failure")
