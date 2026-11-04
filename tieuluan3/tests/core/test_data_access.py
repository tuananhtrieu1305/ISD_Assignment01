"""Read-only integration against all nine locked preprocessing contracts."""

import json

import numpy as np
import pytest

from src.common.contracts import ROOT, read_json
from src.common.data_access import DatasetView
from src.common.tensor_adapters import TensorAdapter

DATASETS = [
    row["dataset_id"]
    for row in read_json(ROOT / "data/catalog_v3.json")["datasets"]
    if row["chapter"] in {2, 3, 4}
]


@pytest.mark.parametrize("dataset", DATASETS)
def test_real_contract_order_and_train_batch(dataset):
    view = DatasetView(dataset)
    assert view.provenance["preprocessing_sha256"]
    with pytest.raises(ValueError):
        view.ids("test")
    with pytest.raises(ValueError):
        view.ids("quarantine")
    ids = view.ids("train")[:2]
    x, y = view.batch(ids, "scratch")
    assert len(x) == len(y) == 2 and x.dtype == np.float32 and np.isfinite(x).all() and np.isfinite(y).all()
    if view.kind != "image":
        first = TensorAdapter(view.preprocessing)
        second = TensorAdapter(json.loads(json.dumps(view.preprocessing, sort_keys=True)))
        assert first.output_feature_names == second.output_feature_names
        assert first.output_feature_names == view.adapter_contract["output_feature_names"]
        frame = view._frame[view.preprocessing["input_columns"]].head(3)
        np.testing.assert_array_equal(first.transform(frame), second.transform(frame))
    else:
        px, py = view.batch(ids, "pytorch")
        np.testing.assert_array_equal(px.transpose(0, 2, 3, 1), x)
        np.testing.assert_array_equal(py, y)
    with pytest.raises(ValueError):
        view.batch(["missing_id"], "scratch")


def test_reject_nontraining_catalog_entry():
    for dataset in ["ch1_iris_history", "ch5_finqa", "ch6_gold_tasks", "not_a_dataset"]:
        with pytest.raises(ValueError):
            DatasetView(dataset)


def test_series_cache_missing_reconstructs_identical_tensors(monkeypatch):
    from pathlib import Path

    view = DatasetView("ch4_gold_pink_sheet")
    ids = view.ids("train")[:2]
    expected = view.batch(ids, "scratch")
    receipt = read_json(view.base / "series_cache.json")
    cache = ROOT / receipt["path"]
    original_exists = Path.exists
    monkeypatch.setattr(Path, "exists", lambda path: False if path == cache else original_exists(path))
    actual = DatasetView("ch4_gold_pink_sheet").batch(ids, "scratch")
    for first, second in zip(expected, actual, strict=True):
        np.testing.assert_array_equal(first, second)
