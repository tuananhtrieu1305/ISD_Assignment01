"""Verify and stage the frozen production CPU ZIP on Linux ext4, without installation."""

import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tempfile
import zipfile
from scripts.phase35_runtime import ROOT, GPU, digest, write_once_json


def checked_members(archive, expected_count, expected_bytes):
    rows = archive.infolist()
    names = set()
    for row in rows:
        path = PurePosixPath(row.filename)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in row.filename
            or ":" in row.filename
            or row.filename in names
        ):
            raise ValueError("Unsafe ZIP path")
        if stat.S_ISLNK(row.external_attr >> 16):
            raise ValueError("Symlink not permitted")
        names.add(row.filename)
    files = [r for r in rows if not r.is_dir()]
    if len(files) != expected_count or sum(r.file_size for r in files) != expected_bytes:
        raise ValueError("ZIP count/size differs from locked package")
    return files


def main():
    metadata = json.loads((ROOT / "artifacts/manifests/phase32/package_v2.json").read_text())
    archive = ROOT / metadata["archive"]["path"]
    if (
        digest(archive) != metadata["archive"]["sha256"]
        or archive.stat().st_size != metadata["archive"]["size_bytes"]
    ):
        raise ValueError("Frozen archive changed")
    receipt = ROOT / "artifacts/manifests/phase35/compact_bundle_r2.json"
    if receipt.exists():
        raise FileExistsError("Already staged; inspect receipt rather than duplicate staging")
    with zipfile.ZipFile(archive) as z:
        manifest_data = z.read("bundle_manifest.json")
        import hashlib

        if (
            len(manifest_data) > 1024**2
            or hashlib.sha256(manifest_data).hexdigest() != metadata["manifest_sha256"]
        ):
            raise ValueError("Pinned bundle manifest mismatch")
        # Phase32 file_count/expanded_bytes refer to payload; the ZIP additionally contains its manifest.
        members = checked_members(
            z, metadata["file_count"] + 1, metadata["expanded_bytes"] + len(manifest_data)
        )
        directory = Path(tempfile.mkdtemp(prefix="phase35_cpu_"))
        for row in members:
            target = directory / row.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(row) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
    manifest = directory / "bundle_manifest.json"
    if digest(manifest) != metadata["manifest_sha256"]:
        raise ValueError("Bundle manifest changed")
    env = {
        **os.environ,
        "PYTHONPATH": str(directory),
        "CUDA_VISIBLE_DEVICES": "",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    result = subprocess.run(
        [str(GPU / ".venv-torch/bin/python"), "-B", "-m", "apps.api.v3.check_bundle"],
        cwd=directory,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    check = json.loads(result.stdout)
    assert check["status"] == "PASS" and check["inference_executed"] is False
    write_once_json(
        receipt,
        {
            "status": "PASS",
            "root": str(directory),
            "archive": metadata["archive"],
            "payload_expanded_bytes": metadata["expanded_bytes"],
            "payload_file_count": metadata["file_count"],
            "archive_files": len(members),
            "total_expanded_bytes": metadata["expanded_bytes"] + len(manifest_data),
            "verification": check,
            "gpu_environment_modified": False,
            "fresh_cpu_only_venv": False,
            "scope": "Frozen production project on ext4; existing pinned Python env; local only, no cloud",
        },
    )
    print(json.dumps({"root": str(directory), "verification": check}))


if __name__ == "__main__":
    main()
