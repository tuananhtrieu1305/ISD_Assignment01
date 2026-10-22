"""Deterministic batches, optimizer semantics, undefined metrics, safe checkpoints."""

import numpy as np
import pytest

from src.common.artifact_core import ArtifactStore
from src.common.metric_core import classification_metrics, regression_metrics
from src.common.training_core import Adam, EarlyStopping, batch_order, clip_gradients, seed_everything


def test_seed_batches_clip_adam_early_stop():
    seed_everything(42)
    first = np.random.rand(4)
    seed_everything(42)
    np.testing.assert_array_equal(first, np.random.rand(4))
    assert batch_order(7, 3, 42, 0) == batch_order(7, 3, 42, 0)
    assert sorted(value for batch in batch_order(7, 3, 42, 0) for value in batch) == list(range(7))
    clipped, norm = clip_gradients({"a": np.array([3.0, 4.0])}, 1)
    assert norm == 5
    np.testing.assert_allclose(clipped["a"], [0.6, 0.8])
    weights = {"a": np.array([1.0, 2.0])}
    optimizer = Adam(weights)
    optimizer.step(weights, {"a": np.array([0.2, -0.3])})
    np.testing.assert_allclose(weights["a"], [1 - 0.001 * 0.2 / (0.2 + 1e-7), 2 + 0.001 * 0.3 / (0.3 + 1e-7)])
    stop = EarlyStopping(patience=2, min_delta=1e-5)
    assert stop.observe(2, 0) == (True, False)
    assert stop.observe(3, 1) == (False, False)
    assert stop.observe(4, 2) == (False, True)
    assert stop.best_epoch == 0
    with pytest.raises(ValueError):
        stop.observe(np.nan, 3)
    with pytest.raises(ValueError):
        clip_gradients({"a": np.array([np.inf])}, 1)


def test_metrics_and_undefined_support():
    result = classification_metrics([0, 1, 1], np.array([[0.9, 0.1], [0.2, 0.8], [0.1, 0.9]]))
    assert result["accuracy"]["value"] == 1
    assert result["auroc"]["value"] == 1
    missing = classification_metrics([0, 0], np.array([[0.9, 0.1], [0.8, 0.2]]))
    assert missing["auroc"]["value"] is None and missing["auroc"]["undefined_reason"]
    regression = regression_metrics([[0, 2], [0, 4]], [[0, 1], [0, 3]], horizons=[1, 3])
    assert regression["by_horizon"]["1"]["smape"]["value"] == 0
    assert regression["by_horizon"]["3"]["mae"]["value"] == 1
    with pytest.raises(ValueError):
        regression_metrics([1], [np.nan])


def test_npz_roundtrip_tamper_no_pickle_and_provenance(tmp_path):
    store = ArtifactStore(tmp_path)
    provenance = {key: "a" * 64 for key in store.PROVENANCE_KEYS}
    arrays = {"dense_1/w": np.arange(6, dtype="float32").reshape(2, 3)}
    metadata = store.save_checkpoint("model", arrays, provenance)
    result = store.load_checkpoint("model", provenance)
    np.testing.assert_array_equal(result["dense_1/w"], arrays["dense_1/w"])
    assert metadata["cpu_loadable"]
    with pytest.raises(ValueError):
        store.save_checkpoint("missing", arrays, {})
    with pytest.raises(ValueError):
        store.save_checkpoint("../outside", arrays, provenance)
    with pytest.raises(ValueError):
        store.save_checkpoint("objects", {"x": np.array([object()])}, provenance)
    with pytest.raises(ValueError):
        store.save_checkpoint("model", arrays, provenance)
    with pytest.raises(ValueError):
        store.load_checkpoint("model", {**provenance, "config_sha256": "b" * 64})
    (tmp_path / "model.npz").write_bytes(b"tampered")
    with pytest.raises(ValueError):
        store.load_checkpoint("model", provenance)
