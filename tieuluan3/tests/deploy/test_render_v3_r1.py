"""Deploy-only tests; never train models or reopen scientific TEST splits."""

import hashlib
import json
import stat
import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts import render_v3


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def make_bundle(tmp_path, files=None, extra=None):
    files = files or {"apps/api/v3/server.py": b"# frozen source\n", "artifacts/model.npz": b"weights"}
    manifest = json.dumps(
        {
            "files": [
                {"path": name, "sha256": digest(data), "size_bytes": len(data)}
                for name, data in files.items()
            ]
        }
    ).encode()
    archive = tmp_path / "bundle.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        for name, data in files.items():
            stream.writestr(name, data)
        stream.writestr("bundle_manifest.json", manifest)
        if extra:
            stream.writestr(*extra)
    spec = {
        "archive": {
            "path": "bundle.zip",
            "sha256": digest(archive.read_bytes()),
            "size_bytes": archive.stat().st_size,
        },
        "manifest_sha256": digest(manifest),
        "file_count": len(files),
        "expanded_bytes": sum(map(len, files.values())),
    }
    return archive, spec, files


def test_stage_exact_bytes_and_idempotent(tmp_path):
    archive, spec, files = make_bundle(tmp_path)
    output = tmp_path / "runtime"
    assert render_v3.stage_bundle(archive, spec, output) == output
    assert render_v3.stage_bundle(archive, spec, output) == output
    for name, data in files.items():
        assert (output / name).read_bytes() == data


@pytest.mark.parametrize("field,value", [("sha256", "0" * 64), ("size_bytes", 0)])
def test_reject_changed_archive(tmp_path, field, value):
    archive, spec, _ = make_bundle(tmp_path)
    spec["archive"][field] = value
    with pytest.raises(ValueError, match="archive"):
        render_v3.stage_bundle(archive, spec, tmp_path / "runtime")


@pytest.mark.parametrize(
    "name", ["../escape", "/absolute", "C:/file", "a\\b", "a/../b", "a//b", "./file", ".env"]
)
def test_reject_unsafe_member(tmp_path, name):
    archive, spec, _ = make_bundle(tmp_path, {name: b"x"})
    with pytest.raises(ValueError, match="path"):
        render_v3.stage_bundle(archive, spec, tmp_path / "runtime")
    assert not (tmp_path / "escape").exists()


def test_reject_symlink_archive_member(tmp_path):
    member = zipfile.ZipInfo("apps/link")
    member.create_system = 3
    member.external_attr = (stat.S_IFLNK | 0o777) << 16
    archive, spec, _ = make_bundle(tmp_path, extra=(member, "target"))
    with pytest.raises(ValueError, match="symlink"):
        render_v3.stage_bundle(archive, spec, tmp_path / "runtime")


def test_reject_duplicate_archive_member(tmp_path):
    with pytest.warns(UserWarning):
        archive, spec, _ = make_bundle(tmp_path, extra=("apps/api/v3/server.py", "bad"))
    with pytest.raises(ValueError, match="duplicate"):
        render_v3.stage_bundle(archive, spec, tmp_path / "runtime")


@pytest.mark.parametrize(
    "field,value", [("manifest_sha256", "0" * 64), ("file_count", 999), ("expanded_bytes", 0)]
)
def test_reject_manifest_or_budget_mismatch(tmp_path, field, value):
    archive, spec, _ = make_bundle(tmp_path)
    spec[field] = value
    with pytest.raises(ValueError):
        render_v3.stage_bundle(archive, spec, tmp_path / "runtime")


def test_reject_extra_file(tmp_path):
    archive, spec, _ = make_bundle(tmp_path, extra=("apps/unexpected.py", "bad"))
    with pytest.raises(ValueError):
        render_v3.stage_bundle(archive, spec, tmp_path / "runtime")


def test_reject_changed_staged_file(tmp_path):
    archive, spec, _ = make_bundle(tmp_path)
    output = render_v3.stage_bundle(archive, spec, tmp_path / "runtime")
    (output / "artifacts/model.npz").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="staged"):
        render_v3.stage_bundle(archive, spec, output)


