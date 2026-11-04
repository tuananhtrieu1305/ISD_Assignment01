import copy
import json

import numpy as np
import pytest

from src.common.artifact_core import ArtifactStore, code_fingerprint, sha256_file, write_once
from src.common.data_access import DatasetView
from src.common.device_core import DeviceMonitor
from src.common.metric_core import classification_metrics, regression_metrics
from src.common.model_core import ModelRegistry, build_plan, canonical_weights, make_contract, validate_model
from src.common.numpy_engine import NumpyNetwork, loss_and_gradient, numerical_gradient
from src.common.training_core import Adam, EarlyStopping, batch_order, clip_gradients, seed_everything


def test_invalid_architecture_and_measured_provenance():
    for family, shape in [("cnn", [2, 2, 3]), ("rnn", [4]), ("mlp", [0])]:
        with pytest.raises(ValueError):
            build_plan(family, shape, 1)
    plan = build_plan("mlp", [2], 1)
    with pytest.raises(ValueError):
        make_contract(plan, "unknown", "synthetic_fixture")
    with pytest.raises(ValueError):
        make_contract(plan, "scratch", "measured")
    with pytest.raises(ValueError):
        make_contract(build_plan("mlp", [2], 1, tiny=True), "scratch", "measured", {})
    original = make_contract(plan, "scratch", "synthetic_fixture")
    invalid = copy.deepcopy(original)
    invalid["layers"][-1]["output_shape"] = ["batch", 2]
    invalid["functions"][-1]["output_shape"] = ["batch", 2]
    with pytest.raises(ValueError):
        validate_model(invalid)
    invalid = copy.deepcopy(original)
    invalid["layers"][0]["parameter_count"] += 1
    invalid["functions"][0]["parameters"] += 1
    invalid["parameter_count"] += 1
    with pytest.raises(ValueError):
        validate_model(invalid)
    registry = ModelRegistry()
    registry.register(original)
    returned = registry.get(original["model_id"])
    returned["parameter_count"] = 0
    assert registry.get(original["model_id"])["parameter_count"] > 0


@pytest.mark.parametrize("task", ["mse", "binary", "multiclass"])
def test_weighted_loss_gradient(task):
    logits = (
        np.array([[0.3, 0.8], [0.2, -0.4]], dtype="float64")
        if task == "multiclass"
        else np.array([[0.3], [0.2]], dtype="float64")
    )
    labels = np.array([0, 1]) if task == "multiclass" else np.array([[0.0], [1.0]])
    _, gradient = loss_and_gradient(logits, labels, task, sample_weight=[1.0, 3.0])
    np.testing.assert_allclose(
        gradient,
        numerical_gradient(lambda: loss_and_gradient(logits, labels, task, [1.0, 3.0])[0], logits),
        atol=1e-8,
    )
    for weights in [[0, 0], [-1, 2], [np.nan, 1], [1]]:
        with pytest.raises(ValueError):
            loss_and_gradient(logits, labels, task, weights)


def test_numpy_guards_and_input_derivative():
    for logits, target, task in [
        (np.zeros(2), np.ones(2), "mse"),
        (np.array([[np.nan]]), [[0]], "mse"),
        (np.zeros((1, 1)), [[2]], "binary"),
        (np.zeros((1, 1)), [[0]], "unknown"),
        (np.zeros((1, 2)), [3], "multiclass"),
        (np.zeros((1, 1)), [1], "mse"),
    ]:
        with pytest.raises(ValueError):
            loss_and_gradient(logits, target, task)
    with pytest.raises(ValueError):
        numerical_gradient(lambda: 0.0, np.zeros(1, dtype="float32"))
    plan = build_plan("rnn", [3, 2], 1, tiny=True)
    weights = canonical_weights(plan, 17, dtype="float64")
    for name in weights:
        if name.startswith("dense_") and name.endswith("/b"):
            weights[name] += 0.1234
    model = NumpyNetwork(plan, weights)
    x = np.random.default_rng(42).normal(size=(2, 3, 2))
    y = np.zeros((2, 1))
    _, _, dx = model.loss_gradients(x, y, "mse")
    np.testing.assert_allclose(
        dx, numerical_gradient(lambda: model.loss_gradients(x, y, "mse")[0], x), rtol=1e-3, atol=1e-7
    )
    with pytest.raises(ValueError):
        NumpyNetwork(plan, {})
    with pytest.raises(ValueError):
        model.forward(np.zeros((2, 3, 3)))


