import hashlib
import io
import zipfile
from typing import ClassVar

import numpy as np
import pytest
from PIL import Image

from src.ch03_cnn.image_cache import ImageCache
from src.ch03_cnn.training import CnnScratchTrainer, fit_images
from src.ch03_cnn.workflow import CnnEvaluationGate, test_partition_cache
from src.common.model_core import build_plan, canonical_weights


def test_gate_consumes_claim_and_never_reopens(tmp_path):
    gate = CnnEvaluationGate(tmp_path / "seal")
    manifest = {
        "dataset_id": "ch3_cifar10",
        "split_sha256": "a" * 64,
        "code_sha256": "b" * 64,
        "runs": ["cnn_fixture"],
    }
    gate.lock(manifest)
    assert gate.state()["seal_id"] == "ch3_cifar10_phase27_test_v1"
    with pytest.raises(ValueError):
        gate.begin("c" * 64)
    gate.begin("b" * 64)
    gate.claim("cnn_fixture", "b" * 64)
    with pytest.raises(ValueError):
        gate.claim("cnn_fixture", "b" * 64)
    gate.record("cnn_fixture", {"status": "PASS"})
    gate.complete()
    assert gate.state()["evaluation_count"] == 1
    with pytest.raises(ValueError):
        gate.begin("b" * 64)
    with pytest.raises(ValueError):
        test_partition_cache("ch3_cifar10", gate, "cnn_fixture")


def test_failed_gate_and_unclaimed_records_stay_blocked(tmp_path):
    gate = CnnEvaluationGate(tmp_path / "seal")
    manifest = {
        "dataset_id": "ch3_cifar10",
        "split_sha256": "a" * 64,
        "code_sha256": "b" * 64,
        "runs": ["cnn_fixture"],
    }
    gate.lock(manifest)
    with pytest.raises(ValueError):
        gate.lock(manifest)
    gate.begin("b" * 64)
    with pytest.raises(ValueError, match="unclaimed"):
        gate.record("cnn_fixture", {"status": "PASS"})
    with pytest.raises(ValueError):
        test_partition_cache("ch3_cifar10", gate, "cnn_fixture")
    gate.claim("cnn_fixture", "b" * 64)
    gate.fail("synthetic failure fixture; no model or real TEST data")
    assert gate.state()["state"] == "failed_sealed"
    assert gate.state()["evaluation_count"] == 1
    with pytest.raises(ValueError):
        gate.begin("b" * 64)
    with pytest.raises(ValueError):
        gate.claim("cnn_fixture", "b" * 64)


def test_sealed_image_cache_builder_on_synthetic_zip_only(tmp_path, monkeypatch):
    from src.ch03_cnn import workflow as module

    pixels = np.zeros((8, 8, 3), dtype="uint8")
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")
    with zipfile.ZipFile(tmp_path / "synthetic.zip", "w") as archive:
        archive.writestr("fixture/image.png", buffer.getvalue())

    class FixtureView:
        split_dir = tmp_path / "synthetic_splits"
        provenance: ClassVar[dict] = {"split_sha256": "a" * 64, "fixture": "no_actual_public_test"}
        preprocessing: ClassVar[dict] = {"input_shape_hwc": [8, 8, 3]}
        adapter_contract: ClassVar[dict] = {"source_label_to_id": {"0": 0}}
        _index: ClassVar[dict] = {
            "fixture_holdout": {
                "id": "fixture_holdout",
                "member": "fixture/image.png",
                "target": "0",
                "model_pixel_sha256": hashlib.sha256(pixels.tobytes()).hexdigest(),
            }
        }

        def _load(self):
            pass

    view = FixtureView()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "DatasetView", lambda _: view)
    monkeypatch.setattr(module, "read_rows", lambda _: ["fixture_holdout"])
    monkeypatch.setattr(module, "source", lambda _: {"contract": {"files": [{"path": "synthetic.zip"}]}})
    gate = CnnEvaluationGate(tmp_path / "synthetic_seal")
    gate.lock(
        {
            "dataset_id": "ch3_eurosat",
            "split_sha256": "a" * 64,
            "code_sha256": "b" * 64,
            "runs": ["cnn_fixture"],
        }
    )
    gate.begin("b" * 64)
    with pytest.raises(ValueError):
        module.test_partition_cache("ch3_eurosat", gate, "cnn_fixture")
    gate.claim("cnn_fixture", "b" * 64)
    cache, _, ids = module.test_partition_cache("ch3_eurosat", gate, "cnn_fixture")
    assert ids == ["fixture_holdout"] and cache.labels.tolist() == [0]
    np.testing.assert_array_equal(cache.pixels[0], pixels)
    reused, _, _ = module.test_partition_cache("ch3_eurosat", gate, "cnn_fixture")
    np.testing.assert_array_equal(cache.pixels, reused.pixels)
    view.provenance["fixture"] = "changed"
    with pytest.raises(ValueError, match="provenance"):
        module.test_partition_cache("ch3_eurosat", gate, "cnn_fixture")


def test_fit_resume_and_batch_history(tmp_path):
    plan = build_plan("cnn", [8, 8, 3], 3, tiny=True)
    weights = canonical_weights(plan, 17)
    pixels = np.random.default_rng(8).integers(0, 255, (8, 8, 8, 3), dtype="uint8")
    cache = ImageCache.create(
        tmp_path / "cache",
        [str(i) for i in range(8)],
        pixels,
        [0, 1, 2, 0, 1, 2, 0, 1],
        {},
        free_bytes=10**10,
    )
    settings = {
        "max_epochs": 2,
        "patience": 6,
        "min_delta": 1e-5,
        "batch_size": 2,
        "wall_time_limit_minutes": 2,
    }
    saved = []
    a = CnnScratchTrainer(plan, weights)
    result = fit_images(
        a, cache, [str(i) for i in range(6)], ["6", "7"], seed=17, budget=settings, progress=saved.append
    )
    b = CnnScratchTrainer(plan, weights)
    resumed = fit_images(
        b, cache, [str(i) for i in range(6)], ["6", "7"], seed=17, budget=settings, resume=saved[0]
    )
    assert len(result["history"]) == len(resumed["history"]) == 2
    for key in weights:
        np.testing.assert_array_equal(result["weights"][key], resumed["weights"][key])
    early = saved[-1]
    early["early_stopping"]["bad_epochs"] = 6
    c = CnnScratchTrainer(plan, weights)
    assert (
        fit_images(
            c,
            cache,
            [str(i) for i in range(6)],
            ["6", "7"],
            seed=17,
            budget={**settings, "max_epochs": 40},
            resume=early,
        )["optimizer_steps"]
        == result["optimizer_steps"]
    )
