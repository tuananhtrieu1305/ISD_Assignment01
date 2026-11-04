"""Stage and serve the frozen CPU runtime from this monorepo, without GPU installs.

The development tree is never imported by Gunicorn. Repository Python sources
must agree with the release so a backend edit cannot silently serve stale code.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = "deploy/render-v3-r1/release.json"
MAX_ARCHIVE_BYTES = 100 * 1024**2
MAX_EXPANDED_BYTES = 160 * 1024**2
MAX_FILES = 3000


def file_digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_spec(root=ROOT):
    return json.loads((root / SPEC_PATH).read_text(encoding="utf-8"))


def safe_name(name):
    path = PurePosixPath(name)
    if (
        not name
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in name
        or ":" in name
        or path.as_posix() != name
        or any(part.startswith(".") for part in path.parts)
    ):
        raise ValueError("Unsafe deployment path: " + name)
    return name


def no_symlinks(path):
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("Deployment symlink is not permitted: " + str(path))


def archive_manifest(archive, spec):
    members = archive.infolist()
    names = set()
    for member in members:
        name = safe_name(member.filename)
        if stat.S_ISLNK(member.external_attr >> 16):
            raise ValueError("Deployment ZIP symlink is not permitted")
        if name in names:
            raise ValueError("Deployment ZIP duplicate path")
        names.add(name)
    total = sum(member.file_size for member in members)
    if len(members) > MAX_FILES or total > MAX_EXPANDED_BYTES:
        raise ValueError("Deployment ZIP budget exceeded")
    manifest_info = archive.getinfo("bundle_manifest.json")
    if manifest_info.file_size > 1024**2:
        raise ValueError("Deployment manifest budget exceeded")
    manifest_bytes = archive.read(manifest_info)
    if hashlib.sha256(manifest_bytes).hexdigest() != spec["manifest_sha256"]:
        raise ValueError("Deployment manifest hash mismatch")
    records = json.loads(manifest_bytes)["files"]
    expected = {}
    for record in records:
        name = safe_name(record["path"])
        if name in expected or name == "bundle_manifest.json":
            raise ValueError("Deployment manifest duplicate path")
        size = record["size_bytes"]
        if type(size) is not int or size < 0 or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"]):
            raise ValueError("Invalid deployment manifest record")
        expected[name] = record
    if (
        names != {*expected, "bundle_manifest.json"}
        or len(expected) != spec["file_count"]
        or sum(record["size_bytes"] for record in records) != spec["expanded_bytes"]
        or total != spec["expanded_bytes"] + len(manifest_bytes)
        or any(archive.getinfo(name).file_size != row["size_bytes"] for name, row in expected.items())
    ):
        raise ValueError("Deployment manifest file/count/size mismatch")
    return expected, manifest_bytes


def verify_repository_sources(repo, archive, records):
    for name in records:
        if not name.endswith(".py"):
            continue
        source = repo / name
        no_symlinks(source)
        if not source.is_file():
            raise ValueError("Repository source missing: " + name)
        # Git may normalize CRLF; serialized artifact bytes themselves never change.
        if source.read_bytes().replace(b"\r\n", b"\n") != archive.read(name).replace(b"\r\n", b"\n"):
            raise ValueError("Backend source changed; create an explicit deployment revision: " + name)


def verify_staged(output, records, manifest_bytes):
    manifest = output / "bundle_manifest.json"
    no_symlinks(manifest)
    if not manifest.is_file() or manifest.read_bytes() != manifest_bytes:
        raise ValueError("Invalid staged manifest; clear the generated build cache")
    for name, row in records.items():
        target = output / name
        no_symlinks(target)
        if (
            not target.is_file()
            or target.stat().st_size != row["size_bytes"]
            or file_digest(target) != row["sha256"]
        ):
            raise ValueError("Invalid staged file; clear the generated build cache: " + name)
    paths = list(output.rglob("*"))
    if any(path.is_symlink() for path in paths):
        raise ValueError("Unexpected staged symlink")
    actual = {path.relative_to(output).as_posix() for path in paths if path.is_file()}
    if actual != {*records, "bundle_manifest.json"}:
        raise ValueError("Unexpected staged file; clear the generated build cache")


def stage_bundle(archive_path, spec, output, *, repo=None):
    archive_path, output = Path(archive_path), Path(output)
    no_symlinks(archive_path)
    no_symlinks(output)
    if (
        not archive_path.is_file()
        or archive_path.stat().st_size != spec["archive"]["size_bytes"]
        or archive_path.stat().st_size > MAX_ARCHIVE_BYTES
        or file_digest(archive_path) != spec["archive"]["sha256"]
    ):
        raise ValueError("Deployment archive missing/changed (commit the real ZIP, not a Git LFS pointer)")
    with zipfile.ZipFile(archive_path) as archive:
        records, manifest_bytes = archive_manifest(archive, spec)
        if repo is not None:
            verify_repository_sources(repo, archive, records)
        if output.exists():
            verify_staged(output, records, manifest_bytes)
            return output
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=".render-stage-", dir=output.parent))
        for name in [*records, "bundle_manifest.json"]:
            target = temporary / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as source, target.open("xb") as destination:
                shutil.copyfileobj(source, destination)
        verify_staged(temporary, records, manifest_bytes)
        # Never recursively delete or overwrite an unrelated directory.
        temporary.rename(output)
    return output


def stage_repository(root=ROOT, output=None):
    spec = load_spec(root)
    archive_name = safe_name(spec["archive"]["path"])
    output = output or root / ".render-v3" / ("runtime-" + spec["archive"]["sha256"][:16])
    return stage_bundle(root / archive_name, spec, output, repo=root)


def runtime_environment(runtime, original=None):
    env = dict(os.environ if original is None else original)
    if env.get("AI_SERVING_MODE", "cpu") != "cpu":
        raise ValueError("Render deployment is CPU only")
    env.update(
        AI_SERVING_MODE="cpu",
        PYTHONPATH=str(runtime),
        PYTHONDONTWRITEBYTECODE="1",
        CUDA_VISIBLE_DEVICES="",
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
    )
    return env


def verify_runtime(runtime):
    subprocess.run(
        [sys.executable, "-B", "-m", "apps.api.v3.check_bundle"],
        cwd=runtime,
        env=runtime_environment(runtime),
        check=True,
        timeout=180,
    )


def build_runtime(runtime):
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "--require-hashes",
            "-r",
            str(runtime / "deploy/v3/requirements-cpu.lock"),
        ],
        cwd=runtime,
        env=runtime_environment(runtime),
        check=True,
    )
    verify_runtime(runtime)


def start_arguments(runtime, env):
    port = env.get("PORT", "10000")
    if not re.fullmatch(r"[0-9]{1,5}", port) or not 1 <= int(port) <= 65535:
        raise ValueError("PORT must be an integer from 1 to 65535")
    return [
        sys.executable,
        "-B",
        "-m",
        "gunicorn",
        "--chdir",
        str(runtime),
        "--bind",
        "0.0.0.0:" + port,
        "--workers",
        "1",
        "--threads",
        "2",
        "--timeout",
        "120",
        "apps.api.v3.server:create_app()",
    ]


def start_runtime(runtime):
    env = runtime_environment(runtime)
    os.chdir(runtime)
    os.execvpe(sys.executable, start_arguments(runtime, env), env)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["stage", "check", "build", "start"])
    parser.add_argument("--output", type=Path, help="Optional fresh staging path for local QA")
    args = parser.parse_args(argv)
    if sys.version_info[:3] != (3, 11, 17):
        parser.error("Use the pinned Python 3.11.17 runtime")
    runtime = stage_repository(output=args.output)
    if args.action == "build":
        build_runtime(runtime)
    elif args.action == "check":
        verify_runtime(runtime)
    elif args.action == "start":
        start_runtime(runtime)
    print(
        json.dumps(
            {
                "status": "PASS",
                "action": args.action,
                "runtime": str(runtime),
                "training_executed": False,
                "historical_test_executed": False,
            }
        )
    )


if __name__ == "__main__":
    main()
