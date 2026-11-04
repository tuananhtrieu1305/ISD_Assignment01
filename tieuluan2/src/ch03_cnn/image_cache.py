"""Budgeted, data-only uint8 image cache; no archive extraction or pickle.

Development builder accepts only DatasetView train/validation IDs. Evaluation
must obtain its own sealed authorization before constructing a separate cache.
Every decoded pixel hash is checked against the frozen Phase24 index.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

import numpy as np
from PIL import Image

from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json
from src.common.data_access import DatasetView
from src.common.eda_sources import source
from src.common.tensor_adapters import image_batch

RESERVE_BYTES = 5 * 1024**3
MAX_CACHE_BYTES = 256 * 1024**2


def storage_budget(count, shape, *, free_bytes, max_bytes=MAX_CACHE_BYTES):
    if count < 1 or len(shape) != 3 or shape[-1] != 3 or min(shape) < 1:
        raise ValueError("Invalid image dimensions/count")
    pixels = int(count) * int(np.prod(shape))
    # Header, ID strings, labels, and atomic receipt margin; no float32 disk cache.
    required = pixels + count * 1024 + 1024**2
    if required > max_bytes:
        raise ValueError("Image cache exceeds declared byte budget")
    if free_bytes - required < RESERVE_BYTES:
        raise OSError("Image cache would cross host disk reserve 5 GiB")
    return {
        "pixel_bytes": pixels,
        "reserved_write_bytes": required,
        "reserve_bytes": RESERVE_BYTES,
        "cap_bytes": max_bytes,
    }


def _member(name):
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
        raise ValueError("Unsafe archive member")
    return name


def decode_rows(dataset, path, rows, resolution):
    """One archive pass, bounded member buffer; yields (ID, uint8 HWC)."""
    if dataset not in {"ch3_idrid", "ch3_eurosat", "ch3_cifar10"}:
        raise ValueError("Unknown image dataset")
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate image IDs")
    members = {}
    for row in rows:
        members.setdefault(_member(row["member"]), []).append(row)
    found = set()
    if dataset == "ch3_cifar10":
        with tarfile.open(path, "r|gz") as archive:
            for member in archive:
                if member.name not in members:
                    continue
                if (
                    not member.isfile()
                    or not re.fullmatch(
                        r"cifar-10-batches-bin/(data_batch_[1-5]|test_batch)\.bin", member.name
                    )
                    or member.size > 3073 * 10000
                ):
                    raise ValueError("Invalid CIFAR member/type/size")
                with archive.extractfile(member) as stream:
                    payload = stream.read(3073 * 10000 + 1)
                if not payload or len(payload) % 3073:
                    raise ValueError("Invalid CIFAR record bytes")
                records = np.frombuffer(payload, np.uint8).reshape(-1, 3073)
                for row in members[member.name]:
                    index = int(row["record_offset"])
                    if index < 0 or index >= len(records) or str(records[index, 0]) != str(row["target"]):
                        raise ValueError("CIFAR record offset/label mismatch")
                    image = Image.fromarray(records[index, 1:].reshape(3, 32, 32).transpose(1, 2, 0))
                    yield (
                        row["id"],
                        np.asarray(image.resize(tuple(resolution), Image.Resampling.BILINEAR)).copy(),
                    )
                    found.add(row["id"])
    else:
        with zipfile.ZipFile(path) as archive:
            for member, selected in members.items():
                info = archive.getinfo(member)
                if info.file_size > 64 * 1024**2 or info.is_dir():
                    raise ValueError("Image member exceeds byte budget")
                with archive.open(info) as stream, Image.open(stream) as image:
                    if image.mode != "RGB":
                        raise ValueError("Frozen pipeline requires RGB")
                    pixels = np.asarray(image.resize(tuple(resolution), Image.Resampling.BILINEAR)).copy()
                for row in selected:
                    yield row["id"], pixels
                    found.add(row["id"])
    if len(found) != len(rows):
        raise ValueError("Missing image archive members")


class ImageCache:
    def __init__(self, root):
        self.root = Path(root)
        self.receipt = read_json(self.root / "manifest.json")
        for name, digest in self.receipt["files"].items():
            if name not in {"pixels.npy", "labels.npy", "ids.npy"} or sha256_file(self.root / name) != digest:
                raise ValueError("Image cache hash mismatch")
        if set(self.receipt["files"]) != {"pixels.npy", "labels.npy", "ids.npy"}:
            raise ValueError("Incomplete image cache")
        self.pixels = np.load(self.root / "pixels.npy", mmap_mode="r", allow_pickle=False)
        self.labels = np.load(self.root / "labels.npy", mmap_mode="r", allow_pickle=False)
        self.ids = np.load(self.root / "ids.npy", allow_pickle=False).tolist()
        self._validate(self.ids, self.pixels, self.labels)
        self.positions = {key: i for i, key in enumerate(self.ids)}

    @staticmethod
    def _validate(ids, pixels, labels):
        labels = np.asarray(labels)
        if (
            pixels.dtype != np.uint8
            or pixels.ndim != 4
            or pixels.shape[-1] != 3
            or len(pixels) != len(ids)
            or not ids
            or len(set(ids)) != len(ids)
            or not all(isinstance(k, str) and k for k in ids)
            or labels.shape != (len(ids),)
            or labels.dtype.kind not in "iu"
            or np.any(labels < 0)
        ):
            raise ValueError("Invalid uint8 cache input/IDs/labels")

    @classmethod
    def create(cls, root, ids, pixels, labels, provenance, *, free_bytes):
        root = Path(root)
        cls._validate(ids, pixels, labels)
        budget = storage_budget(len(ids), pixels.shape[1:], free_bytes=free_bytes)
        root.mkdir(parents=True, exist_ok=False)
        for name, value in (
            ("pixels", pixels),
            ("ids", np.asarray(ids)),
            ("labels", np.asarray(labels, dtype="int64")),
        ):
            with (root / f"{name}.npy").open("xb") as stream:
                np.save(stream, value, allow_pickle=False)
        write_once(
            root / "manifest.json",
            {
                "version": "phase27.uint8.1",
                "provenance": provenance,
                "shape": list(pixels.shape),
                "budget": budget,
                "files": {
                    f"{name}.npy": sha256_file(root / f"{name}.npy") for name in ("pixels", "ids", "labels")
                },
            },
        )
        return cls(root)

    def batch(self, ids, implementation="scratch"):
        if not ids or len(set(ids)) != len(ids) or any(k not in self.positions for k in ids):
            raise ValueError("Unknown/duplicate/sealed image IDs")
        pos = [self.positions[key] for key in ids]
        return image_batch(self.pixels[pos], implementation), np.asarray(self.labels[pos])


def development_cache(dataset, cache_root=None):
    view = DatasetView(dataset)
    if view.kind != "image":
        raise ValueError("Image dataset required")
    root = Path(cache_root) if cache_root else ROOT / f"data/processed/v3/phase27/{dataset}_development"
    ids = view.ids("train") + view.ids("validation")
    if root.exists():
        cached = ImageCache(root)
        if cached.ids != ids or cached.receipt["provenance"] != view.provenance:
            raise ValueError("Cache provenance/partition mismatch")
        return cached, view
    shape = view.preprocessing["input_shape_hwc"]
    storage_budget(len(ids), shape, free_bytes=shutil.disk_usage(ROOT).free)
    view._load()
    rows = [view._index[key] for key in ids]
    # Largest development block ~31 MiB, uint8 only. Streaming decoder <=31 MiB member.
    pixels = np.empty((len(ids), *shape), dtype="uint8")
    positions = {key: i for i, key in enumerate(ids)}
    row_map = {row["id"]: row for row in rows}
    path = ROOT / source(dataset)["contract"]["files"][0]["path"]
    for key, image in decode_rows(dataset, path, rows, shape[:2]):
        if hashlib.sha256(image.tobytes()).hexdigest() != row_map[key]["model_pixel_sha256"]:
            raise ValueError("Frozen model pixel hash mismatch")
        pixels[positions[key]] = image
    labels = np.asarray(
        [view.adapter_contract["source_label_to_id"][str(row["target"])] for row in rows], dtype="int64"
    )
    return ImageCache.create(
        root, ids, pixels, labels, view.provenance, free_bytes=shutil.disk_usage(ROOT).free
    ), view
