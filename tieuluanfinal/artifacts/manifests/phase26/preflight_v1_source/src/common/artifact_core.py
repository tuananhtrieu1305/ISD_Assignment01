"""Data-only, hash-verified checkpoints and complete provenance (no pickle)."""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

import numpy as np

from src.common.contracts import canonical_sha256


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_once(path, document):
    path = Path(path)
    encoded = (
        json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(encoded)
    except FileExistsError:
        if path.read_bytes() != encoded:
            raise ValueError(f"Immutable artifact differs: {path.name}") from None
    return {"path": path, "sha256": hashlib.sha256(encoded).hexdigest()}


class ArtifactStore:
    PROVENANCE_KEYS = (
        "dataset_sha256",
        "split_sha256",
        "subset_sha256",
        "preprocessing_sha256",
        "adapter_sha256",
        "config_sha256",
        "code_sha256",
        "environment_sha256",
        "model_contract_sha256",
    )

    def __init__(self, root, max_bytes=128 * 1024**2):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes

    def _path(self, name, suffix):
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,95}", name):
            raise ValueError("Invalid checkpoint ID")
        path = (self.root / (name + suffix)).resolve()
        if path.parent != self.root:
            raise ValueError("Checkpoint path escapes root")
        return path

    def _provenance(self, provenance):
        if set(provenance) != set(self.PROVENANCE_KEYS) or any(
            not isinstance(v, str) or not re.fullmatch(r"[a-f0-9]{64}", v) for v in provenance.values()
        ):
            raise ValueError("Missing/invalid artifact provenance")

    def save_checkpoint(self, name, arrays, provenance):
        self._provenance(provenance)
        path = self._path(name, ".npz")
        metadata_path = self._path(name, ".json")
        if path.exists() or metadata_path.exists():
            raise ValueError("Checkpoint already exists")
        if not arrays or any(
            not re.fullmatch(r"[a-z][a-z0-9_/-]{0,127}", k)
            or v.dtype.kind not in "fiu"
            or not np.isfinite(v).all()
            for k, v in arrays.items()
        ):
            raise ValueError("Only finite named numeric arrays may be saved")
        if sum(v.nbytes for v in arrays.values()) > self.max_bytes:
            raise ValueError("Checkpoint size budget exceeded")
        buffer = io.BytesIO()
        np.savez(buffer, **arrays)
        payload = buffer.getvalue()
        if len(payload) > self.max_bytes:
            raise ValueError("Serialized size budget exceeded")
        metadata = {
            "checkpoint_version": "phase25.1",
            "serialization": "npz",
            "load_policy": "numpy_no_pickle",
            "cpu_loadable": True,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
            "provenance": dict(provenance),
            "arrays": {k: {"shape": list(v.shape), "dtype": str(v.dtype)} for k, v in arrays.items()},
        }
        with path.open("xb") as stream:
            stream.write(payload)
        write_once(metadata_path, metadata)
        return metadata

    def load_checkpoint(self, name, expected_provenance, *, expected_manifest_sha256=None):
        self._provenance(expected_provenance)
        if (
            expected_manifest_sha256 is not None
            and sha256_file(self._path(name, ".json")) != expected_manifest_sha256
        ):
            raise ValueError("Checkpoint manifest hash mismatch")
        metadata = json.loads(self._path(name, ".json").read_text(encoding="utf-8"))
        path = self._path(name, ".npz")
        if (
            metadata["provenance"] != expected_provenance
            or metadata.get("checkpoint_version") != "phase25.1"
            or metadata.get("load_policy") != "numpy_no_pickle"
        ):
            raise ValueError("Checkpoint provenance/load policy mismatch")
        if (
            path.stat().st_size != metadata["size_bytes"]
            or path.stat().st_size > self.max_bytes
            or sha256_file(path) != metadata["sha256"]
        ):
            raise ValueError("Checkpoint integrity mismatch")
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != metadata["sha256"]:
            raise ValueError("Checkpoint changed while loading")
        with zipfile.ZipFile(io.BytesIO(payload)) as packed:
            if sum(item.file_size for item in packed.infolist()) > self.max_bytes:
                raise ValueError("Expanded checkpoint exceeds size budget")
        with np.load(io.BytesIO(payload), allow_pickle=False) as archive:
            arrays = {k: archive[k] for k in archive.files}
        if set(arrays) != set(metadata["arrays"]) or any(
            list(v.shape) != metadata["arrays"][k]["shape"]
            or str(v.dtype) != metadata["arrays"][k]["dtype"]
            or v.dtype.kind not in "fiu"
            or not np.isfinite(v).all()
            for k, v in arrays.items()
        ):
            raise ValueError("Checkpoint tensor metadata mismatch")
        return arrays


def code_fingerprint(root, paths):
    root = Path(root)
    return canonical_sha256({str(path): sha256_file(root / path) for path in sorted(paths)})
