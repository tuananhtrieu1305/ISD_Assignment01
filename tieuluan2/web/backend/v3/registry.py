"""Trusted, budgeted asset registry. Clients never select filesystem paths."""

from pathlib import Path, PurePosixPath

from src.common.artifact_core import sha256_file
from src.common.contracts import ROOT, read_json


class ArtifactError(ValueError):
    """Missing, changed or non-allowlisted deployment asset."""


class Registry:
    def __init__(self, path=None, *, expected_sha256=None, root=ROOT):
        from apps.api.v3.pins import REGISTRY_SHA256

        self.root = Path(root).resolve()
        path = Path(path or self.root / "artifacts/manifests/phase32/registry_v3.json")
        self.path = path
        try:
            if sha256_file(path) != (expected_sha256 or REGISTRY_SHA256):
                raise ArtifactError("Registry integrity check failed")
            self.document = read_json(path)
            self.files = {r["path"]: r for r in self.document["files"]}
            if len(self.files) != len(self.document["files"]) or len(self.files) > 3000:
                raise ArtifactError("Invalid registry budget")
            if sum(r["size_bytes"] for r in self.files.values()) > 160 * 1024**2:
                raise ArtifactError("Deployment bundle exceeds budget")
            self.models = {r["model_id"]: r for r in self.document["models"]}
            self.datasets = {r["dataset_id"]: r for r in self.document["datasets"]}
            self.chapters = self.document["chapters"]
        except (OSError, KeyError, TypeError, ValueError) as error:
            raise ArtifactError("Deployment registry unavailable") from error

    def checked(self, record):
        name = record["path"]
        parts = PurePosixPath(name)
        if (
            parts.is_absolute()
            or ".." in parts.parts
            or "\\" in name
            or ":" in name
            or name not in self.files
            or record["sha256"] != self.files[name]["sha256"]
        ):
            raise ArtifactError("Asset not allowlisted")
        path = self.root / name
        if not path.resolve().is_relative_to(self.root) or any(p.is_symlink() for p in [path, *path.parents]):
            raise ArtifactError("Asset path escapes trusted root")
        try:
            if path.stat().st_size != self.files[name]["size_bytes"] or sha256_file(path) != record["sha256"]:
                raise ArtifactError("Asset integrity check failed")
        except OSError as error:
            raise ArtifactError("Asset unavailable") from error
        return path

    def json(self, record):
        return read_json(self.checked(record))

    def components(self):
        rows = []
        for group in self.document["components"]:
            try:
                for record in group["assets"]:
                    self.checked(record)
                reason = None
            except ArtifactError:
                reason = "artifact_unavailable"
            rows.append({"id": group["id"], "status": "unavailable" if reason else "ready", "reason": reason})
        return rows
