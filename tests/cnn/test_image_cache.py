"""Phase27 RED: uint8/cache safety and exact frozen preprocessing."""

import hashlib
import io
import tarfile
import zipfile
from typing import ClassVar

import numpy as np
import pytest
from PIL import Image

from src.ch03_cnn.image_cache import ImageCache, decode_rows, storage_budget


def test_cifar_single_stream_pixels_and_order(tmp_path):
    pixels = np.arange(2 * 32 * 32 * 3, dtype=np.uint8).reshape(2, 32, 32, 3)
    payload = b"".join(bytes([i]) + p.transpose(2, 0, 1).tobytes() for i, p in enumerate(pixels))
    path = tmp_path / "images.tar.gz"
    member = "cifar-10-batches-bin/data_batch_1.bin"
    with tarfile.open(path, "w:gz") as archive:
        info = tarfile.TarInfo(member)
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    rows = [{"id": str(i), "member": member, "record_offset": i, "target": str(i)} for i in (1, 0)]
    actual = list(decode_rows("ch3_cifar10", path, rows, [32, 32]))
    assert {key: value.tobytes() for key, value in actual} == {str(i): pixels[i].tobytes() for i in (1, 0)}


def test_zip_rgb_bilinear_and_unsafe_member(tmp_path):
    path = tmp_path / "images.zip"
    image = Image.fromarray(np.arange(18 * 18 * 3, dtype=np.uint8).reshape(18, 18, 3))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("class/a.png", buffer.getvalue())
    rows = [{"id": "a", "member": "class/a.png"}]
    actual = next(decode_rows("ch3_eurosat", path, rows, [8, 8]))[1]
    np.testing.assert_array_equal(actual, np.asarray(image.resize((8, 8), Image.Resampling.BILINEAR)))
    with pytest.raises(ValueError, match="member"):
        list(decode_rows("ch3_eurosat", path, [{"id": "a", "member": "../a.png"}], [8, 8]))


def test_cache_roundtrip_and_tampering(tmp_path):
    pixels = np.ones((3, 8, 8, 3), dtype=np.uint8)
    ids = ["a", "b", "c"]
    cache = ImageCache.create(
        tmp_path / "cache", ids, pixels, [0, 1, 0], {"fixture": "tiny"}, free_bytes=10**10
    )
    x, y = cache.batch(["c", "a"], "scratch")
    assert x.dtype == np.float32 and y.tolist() == [0, 0]
    np.testing.assert_allclose(x, 1 / 255)
    torch_x, _ = cache.batch(["a"], "pytorch")
    assert torch_x.shape == (1, 3, 8, 8)
    for bad in (["z"], ["a", "a"], []):
        with pytest.raises(ValueError):
            cache.batch(bad, "scratch")
    with pytest.raises(ValueError):
        cache.batch(["a"], "unknown")
    path = tmp_path / "cache" / "pixels.npy"
    payload = bytearray(path.read_bytes())
    payload[-1] ^= 1
    path.write_bytes(payload)
    with pytest.raises(ValueError, match="hash"):
        ImageCache(tmp_path / "cache")


@pytest.mark.parametrize(
    "pixels,ids,labels",
    [
        (np.zeros((1, 8, 8, 3), dtype=np.float32), ["a"], [0]),
        (np.zeros((2, 8, 8, 3), dtype=np.uint8), ["a", "a"], [0, 1]),
        (np.zeros((1, 8, 8, 3), dtype=np.uint8), ["a"], [-1]),
    ],
)
def test_cache_rejects_bad_input(tmp_path, pixels, ids, labels):
    with pytest.raises(ValueError):
        ImageCache.create(tmp_path / "bad", ids, pixels, labels, {}, free_bytes=10**10)


def test_budget_reserve_and_cap():
    assert storage_budget(10, [32, 32, 3], free_bytes=10**10)["pixel_bytes"] == 30720
    with pytest.raises(OSError):
        storage_budget(10, [32, 32, 3], free_bytes=5 * 1024**3)
    with pytest.raises(ValueError):
        storage_budget(10**7, [128, 128, 3], free_bytes=10**15)


def test_real_development_cache_and_reference_parity(tmp_path):
    from src.common.contracts import ROOT
    from src.common.data_access import DatasetView
    from src.common.eda_sources import image_for_row, source

    for dataset in ("ch3_idrid", "ch3_eurosat", "ch3_cifar10"):
        view = DatasetView(dataset)
        view._load()
        ids = view.ids("train")[:1] + view.ids("validation")[:1]
        rows = [view._index[key] for key in ids]
        path = ROOT / source(dataset)["contract"]["files"][0]["path"]
        decoded = dict(decode_rows(dataset, path, rows, view.preprocessing["input_shape_hwc"][:2]))
        for row in rows:
            pixels = decoded[row["id"]]
            assert hashlib.sha256(pixels.tobytes()).hexdigest() == row["model_pixel_sha256"]
            expected = np.asarray(image_for_row(dataset, row, view.preprocessing["input_shape_hwc"][:2]))
            np.testing.assert_array_equal(pixels, expected)
        with pytest.raises(ValueError, match="sealed"):
            view.ids("test")


def test_development_builder_uses_frozen_ids_hashes_and_provenance(tmp_path, monkeypatch):
    from src.ch03_cnn import image_cache as module

    images = {
        "fixture_train": np.zeros((8, 8, 3), dtype="uint8"),
        "fixture_validation": np.ones((8, 8, 3), dtype="uint8"),
    }

    class FixtureView:
        kind = "image"
        preprocessing: ClassVar[dict] = {"input_shape_hwc": [8, 8, 3]}
        adapter_contract: ClassVar[dict] = {"source_label_to_id": {"0": 0, "1": 1}}
        provenance: ClassVar[dict] = {"fixture": "synthetic_no_actual_test_data"}
        _index: ClassVar[dict] = {
            key: {
                "id": key,
                "target": str(i),
                "model_pixel_sha256": hashlib.sha256(value.tobytes()).hexdigest(),
            }
            for i, (key, value) in enumerate(images.items())
        }

        def ids(self, partition):
            return ["fixture_train"] if partition == "train" else ["fixture_validation"]

        def _load(self):
            pass

    view = FixtureView()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "DatasetView", lambda _: view)
    monkeypatch.setattr(
        module, "source", lambda _: {"contract": {"files": [{"path": "synthetic-unused-archive"}]}}
    )
    monkeypatch.setattr(
        module,
        "decode_rows",
        lambda dataset, path, rows, resolution: ((row["id"], images[row["id"]]) for row in rows),
    )
    root = tmp_path / "development"
    cache, _ = module.development_cache("ch3_cifar10", root)
    assert cache.ids == ["fixture_train", "fixture_validation"]
    assert cache.labels.tolist() == [0, 1]
    reused, _ = module.development_cache("ch3_cifar10", root)
    np.testing.assert_array_equal(reused.pixels, cache.pixels)
    view.provenance = {"fixture": "changed"}
    with pytest.raises(ValueError, match="provenance"):
        module.development_cache("ch3_cifar10", root)
    view._index["fixture_train"]["model_pixel_sha256"] = "a" * 64
    with pytest.raises(ValueError, match="pixel hash"):
        module.development_cache("ch3_cifar10", tmp_path / "bad_pixel")
    view.kind = "tabular"
    with pytest.raises(ValueError, match="Image dataset"):
        module.development_cache("ch3_cifar10", tmp_path / "not_image")
