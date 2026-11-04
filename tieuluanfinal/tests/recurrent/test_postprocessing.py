"""Read-only audit/input guards; no real TEST evaluation."""

import copy

import numpy as np
import pytest

from scripts.demo_phase28 import decode_request, sample_request
from scripts.verify_phase28 import audit_prediction_rows
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.metric_core import regression_metrics


def test_saved_forecast_audit_preserves_ids_labels_and_metrics():
    data = WindowData("ch4_gold_pink_sheet")
    ids = data.validation_ids
    target = data.targets(ids)
    prediction = data.baseline(ids, "last_value")
    rows = [
        {
            "id": key,
            "series": data.rows[key]["series"],
            "target_times": data.rows[key]["target_times"],
            "target": y.tolist(),
            "prediction": p.tolist(),
        }
        for key, y, p in zip(ids, target, prediction, strict=True)
    ]
    metrics = regression_metrics(target, prediction, data.horizons, data.series(ids))
    assert audit_prediction_rows(data, rows, metrics) == len(ids)
    bad = copy.deepcopy(rows)
    bad[0]["target"][0] += 1
    with pytest.raises(ValueError):
        audit_prediction_rows(data, bad, metrics)
    with pytest.raises(ValueError):
        audit_prediction_rows(data, rows[::-1], metrics)
    with pytest.raises(ValueError):
        audit_prediction_rows(data, rows, {**metrics, "rmse": {"value": 0, "undefined_reason": None}})


@pytest.mark.parametrize("dataset", ["ch4_gold_pink_sheet", "ch4_bis_house_prices", "ch4_household_power"])
def test_cpu_request_shape_order_and_invalid_input(dataset):
    request, key = sample_request(dataset)
    x, adapter = decode_request(request)
    data = WindowData(dataset)
    reference, _ = data.batch([key])
    np.testing.assert_array_equal(x, reference)
    assert adapter.output_feature_names == data.adapter.output_feature_names
    bad = copy.deepcopy(request)
    bad["input"]["values"] = [[1.0]]
    with pytest.raises(ValueError):
        decode_request(bad)
    bad = copy.deepcopy(request)
    bad["family"] = "lstm"
    with pytest.raises(ValueError):
        decode_request(bad)


def test_missing_original_training_telemetry_is_excluded_not_replaced_by_zero():
    from scripts.summarize_phase28 import aggregate_rows

    rows = [{"dataset_id": "ch4_household_power", "method": "pytorch", "fold": None,
             "seed": seed, "rmse": 0.7, "train_seconds": seconds,
             "peak_ram_bytes": None if seconds is None else 100,
             "peak_vram_bytes": None if seconds is None else 200}
            for seed, seconds in [(17, None), (42, 10.0), (73, 20.0)]]
    aggregate = {r["metric"]: r for r in aggregate_rows(rows)}
    assert aggregate["rmse"]["n"] == 3
    assert aggregate["train_seconds"]["n"] == 2
    assert aggregate["train_seconds"]["mean"] == 15
    np.testing.assert_allclose(aggregate["train_seconds"]["sample_std"], np.std([10, 20], ddof=1))
    assert aggregate["peak_ram_bytes"]["n"] == 2
    assert aggregate["peak_vram_bytes"]["n"] == 2


def test_metric_row_order_roundtrip_is_semantic_not_json_key_order():
    from scripts.verify_phase28 import audit_metric_rows

    expected = [{"name": "rmse", "horizon": h, "value": 0.5 if h is None else float(h), "unit": "kW",
                 "undefined_reason": None, "direction": "min"} for h in (None, 1, 6, 24)]
    actual = [expected[i] for i in (0, 1, 3, 2)]
    assert audit_metric_rows(actual, expected) == 4
    bad = copy.deepcopy(actual)
    bad[0]["value"] += 1e-12
    with pytest.raises(ValueError):
        audit_metric_rows(bad, expected)
    with pytest.raises(ValueError):
        audit_metric_rows(actual + [actual[0]], expected)
    with pytest.raises(ValueError):
        audit_metric_rows(actual[:-1], expected)
