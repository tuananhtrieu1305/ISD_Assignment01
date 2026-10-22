"""Phase25: canonical tensors must survive sorted JSON serialization."""

import copy
import json

import numpy as np
import pandas as pd
import pytest

from src.common.tensor_adapters import TensorAdapter, image_batch, select_rows, window_batch


def state():
    return {
        "input_columns": ["z", "a", "kind"],
        "numeric": {"z": {"median": 2, "mean": 2, "std": 2}, "a": {"median": 10, "mean": 10, "std": 5}},
        "categorical": {"kind": ["__missing__", "b", "a"]},
        "output_width": 5,
        "fit_scope": "train_only",
        "target_transform": {"name": "standardize", "mean": 100, "std": 20},
    }


def test_order_roundtrip_and_unknown_missing():
    frame = pd.DataFrame({"kind": ["a", "new", None], "a": [15, None, 10], "z": [4, 2, np.inf]})
    first = TensorAdapter(state())
    second = TensorAdapter(json.loads(json.dumps(state(), sort_keys=True)))
    expected = np.array([[1, 1, 0, 0, 1], [0, 0, 0, 0, 0], [0, 0, 1, 0, 0]], dtype="float32")
    assert first.output_feature_names == ["z", "a", "kind=__missing__", "kind=b", "kind=a"]
    np.testing.assert_array_equal(first.transform(frame), expected)
    np.testing.assert_array_equal(second.transform(frame), expected)
    np.testing.assert_array_equal(TensorAdapter.from_dict(first.to_dict()).transform(frame), expected)
    assert first.transform(frame).flags.c_contiguous
    np.testing.assert_array_equal(first.inverse_target(first.target([80, 120])), [80, 120])


@pytest.mark.parametrize("mutation", ["width", "scope", "std", "duplicate", "unknown_rule", "feature_names"])
def test_invalid_state_fails(mutation):
    value = state()
    if mutation == "width":
        value["output_width"] = 6
    if mutation == "scope":
        value["fit_scope"] = "test"
    if mutation == "std":
        value["numeric"]["z"]["std"] = 0
    if mutation == "duplicate":
        value["input_columns"].append("z")
    if mutation == "unknown_rule":
        value["numeric"]["rogue"] = value["numeric"]["z"]
    if mutation == "feature_names":
        value["categorical"]["kind"] = ["b", "b", "a"]
    with pytest.raises(ValueError):
        TensorAdapter(value)


def test_schema_target_and_serialized_order_guard():
    adapter = TensorAdapter(state())
    with pytest.raises(ValueError):
        adapter.transform(pd.DataFrame({"z": [1]}))
    with pytest.raises(ValueError):
        adapter.target([np.nan])
    document = adapter.to_dict()
    document["output_feature_names"] = list(reversed(document["output_feature_names"]))
    with pytest.raises(ValueError):
        TensorAdapter.from_dict(document)
    np.testing.assert_array_equal(
        TensorAdapter({**state(), "target_transform": {"name": "identity"}}).target([1]), [1]
    )


def test_label_order_numeric_ids_not_alphabetic():
    adapter = TensorAdapter({**state(), "class_names": {"1": "yes", "0": "no"}})
    assert adapter.class_names == ["no", "yes"]
    np.testing.assert_array_equal(adapter.encode_labels(["yes", "no"]), [1, 0])
    with pytest.raises(ValueError):
        adapter.encode_labels(["unknown"])


def test_image_layout_same_values():
    images = np.arange(2 * 4 * 4 * 3, dtype="uint8").reshape(2, 4, 4, 3)
    hwc = image_batch(images, "keras")
    chw = image_batch(images, "pytorch")
    np.testing.assert_array_equal(chw.transpose(0, 2, 3, 1), hwc)
    np.testing.assert_array_equal(image_batch(images, "scratch"), hwc)
    for bad in [np.zeros((2, 4, 4)), images.astype(float), np.ones((2, 4, 4, 1), dtype="uint8")]:
        with pytest.raises(ValueError):
            image_batch(bad, "keras")
    with pytest.raises(ValueError):
        image_batch(images, "unknown")


def test_ids_and_causal_window_alignment():
    frame = pd.DataFrame(
        {
            "z": [2, 4, 6, 8],
            "a": [10] * 4,
            "kind": ["b"] * 4,
            "target": [80, 100, 120, 140],
            "series": ["s"] * 4,
        }
    )
    window = {"id": "s/1", "start_index": 0, "origin_index": 1, "target_indices": [2, 3], "series": "s"}
    x, y = window_batch(frame, [window], TensorAdapter(state()))
    assert x.shape == (1, 2, 5)
    np.testing.assert_array_equal(y, [[1, 2]])
    assert select_rows(["a", "b"], ["b", "a"]) == [1, 0]
    for source, wanted in [(["a", "a"], ["a"]), (["a"], ["b"]), (["a"], ["a", "a"])]:
        with pytest.raises(ValueError):
            select_rows(source, wanted)
    invalid = copy.deepcopy(window)
    invalid["target_indices"] = [0, 2]
    with pytest.raises(ValueError):
        window_batch(frame, [invalid], TensorAdapter(state()))
