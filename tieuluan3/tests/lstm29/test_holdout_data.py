"""Synthetic reader tests: never open any real Chapter4 TEST window."""

from types import SimpleNamespace
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest

from src.ch04_rnn_lstm.phase29 import holdout_data


@pytest.fixture
def synthetic(monkeypatch):
    frame = pd.DataFrame(
        {
            "time": pd.date_range("2000-01-01", periods=9, freq="D"),
            "series": ["S"] * 9,
            "target": np.arange(9, dtype="float64"),
            "feature": np.arange(9, dtype="float64"),
        }
    )
    row = {
        "id": "test_a",
        "series": "S",
        "partition": "test",
        "start_index": 3,
        "origin_index": 5,
        "target_indices": [6, 7],
        "context_start": frame.time.iloc[3].isoformat(),
        "context_end": frame.time.iloc[5].isoformat(),
        "target_times": [frame.time.iloc[i].isoformat() for i in (6, 7)],
    }
    calls = []

    class Adapter:
        state: ClassVar = {"input_columns": ["feature"]}

        def transform(self, values):
            calls.append(values.index.tolist())
            return values.to_numpy("float32")

        def target(self, y):
            return y.astype("float32")

    def fake_development(self, dataset):
        self.dataset_id = dataset
        self.fold = None
        self.frame = frame
        self.rows = {"test_a": row}
        self.features = np.full((9, 1), np.nan, "float32")
        self.adapter = Adapter()
        self.lookback = 3
        self.horizons = [1, 2]
        self.allowed = {"train_a"}
        self.view = SimpleNamespace(split_dir=holdout_data.ROOT / "synthetic_only", spec={"seasonality": 2})

    monkeypatch.setattr(holdout_data.WindowData, "__init__", fake_development)
    monkeypatch.setattr(holdout_data, "read_rows", lambda p: ["test_a"])
    monkeypatch.setattr(holdout_data, "sha256_file", lambda p: "a" * 64)
    monkeypatch.setattr(
        holdout_data,
        "read_json",
        lambda p: {
            "partitions": [
                {"name": "validation", "target_end": frame.time.iloc[5].isoformat()},
                {
                    "name": "test",
                    "ids": {"path": "synthetic_only/test.ids.jsonl.gz", "sha256": "a" * 64},
                    "target_start": frame.time.iloc[6].isoformat(),
                    "target_end": frame.time.iloc[8].isoformat(),
                },
            ]
        },
    )

    class Gate:
        root = holdout_data.ROOT / "synthetic_only"

        def materialize(self, code):
            calls.append("consumed")

        def _check(self, code, allowed):
            return {}, {"dataset_id": "ch4_gold_pink_sheet"}

    return Gate(), frame, row, calls


def test_holdout_reader_consumes_before_transform_and_gathers_only_causal_context(synthetic):
    gate, frame, _, calls = synthetic
    data = holdout_data.HoldoutData(gate, "a" * 64)
    assert calls[0] == "consumed" and calls[-1] == [3, 4, 5]
    x, y = data.batch(data.test_ids)
    np.testing.assert_array_equal(x[:, :, 0], [[3, 4, 5]])
    np.testing.assert_array_equal(y, [[6, 7]])
    assert data.targets(data.test_ids).dtype == np.float64
    np.testing.assert_array_equal(data.baseline(data.test_ids, "last_value"), [[5, 5]])
    with pytest.raises(ValueError):
        data.batch(["train_a"])
    with pytest.raises(ValueError):
        data.batch(["test_a", "test_a"])
    assert np.isnan(data.features[6:]).all()
    frame.loc[7, "target"] = np.nan
    with pytest.raises(ValueError):
        data.targets(data.test_ids)


@pytest.mark.parametrize(
    "fault",
    [
        "future",
        "wrong_series",
        "early_target",
        "bad_calendar",
        "wrong_partition",
        "short_context",
        "missing_label",
    ],
)
def test_holdout_reader_rejects_noncausal_or_inconsistent_source(synthetic, fault):
    gate, frame, row, _ = synthetic
    if fault == "future":
        row["target_indices"] = [5, 7]
    elif fault == "wrong_series":
        frame.loc[7, "series"] = "other"
    elif fault == "early_target":
        row["target_indices"] = [5, 6]
    elif fault == "bad_calendar":
        row["target_times"][0] = "1900-01-01"
    elif fault == "wrong_partition":
        row["partition"] = "validation"
    elif fault == "short_context":
        row["start_index"] = 4
    else:
        frame.loc[7, "target"] = np.nan
    with pytest.raises(ValueError):
        holdout_data.HoldoutData(gate, "a" * 64)
