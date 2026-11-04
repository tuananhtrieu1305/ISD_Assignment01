"""Synthetic compact cache tests: overlapping windows, hashes and NPZ budgets."""

import io
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import numpy as np
import pytest

from src.ch04_rnn_lstm.phase29 import holdout_cache, protocol
from src.common.artifact_core import write_once


@pytest.fixture
def source(tmp_path, monkeypatch):
    monkeypatch.setattr(protocol, "ROOT", tmp_path)
    monkeypatch.setattr(holdout_cache, "ROOT", tmp_path)
    prep = tmp_path / "synthetic_preprocessing.json"
    write_once(prep, {"synthetic": True})

    class Data:
        dataset_id = "ch4_gold_pink_sheet"
        test_ids = ("synthetic_a", "synthetic_b")
        lookback = 3
        horizons = (1, 2)
        features = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0], [4.0, 40.0], [np.nan, np.nan]], "float32")
        rows: ClassVar = {
            "synthetic_a": {
                "series": "S",
                "start_index": 0,
                "origin_index": 2,
                "target_times": ["2000-01-04", "2000-01-05"],
            },
            "synthetic_b": {
                "series": "S",
                "start_index": 1,
                "origin_index": 3,
                "target_times": ["2000-01-05", "2000-01-06"],
            },
        }
        view = SimpleNamespace(contract=lambda: {"preprocessing": protocol.ref(prep)})

        def targets(self, ids):
            return np.asarray([[4.0, 5.0] if k == "synthetic_a" else [5.0, 6.0] for k in ids], "float64")

        def batch(self, ids):
            return np.stack(
                [self.features[self.rows[k]["start_index"] : self.rows[k]["origin_index"] + 1] for k in ids]
            ), self.targets(ids).astype("float32") / 10

        def baseline(self, ids, method):
            return np.asarray([[3.0, 3.0] if k == "synthetic_a" else [4.0, 4.0] for k in ids], "float64")

        def contract(self):
            return {"split": "test", "evidence_kind": "synthetic_fixture"}

    return Data(), tmp_path


def test_compact_cache_all_pixel_free_window_parity_and_float64_targets(source):
    data, root = source
    reference = holdout_cache.write_cache(data, root / "cache", "a" * 64)
    restored = holdout_cache.CachedHoldout(reference, "a" * 64)
    assert restored.ids == list(data.test_ids)
    assert restored.arrays["features"].shape == (4, 2)  # shared context, not NxTxF duplicate
    for ids in ([data.test_ids[0]], list(reversed(data.test_ids))):
        x, y = restored.batch(ids)
        expected = data.batch(ids)
        np.testing.assert_array_equal(x, expected[0])
        np.testing.assert_array_equal(y, expected[1])
        np.testing.assert_array_equal(restored.targets(ids), data.targets(ids))
        assert restored.targets(ids).dtype == np.float64
    assert restored.series(restored.ids) == ["S", "S"]
    np.testing.assert_array_equal(
        restored.baseline(restored.ids, "last_value"), data.baseline(data.test_ids, "last_value")
    )
    for ids in ([], ["unknown"], [data.test_ids[0]] * 2):
        with pytest.raises(ValueError):
            restored.batch(ids)
    with pytest.raises(ValueError):
        restored.baseline(restored.ids, "unknown")


def test_cache_requires_matching_authorization_hash_and_artifact_hash(source):
    data, root = source
    reference = holdout_cache.write_cache(data, root / "cache", "a" * 64)
    with pytest.raises(ValueError):
        holdout_cache.CachedHoldout(reference, "b" * 64)
    with pytest.raises(ValueError):
        holdout_cache.CachedHoldout({**reference, "sha256": "c" * 64}, "a" * 64)
    archive = root / "cache/arrays.npz"
    archive.write_bytes(archive.read_bytes() + b"tampered")
    with pytest.raises(ValueError):
        holdout_cache.CachedHoldout(reference, "a" * 64)


def test_cache_rejects_nan_context_duplicate_ids_and_budget_overflow(source, monkeypatch):
    data, root = source
    data.features[0, 0] = np.nan
    with pytest.raises(ValueError):
        holdout_cache.write_cache(data, root / "bad1", "a" * 64)
    data.features[0, 0] = 1
    data.test_ids = ("synthetic_a", "synthetic_a")
    with pytest.raises(ValueError):
        holdout_cache.write_cache(data, root / "bad2", "a" * 64)
    data.test_ids = ("synthetic_a", "synthetic_b")
    monkeypatch.setattr(holdout_cache, "BUDGET", 1)
    with pytest.raises(ValueError):
        holdout_cache.write_cache(data, root / "bad3", "a" * 64)


def test_cache_hash_is_checked_on_the_exact_loaded_bytes(source, monkeypatch):
    data, root = source
    reference = holdout_cache.write_cache(data, root / "cache", "a" * 64)
    path = root / "cache/arrays.npz"
    with np.load(path, allow_pickle=False) as archive:
        arrays = {k: archive[k] for k in archive.files}
    arrays["features"] = arrays["features"] + 100
    packed = io.BytesIO()
    np.savez_compressed(packed, **arrays)
    original = Path.read_bytes
    monkeypatch.setattr(
        Path, "read_bytes", lambda self: packed.getvalue() if self == path else original(self)
    )
    with pytest.raises(ValueError, match="changed while loading"):
        holdout_cache.CachedHoldout(reference, "a" * 64)
