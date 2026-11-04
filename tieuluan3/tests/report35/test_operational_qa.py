"""Synthetic helper tests plus a read-only integration inspection of the rendered PDF."""

import io
import json
from pathlib import Path
import subprocess
import tarfile
from types import SimpleNamespace
import zipfile
import pytest
from scripts.phase35_runtime import ROOT, digest
import scripts.phase35_inspect as inspection
import scripts.phase35_visual_review as visual
import scripts.phase35_smoke_bundle as bundle
import scripts.phase35_tdf as tdf


def test_real_pdf_geometry_and_index_cache():
    data = inspection.inspect(
        ROOT / "report/qa35/candidate-r12/candidate-r12.pdf",
        ROOT / "report/build/phase35/candidate-r12.build.json",
    )
    assert data["pages"] == 202
    assert not any(row["outside_safe"] for row in data["pages_detail"])
    build = json.loads((ROOT / "report/build/phase35/candidate-r12.build.json").read_text())
    for target in [r for r in build["headings"] if r["toc"]] + build["captions"]:
        assert data["page_map"][target["anchor"]] == build["page_map"][target["anchor"]]


def test_synthetic_review_ranges_must_be_sequential(tmp_path, monkeypatch):
    monkeypatch.setattr(visual, "ROOT", tmp_path)
    root = tmp_path / "report/qa35/candidate-r7"
    root.mkdir(parents=True)
    for n in range(1, 4):
        (root / f"page-{n}.png").write_bytes(b"SYNTHETIC NOT AN IMAGE")
    meta = tmp_path / "report/build/phase35"
    meta.mkdir(parents=True)
    (meta / "candidate-r7.build.json").write_text(json.dumps({"sha256": "synthetic"}))
    visual.record(1, 2, "SYNTHETIC UNIT FIXTURE, NOT ACTUAL HUMAN QA")
    with pytest.raises(ValueError):
        visual.record(2, 3, "duplicate")
    with pytest.raises(ValueError):
        visual.record(3, 4, "outside")
    visual.record(3, 3, "SYNTHETIC UNIT FIXTURE, NOT ACTUAL HUMAN QA")
    target = tmp_path / "report/qa35/candidate-r8"
    target.mkdir()
    for n in range(1, 4):
        (target / f"page-{n}.png").write_bytes(b"SYNTHETIC NOT AN IMAGE")
    (meta / "candidate-r8.build.json").write_text(json.dumps({"sha256": "synthetic-target"}))
    visual.carry("candidate-r7", "candidate-r8")
    with pytest.raises(ValueError):
        visual.carry("candidate-r8", "candidate-r8")
    with pytest.raises(ValueError):
        visual.carry("candidate-r99", "candidate-r100")
    with pytest.raises(ValueError):
        visual.record(1, 1, "bad", "../escape")


def test_bundle_main_only_in_private_temp_root(tmp_path, monkeypatch):
    monkeypatch.setattr(bundle, "ROOT", tmp_path)
    monkeypatch.setattr(bundle, "GPU", tmp_path / "fake-runtime")
    archive = tmp_path / "unit.zip"
    manifest = json.dumps({"files": []}).encode()
    import hashlib

    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("bundle_manifest.json", manifest)
        z.writestr("apps/api/__init__.py", b"unit")
    meta = {
        "archive": {"path": "unit.zip", "sha256": digest(archive), "size_bytes": archive.stat().st_size},
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "file_count": 1,
        "expanded_bytes": 4,
    }
    base = tmp_path / "artifacts/manifests/phase32"
    base.mkdir(parents=True)
    (base / "package_v2.json").write_text(json.dumps(meta))
    (tmp_path / "artifacts/manifests/phase35").mkdir()
    target = tmp_path / "compact"
    target.mkdir()
    monkeypatch.setattr(bundle.tempfile, "mkdtemp", lambda **kw: str(target))
    monkeypatch.setattr(
        bundle.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(
            a, 0, json.dumps({"status": "PASS", "inference_executed": False})
        ),
    )
    bundle.main()
    assert (target / "apps/api/__init__.py").read_bytes() == b"unit"
    with pytest.raises(FileExistsError):
        bundle.main()


def test_tdf_install_only_fake_debs_and_mock_execution(tmp_path, monkeypatch):
    root = tmp_path / "runtime"
    root.mkdir()
    (root / "bin").mkdir()
    (root / "bin/soffice").write_text("unit old wrapper")
    base = tmp_path / "evidence"
    base.mkdir()
    archive = tmp_path / "unit.tar.gz"
    with tarfile.open(archive, "w:gz") as z:
        row = tarfile.TarInfo("unit/DEBS/a.deb")
        row.size = 3
        z.addfile(row, io.BytesIO(b"abc"))
    (base / "tdf_lock.json").write_text(json.dumps({"root": str(root / "tdf")}))
    monkeypatch.setattr(tdf, "ROOT", tmp_path)
    monkeypatch.setattr(tdf, "RUNTIME", root)
    monkeypatch.setattr(tdf, "BASE", base)
    monkeypatch.setattr(tdf.resource, "setrlimit", lambda *a: None)
    monkeypatch.setattr(tdf.shutil, "disk_usage", lambda _: SimpleNamespace(free=6 * 1024**3))
    monkeypatch.setattr(tdf, "download", lambda *a: archive)

    def fake(args, **kw):
        if args[0] == "dpkg-deb":
            (Path(args[-1]) / "fake-link").symlink_to("/usr/bin/fake")
        return subprocess.CompletedProcess(args, 0, "unit version", "")

    monkeypatch.setattr(tdf.subprocess, "run", fake)
    tdf.install()
    assert json.loads((base / "probe.json").read_text())["system_install_performed"] is False
    assert not (root / "tdf/sysroot/fake-link").readlink().is_absolute()


def test_tdf_guard_and_deb_expansion_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(tdf, "BASE", tmp_path)
    (tmp_path / "tdf_lock.json").write_text(json.dumps({"root": "/invalid"}))
    monkeypatch.setattr(tdf.resource, "setrlimit", lambda *a: None)
    with pytest.raises(RuntimeError):
        tdf.install()
    member = tarfile.TarInfo("unit/DEBS/huge.deb")
    member.size = 501 * 1024**2
    with pytest.raises(ValueError):
        tdf.deb_members(SimpleNamespace(getmembers=lambda: [member]))