def test_training_guards_and_zero_gradient():
    for action in [
        lambda: seed_everything(-1),
        lambda: seed_everything(42, "other"),
        lambda: batch_order(0, 2, 42, 0),
        lambda: clip_gradients({}, 1),
        lambda: clip_gradients({"a": np.zeros(1)}, 0),
        lambda: Adam({}, epsilon=0),
        lambda: EarlyStopping(patience=0),
        lambda: Adam({"a": np.ones(1)}).step({"a": np.ones(1)}, {"b": np.ones(1)}),
    ]:
        with pytest.raises(ValueError):
            action()
    values, norm = clip_gradients({"a": np.zeros(2)})
    assert norm == 0 and values["a"].sum() == 0
    with pytest.raises(ValueError):
        DeviceMonitor("numpy", "cpu").finish()


def test_multiclass_metrics_and_series_aggregation():
    result = classification_metrics([0, 1, 2], np.eye(3))
    assert result["auroc"]["value"] == 1 and result["average_precision"]["value"] == 1
    for labels, prob in [
        ([0], [[1.2, -0.2]]),
        ([0], [[0.2, 0.2]]),
        ([2], [[0.2, 0.8]]),
        ([], np.zeros((0, 2))),
    ]:
        with pytest.raises(ValueError):
            classification_metrics(labels, prob)
    result = regression_metrics(
        [[1, 2], [2, 4], [4, 8]], [[1, 2], [3, 5], [4, 8]], horizons=[1, 3], series=["a", "a", "b"]
    )
    assert "macro_series_rmse" in result and len(result["by_series"]) == 2
    assert regression_metrics([1], [1])["r2"]["value"] is None
    with pytest.raises(ValueError):
        regression_metrics([[1, 2]], [[1, 2]], horizons=[1])
    with pytest.raises(ValueError):
        regression_metrics([1], [1], series=["a", "b"])


def test_checkpoint_manifest_pin_and_json_immutability(tmp_path):
    document = {"name": "có dấu"}
    path = tmp_path / "value.json"
    write_once(path, document)
    write_once(path, document)
    with pytest.raises(ValueError):
        write_once(path, {"name": "changed"})
    assert code_fingerprint(tmp_path, ["value.json"])
    store = ArtifactStore(tmp_path)
    provenance = {key: "a" * 64 for key in store.PROVENANCE_KEYS}
    metadata = store.save_checkpoint("safe", {"w": np.ones(2)}, provenance)
    digest = sha256_file(tmp_path / "safe.json")
    store.load_checkpoint("safe", provenance, expected_manifest_sha256=digest)
    with pytest.raises(ValueError):
        store.load_checkpoint("safe", provenance, expected_manifest_sha256="b" * 64)
    tiny = ArtifactStore(tmp_path / "tiny", max_bytes=1)
    with pytest.raises(ValueError):
        tiny.save_checkpoint("large", {"w": np.ones(2)}, provenance)
    metadata["arrays"]["w"]["shape"] = [3]
    (tmp_path / "safe.json").write_text(json.dumps(metadata))
    with pytest.raises(ValueError):
        store.load_checkpoint("safe", provenance)


def test_all_rolling_folds_use_frozen_own_statistics():
    for dataset in ["ch4_gold_pink_sheet", "ch4_bis_house_prices", "ch4_household_power"]:
        for fold in (1, 2, 3):
            view = DatasetView(dataset, fold=fold)
            assert view.contract()["fold"] == fold
            x, y = view.batch(view.ids("validation")[:1], "keras")
            assert x.shape[1] == view.spec["lookback"] and y.shape == (1, 3)
    for dataset, fold in [("ch2_ames_housing", 1), ("ch4_gold_pink_sheet", 4)]:
        with pytest.raises(ValueError):
            DatasetView(dataset, fold)
