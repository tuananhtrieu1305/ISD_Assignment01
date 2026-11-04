"""Causal data contract, train-only scalers and matched-fold parity."""

import numpy as np
import pytest

from src.ch04_rnn_lstm.window_data import WindowData
from src.common.data_access import DatasetView
from src.common.tensor_adapters import window_batch

DATASETS = ("ch4_gold_pink_sheet", "ch4_bis_house_prices", "ch4_household_power")


@pytest.mark.parametrize("dataset", DATASETS)
@pytest.mark.parametrize("fold", [None, 1, 2, 3])
def test_batch_matches_frozen_reference(dataset, fold):
    data = WindowData(dataset, fold)
    view = DatasetView(dataset, fold)
    ids = data.train_ids[:2] + data.validation_ids[-2:]
    x, y = data.batch(ids)
    view._load()
    expected_x, expected_y = window_batch(view._frame, [data.rows[key] for key in ids], view.adapter)
    known = [key for key in ids if key in view._index]
    reference_x, reference_y = view.batch(known, "scratch")
    actual_x, actual_y = data.batch(known)
    np.testing.assert_array_equal(actual_x, reference_x)
    np.testing.assert_array_equal(actual_y, reference_y)
    np.testing.assert_array_equal(x, expected_x)
    np.testing.assert_array_equal(y, expected_y)
    assert data.feature_bytes < 64 * 1024**2
    assert x.dtype == np.float32 and y.shape == (4, 3)
    assert len(data.train_ids) == len(view.ids("train"))
    assert data.provenance["preprocessing_sha256"] == view.provenance["preprocessing_sha256"]
    if fold:
        assert data.provenance["split_sha256"] != DatasetView(dataset).provenance["split_sha256"]
    for key in ids:
        row = data.rows[key]
        assert min(row["target_indices"]) > row["origin_index"]
    for method in ("last_value", "seasonal_naive"):
        values = data.baseline(ids, method)
        assert values.shape == (4, 3) and np.isfinite(values).all()


def test_sealed_duplicate_unknown_and_empty_windows_refused():
    data = WindowData(DATASETS[0])
    for ids in ([], [data.train_ids[0]] * 2, ["unknown"], list(set(data.rows) - data.allowed)[:1]):
        with pytest.raises(ValueError):
            data.batch(ids)
    with pytest.raises(ValueError):
        data.baseline(data.train_ids[:1], "test")


def test_validation_targets_remain_original_float64():
    data = WindowData(DATASETS[0])
    ids = data.validation_ids[:2]
    _, normalized = data.batch(ids)
    original = data.targets(ids)
    assert original.dtype == np.float64
    assert np.max(np.abs(data.adapter.inverse_target(normalized) - original)) > 0


@pytest.mark.parametrize("dataset", DATASETS)
def test_fold_gap_mapping_keeps_frozen_ids_and_target_times(dataset):
    data = WindowData(dataset, 2)
    assert data.reconstructed_fold_ids
    x, y = data.batch(data.reconstructed_fold_ids)
    assert len(x) == len(data.reconstructed_fold_ids) and np.isfinite(y).all()
    for key in data.reconstructed_fold_ids:
        row = data.rows[key]
        assert key == f"{row['series']}/{data.frame.time.iloc[row['origin_index']].isoformat()}"
        assert row["target_indices"] == [row["origin_index"] + h for h in data.horizons]
        assert row["origin_index"] - row["start_index"] + 1 == data.lookback
