"""Render build-time verification of the compact project, without inference."""

import json

from apps.api.v3.registry import Registry
from src.common.artifact_core import sha256_file
from src.common.contracts import ROOT, read_json


def main():
    manifest = read_json(ROOT / "bundle_manifest.json")
    for record in manifest["files"]:
        path = (ROOT / record["path"]).resolve()
        if (
            not path.is_relative_to(ROOT)
            or path.is_symlink()
            or path.stat().st_size != record["size_bytes"]
            or sha256_file(path) != record["sha256"]
        ):
            raise ValueError("Deployment bundle integrity check failed")
    rows = Registry().components()
    if any(row["status"] != "ready" for row in rows):
        raise ValueError("Deployment component unavailable")
    print(
        json.dumps(
            {
                "status": "PASS",
                "files": len(manifest["files"]),
                "components": len(rows),
                "inference_executed": False,
            }
        )
    )


if __name__ == "__main__":
    main()
