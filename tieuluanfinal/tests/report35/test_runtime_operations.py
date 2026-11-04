"""Bootstrap side effects exercised only on fake packages/fonts in pytest temp roots."""

import hashlib
import io
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import pytest
import scripts.phase35_runtime as r


@pytest.fixture
def private(tmp_path, monkeypatch):
    monkeypatch.setattr(r, "ROOT", tmp_path)
    monkeypatch.setattr(r, "RUNTIME", tmp_path / "runtime")
    monkeypatch.setattr(r, "GPU", tmp_path / "gpu")
    monkeypatch.setattr(r, "BASE", tmp_path / "evidence")
    r.BASE.mkdir()
    monkeypatch.setattr(r.shutil, "disk_usage", lambda _: SimpleNamespace(free=6 * 1024**3))
    return tmp_path


def test_download_is_hash_bounded_and_reuses_exact_content(private, monkeypatch):
    row = {
        "filename": "a.deb",
        "url": "https://example.invalid/a.deb",
        "bytes": 3,
        "sha256": hashlib.sha256(b"abc").hexdigest(),
    }
    monkeypatch.setattr(r.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(b"abc"))
    dest = r.download(row, private)
    assert dest.read_bytes() == b"abc"
    assert r.download(row, private) == dest
    dest.write_bytes(b"bad")
    with pytest.raises(ValueError):
        r.download(row, private)


@pytest.mark.parametrize("content", [b"abcd", b"ab", b"xxx"])
def test_download_failure_removes_only_owned_partial(private, monkeypatch, content):
    row = {
        "filename": "a.deb",
        "url": "https://example.invalid/a.deb",
        "bytes": 3,
        "sha256": hashlib.sha256(b"abc").hexdigest(),
    }
    monkeypatch.setattr(r.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(content))
    with pytest.raises(ValueError):
        r.download(row, private)
    assert not list(private.glob("*.part"))
    assert not (private / "a.deb").exists()


def test_resolver_uses_exact_apt_metadata_without_install(private, monkeypatch):
    def fake(args, **kwargs):
        if args[0] == "apt-get":
            return "'http://archive.ubuntu.com/a_1_amd64.deb' a_1_amd64.deb 3 abc\n"
        assert args == ["apt-cache", "show", "a=1"]
        return "Package: a\nVersion: 1\nFilename: pool/a_1_amd64.deb\nSize: 3\nSHA256: " + "a" * 64 + "\n"

    monkeypatch.setattr(r, "run", fake)
    r.resolve_apt()
    value = json.loads((r.BASE / "apt_lock.json").read_text())
    assert value["system_install_performed"] is False


def test_private_font_copy_uses_synthetic_files_only(private, monkeypatch):
    source = private / "fake-fonts"
    source.mkdir()
    names = [
        "calibri.ttf",
        "calibrib.ttf",
        "calibrii.ttf",
        "calibriz.ttf",
        "times.ttf",
        "timesbd.ttf",
        "timesi.ttf",
        "timesbi.ttf",
        "consola.ttf",
        "consolab.ttf",
        "consolai.ttf",
        "consolaz.ttf",
        "cambria.ttc",
        "seguisym.ttf",
    ]
    for name in names:
        (source / name).write_bytes(b"SYNTHETIC UNIT FILE NOT A FONT")
    r.RUNTIME.mkdir()
    monkeypatch.setattr(
        r, "Path", lambda value: source if str(value) == "/mnt/c/Windows/Fonts" else Path(value)
    )
    r.private_fonts()
    assert len(list((r.RUNTIME / "fonts").iterdir())) == 14
    assert json.loads((r.BASE / "local_fonts.json").read_text())["local_only_not_redistributable"]
    (source / "calibri.ttf").unlink()
    with pytest.raises(FileNotFoundError):
        r.private_fonts()


def test_rootless_extract_only_own_sysroot(private, monkeypatch):
    lock = {"root": str(r.RUNTIME), "packages": [{"filename": "fake.deb"}]}
    (r.BASE / "apt_lock.json").write_text(json.dumps(lock))

    def fake_download(row, directory):
        path = directory / row["filename"]
        path.write_bytes(b"unit")
        return path

    monkeypatch.setattr(r, "download", fake_download)

    def fake_run(args, **kwargs):
        assert args[0] == "dpkg-deb"
        sysroot = Path(args[-1])
        link = sysroot / "unit-link"
        link.symlink_to("/usr/bin/fake")
        return ""

    monkeypatch.setattr(r, "run", fake_run)
    monkeypatch.setattr(r, "private_fonts", lambda: None)
    monkeypatch.setattr(
        r.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, "fake version", "")
    )
    r.install_apt()
    assert (r.RUNTIME / "bin/pdfinfo").is_file()
    assert not (r.RUNTIME / "sysroot/unit-link").readlink().is_absolute()
    assert json.loads((r.BASE / "extraction.json").read_text())["packages"] == 1


def test_bootstrap_target_and_disk_guards(private, monkeypatch):
    path = r.BASE / "apt_lock.json"
    path.write_text(json.dumps({"root": "/not-owned", "packages": []}))
    with pytest.raises(ValueError):
        r.install_apt()
    path.write_text(json.dumps({"root": str(r.RUNTIME), "packages": []}))
    monkeypatch.setattr(r.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    with pytest.raises(RuntimeError):
        r.install_apt()


def test_config_relocation_in_synthetic_root(private, monkeypatch):
    program = r.RUNTIME / "sysroot/usr/lib/libreoffice/program"
    program.mkdir(parents=True)
    (program / "fundamentalrc").write_text("x=file:///usr/lib/libreoffice\n")
    (program / "unchangedrc").write_text("x=/usr/lib/other\n")
    monkeypatch.setattr(r.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, "unit", ""))
    r.relocate_program_configuration()
    changes = json.loads((r.BASE / "configuration_relocation.json").read_text())["changes"]
    assert len(changes) == 1


def test_python_setup_compiles_and_syncs_only_private_target(private, monkeypatch):
    (private / "experiments/environment/docs35").mkdir(parents=True)
    calls = []
    monkeypatch.setattr(r, "run", lambda args, **kw: calls.append((args, kw)) or "")
    r.python_setup()
    assert len(calls) == 4
    assert all(str(r.GPU / ".venv-torch") not in str(a) for a, k in calls if "sync" in a)
    assert calls[0][1]["env"]["UV_LINK_MODE"] == "copy"


def test_run_and_cli_are_checked(private, monkeypatch):
    monkeypatch.setattr(r.subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(a, 0, "unit", ""))
    assert r.run(["fake"]) == "unit"
    monkeypatch.setattr("sys.argv", ["phase35_runtime", "--stage", "resolve-apt"])
    calls = []
    monkeypatch.setattr(r, "resolve_apt", lambda: calls.append(True))
    r.main()
    assert calls == [True]


def test_incomplete_apt_line_rejected():
    with pytest.raises(ValueError):
        r.parse_apt_uris("'https://archive.ubuntu.com/a.deb' a.deb")