def test_reject_existing_unrelated_output_without_deletion(tmp_path):
    archive, spec, _ = make_bundle(tmp_path)
    output = tmp_path / "runtime"
    output.mkdir()
    keep = output / "user.txt"
    keep.write_text("keep")
    with pytest.raises(ValueError, match="staged"):
        render_v3.stage_bundle(archive, spec, output)
    assert keep.read_text() == "keep"


def test_reject_output_symlink(tmp_path):
    archive, spec, _ = make_bundle(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    output = tmp_path / "runtime"
    output.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        render_v3.stage_bundle(archive, spec, output)


def test_source_guard_accepts_git_line_endings_but_not_code_changes(tmp_path):
    archive, spec, files = make_bundle(tmp_path)
    repo = tmp_path / "repo"
    source = repo / "apps/api/v3/server.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(files["apps/api/v3/server.py"].replace(b"\n", b"\r\n"))
    render_v3.stage_bundle(archive, spec, tmp_path / "runtime", repo=repo)
    source.write_bytes(b"# edited code\n")
    with pytest.raises(ValueError, match="revision"):
        render_v3.stage_bundle(archive, spec, tmp_path / "another", repo=repo)


def test_missing_repository_source_is_not_silently_hidden_by_zip(tmp_path):
    archive, spec, _ = make_bundle(tmp_path)
    with pytest.raises(ValueError, match="source"):
        render_v3.stage_bundle(archive, spec, tmp_path / "runtime", repo=tmp_path / "repo")


@pytest.mark.parametrize("port", ["0", "65536", "abc", "5000 --workers 4", "-1"])
def test_invalid_port(port):
    with pytest.raises(ValueError, match="PORT"):
        render_v3.start_arguments(Path("/runtime"), {"PORT": port})


def test_start_single_worker_and_cpu_environment():
    args = render_v3.start_arguments(Path("/runtime"), {"PORT": "10000"})
    assert args[args.index("--workers") + 1] == "1"
    assert args[args.index("--threads") + 1] == "2"
    assert "0.0.0.0:10000" in args
    assert args[-1] == "apps.api.v3.server:create_app()"
    env = render_v3.runtime_environment(Path("/runtime"), {"PYTHONPATH": "/old", "AI_SERVING_MODE": "cpu"})
    assert env["PYTHONPATH"] == "/runtime"
    assert env["CUDA_VISIBLE_DEVICES"] == ""
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"


def test_reject_gpu_on_render():
    with pytest.raises(ValueError, match="CPU"):
        render_v3.runtime_environment(Path("/runtime"), {"AI_SERVING_MODE": "local_gpu"})


def test_build_installs_only_hash_locked_cpu_dependencies(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(render_v3.subprocess, "run", lambda args, **kw: calls.append((args, kw)))
    render_v3.build_runtime(tmp_path)
    assert "--require-hashes" in calls[0][0]
    assert "--no-cache-dir" in calls[0][0]
    assert calls[0][0][-1].endswith("requirements-cpu.lock")
    assert calls[1][0][-1] == "apps.api.v3.check_bundle"
    assert all(kw["check"] for _, kw in calls)


def test_start_execs_without_shell(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(render_v3.os, "execvpe", lambda *args: calls.append(args))
    monkeypatch.setattr(render_v3.os, "chdir", lambda path: None)
    monkeypatch.setenv("PORT", "10000")
    monkeypatch.setenv("AI_SERVING_MODE", "cpu")
    render_v3.start_runtime(tmp_path)
    assert calls[0][0] == render_v3.sys.executable
    assert calls[0][1][-1] == "apps.api.v3.server:create_app()"


def test_extra_staged_file_is_rejected(tmp_path):
    archive, spec, _ = make_bundle(tmp_path)
    output = render_v3.stage_bundle(archive, spec, tmp_path / "runtime")
    (output / "extra.py").write_text("# not allowlisted")
    with pytest.raises(ValueError, match="Unexpected staged"):
        render_v3.stage_bundle(archive, spec, output)


def test_staged_symlink_is_rejected(tmp_path):
    archive, spec, _ = make_bundle(tmp_path)
    output = render_v3.stage_bundle(archive, spec, tmp_path / "runtime")
    (output / "empty").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        render_v3.stage_bundle(archive, spec, output)


@pytest.mark.parametrize(
    "constant,value", [("MAX_ARCHIVE_BYTES", 1), ("MAX_FILES", 1), ("MAX_EXPANDED_BYTES", 1)]
)
def test_absolute_budget_limits(tmp_path, monkeypatch, constant, value):
    archive, spec, _ = make_bundle(tmp_path)
    monkeypatch.setattr(render_v3, constant, value)
    with pytest.raises(ValueError):
        render_v3.stage_bundle(archive, spec, tmp_path / "runtime")


@pytest.mark.parametrize("action", ["stage", "check", "build", "start"])
def test_cli_dispatch(monkeypatch, tmp_path, capsys, action):
    calls = []
    monkeypatch.setattr(render_v3, "stage_repository", lambda **kw: tmp_path)
    for method in ("verify_runtime", "build_runtime", "start_runtime"):
        monkeypatch.setattr(render_v3, method, lambda runtime: calls.append(runtime))
    render_v3.main([action])
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["status"] == "PASS"
    assert receipt["training_executed"] is False
    assert len(calls) == (0 if action == "stage" else 1)


def test_cli_rejects_wrong_python(monkeypatch):
    monkeypatch.setattr(render_v3.sys, "version_info", (3, 12, 14))
    with pytest.raises(SystemExit):
        render_v3.main(["stage"])


def test_check_uses_isolated_cwd(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(render_v3.subprocess, "run", lambda args, **kw: calls.append((args, kw)))
    render_v3.verify_runtime(tmp_path)
    assert calls[0][1]["cwd"] == tmp_path
    assert calls[0][1]["env"]["PYTHONPATH"] == str(tmp_path)


def test_real_repository_source_guard_and_stage(tmp_path):
    root = Path(__file__).resolve().parents[2]
    output = render_v3.stage_repository(root, output=tmp_path / "clean-runtime")
    assert (output / "apps/api/v3/server.py").is_file()
    raw = sorted(
        path.relative_to(output).as_posix() for path in (output / "data/raw").rglob("*") if path.is_file()
    )
    assert len(raw) == 11
    assert all(name.startswith("data/raw/ch5/wikidata/") and name.endswith(".json") for name in raw)
    assert not (output / "data/raw/ch3").exists()
    assert not (output / "scripts/package_phase32.py").exists()


def test_committed_python_sources_match_frozen_runtime():
    root = Path(__file__).resolve().parents[2]
    spec = render_v3.load_spec(root)
    with zipfile.ZipFile(root / spec["archive"]["path"]) as archive:
        for name in archive.namelist():
            if not name.endswith(".py"):
                continue
            committed = subprocess.run(
                ["git", "show", "HEAD:" + name], cwd=root, capture_output=True, check=True
            ).stdout
            assert committed.replace(b"\r\n", b"\n") == archive.read(name).replace(b"\r\n", b"\n"), name


def test_real_release_archive_is_git_visible_not_lfs_pointer():
    root = Path(__file__).resolve().parents[2]
    spec = render_v3.load_spec(root)
    archive = root / spec["archive"]["path"]
    assert archive.is_file()
    assert archive.stat().st_size < 100 * 1024**2
    assert archive.read_bytes()[:2] == b"PK"


def test_root_blueprint_is_v3_and_keeps_existing_service_names():
    import yaml

    root = Path(__file__).resolve().parents[2]
    services = yaml.safe_load((root / "render.yaml").read_text())["services"]
    api, web = services
    assert api["name"] == "isd-assignment01-api"
    assert "scripts/render_v3.py build" in api["buildCommand"]
    assert "scripts/render_v3.py start" in api["startCommand"]
    assert "rootDir" not in api
    assert web["name"] == "isd-assignment01-web"
    assert web["rootDir"] == "apps/web"
    assert web["staticPublishPath"] == "dist"
    assert web["routes"] == [{"type": "rewrite", "source": "/*", "destination": "/index.html"}]
    env = {v["key"]: v.get("value") for v in web["envVars"]}
    assert env["VITE_API_BASE_URL"] == "https://isd-assignment01-api.onrender.com"
    assert env["NODE_VERSION"] == "22.23.4"
