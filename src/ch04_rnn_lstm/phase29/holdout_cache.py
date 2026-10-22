"""Compact shared TEST context cache, built only after a joint batch claim.

One row-feature table plus window indices; no NxTxF float tensor on disk.
Inputs are finite numeric NPZ, pinned by external metadata hash, never pickle.
"""

import hashlib
import io
import zipfile
from pathlib import Path

import numpy as np

from src.ch04_rnn_lstm.phase29.protocol import checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json

BUDGET = 64 * 1024**2
FIELDS = {
    "features",
    "windows",
    "source_positions",
    "targets",
    "normalized_targets",
    "last_value",
    "seasonal_naive",
}


def write_cache(data, folder, authorization_sha256):
    ids = list(data.test_ids)
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Missing/duplicate TEST cache IDs")
    positions = sorted(
        {i for key in ids for i in range(data.rows[key]["start_index"], data.rows[key]["origin_index"] + 1)}
    )
    mapping = {position: i for i, position in enumerate(positions)}
    windows = np.asarray(
        [
            [mapping[i] for i in range(data.rows[k]["start_index"], data.rows[k]["origin_index"] + 1)]
            for k in ids
        ],
        "int32",
    )
    normalized = np.concatenate([data.batch(ids[i : i + 32])[1] for i in range(0, len(ids), 32)])
    arrays = {
        "features": np.ascontiguousarray(data.features[positions]),
        "windows": windows,
        "source_positions": np.asarray(positions, "int64"),
        "targets": data.targets(ids),
        "normalized_targets": normalized,
        **{method: data.baseline(ids, method) for method in ("last_value", "seasonal_naive")},
    }
    if sum(a.nbytes for a in arrays.values()) > BUDGET or any(
        a.dtype.kind not in "fiu" or not np.isfinite(a).all() for a in arrays.values()
    ):
        raise ValueError("Nonfinite/unsafe/over-budget TEST cache")
    if windows.shape != (len(ids), data.lookback):
        raise ValueError("TEST window length mismatch")
    for offset in range(0, len(ids), 32):
        expected = data.batch(ids[offset : offset + 32])
        if not np.array_equal(arrays["features"][windows[offset : offset + 32]], expected[0]):
            raise ValueError("Compact window pixel-free feature parity failed")
    folder = Path(folder).resolve()
    if not folder.is_relative_to(ROOT.resolve()):
        raise ValueError("Cache output escapes workspace")
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / "arrays.npz"
    with archive.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    metadata = {
        "cache_version": "phase29.row_cache.1",
        "dataset_id": data.dataset_id,
        "authorization_sha256": authorization_sha256,
        "arrays": ref(archive),
        "input_shape": [data.lookback, arrays["features"].shape[1]],
        "horizons": list(data.horizons),
        "preprocessing": data.view.contract()["preprocessing"],
        "source_contract": data.contract(),
        "rows": [
            {"id": k, "series": data.rows[k]["series"], "target_times": data.rows[k]["target_times"]}
            for k in ids
        ],
        "expanded_array_bytes": sum(a.nbytes for a in arrays.values()),
        "full_window_tensor_stored": False,
        "all_windows_exact_feature_parity": True,
    }
    write_once(folder / "metadata.json", metadata)
    return ref(folder / "metadata.json")


class CachedHoldout:
    def __init__(self, metadata_ref, authorization_sha256):
        self.metadata = read_json(checked(metadata_ref))
        meta = self.metadata
        if (
            meta.get("cache_version") != "phase29.row_cache.1"
            or meta["authorization_sha256"] != authorization_sha256
        ):
            raise ValueError("TEST cache schema/authorization mismatch")
        checked(meta["preprocessing"])
        path = checked(meta["arrays"])
        if path.stat().st_size > BUDGET:
            raise ValueError("Compressed TEST cache exceeds budget")
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != meta["arrays"]["sha256"]:
            raise ValueError("Cache changed while loading")
        with zipfile.ZipFile(io.BytesIO(payload)) as packed:
            if len(packed.infolist()) != len(FIELDS) or sum(i.file_size for i in packed.infolist()) > BUDGET:
                raise ValueError("Expanded TEST cache exceeds budget")
        with np.load(io.BytesIO(payload), allow_pickle=False) as archive:
            self.arrays = {k: archive[k] for k in archive.files}
        arrays = self.arrays
        self.ids = [row["id"] for row in meta["rows"]]
        self.rows = {row["id"]: row for row in meta["rows"]}
        self.horizons = meta["horizons"]
        self._positions = {key: i for i, key in enumerate(self.ids)}
        n, width = len(self.ids), len(self.horizons)
        if (
            not n
            or len(set(self.ids)) != n
            or set(arrays) != FIELDS
            or sum(a.nbytes for a in arrays.values()) > BUDGET
            or any(a.dtype.kind not in "fiu" or not np.isfinite(a).all() for a in arrays.values())
            or arrays["features"].ndim != 2
            or arrays["features"].dtype != np.dtype("float32")
            or arrays["windows"].dtype.kind not in "iu"
            or list(arrays["windows"].shape) != [n, meta["input_shape"][0]]
            or arrays["features"].shape[1] != meta["input_shape"][1]
            or np.min(arrays["windows"]) < 0
            or np.max(arrays["windows"]) >= len(arrays["features"])
            or arrays["source_positions"].shape != (len(arrays["features"]),)
            or arrays["targets"].dtype != np.dtype("float64")
            or arrays["normalized_targets"].dtype != np.dtype("float32")
            or any(
                arrays[k].shape != (n, width)
                for k in ("targets", "normalized_targets", "last_value", "seasonal_naive")
            )
        ):
            raise ValueError("Unsafe/mismatched TEST cache tensors")

    def positions(self, ids):
        if not ids or len(set(ids)) != len(ids) or any(k not in self._positions for k in ids):
            raise ValueError("Unknown/duplicate/empty TEST cache IDs")
        return [self._positions[k] for k in ids]

    def batch(self, ids):
        positions = self.positions(ids)
        return np.ascontiguousarray(self.arrays["features"][self.arrays["windows"][positions]]), self.arrays[
            "normalized_targets"
        ][positions]

    def targets(self, ids):
        return self.arrays["targets"][self.positions(ids)]

    def series(self, ids):
        self.positions(ids)
        return [self.rows[k]["series"] for k in ids]

    def baseline(self, ids, method):
        if method not in {"last_value", "seasonal_naive"}:
            raise ValueError("Unknown causal baseline")
        return self.arrays[method][self.positions(ids)]
