"""Read-only historical survey and selective restoration; never imports historical code."""
from __future__ import annotations

import argparse
import ast
import collections
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/reorganization"
SKIP = {".git", ".openai", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache", ".ipynb_checkpoints", ".expo", "site-packages"}
SPECS = {
    "A01": ("be8442eff", ["Assignment01_Final_5_Models.ipynb", "diabetes.csv", "vietnam_housing_dataset.csv", "artifacts/", "backend/", "web/", "neo4j_scripts/", ".python-version"]),
    "A02": ("0c27b1d2f", ["A02_CT_anhtt.053.ipynb", "datasets/", "artifacts/", "backend/", "web/", "neo4j_scripts/", ".python-version"]),
    "A03": ("d68985ea4", ["pipeline/", "datasets/", "A03_CT_anhtt.053.docx", "build_a03_report.py", "backend/", "web/", "artifacts/", "README.md", "neo4j_scripts/", "PIPELINE_UPGRADE_PLAN.md"]),
    "A04": ("3be831e88", ["pipeline04/", "datasets/", "backend/", "web/", "artifacts/", "README.md", "neo4j_scripts/", "PIPELINE_UPGRADE_PLAN.md"]),
    "A05": ("431f9f3c0", ["A05/"]),
    "A06": ("f1ff9c6a1", ["A06/"]),
    "tieuluan1": ("e7cf49bce", ["term_paper/", "backend/", "web/", "render.yaml", "RENDER_DEPLOY.md", "TIEU_LUAN_AI_EXECUTION_PLAN.md", "README.md"]),
}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-c", "core.filemode=false", "-C", str(ROOT), *args])


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write(name: str, value: object) -> None:
    target = OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def excluded(path: str) -> str | None:
    parts = PurePosixPath(path).parts
    for part in parts:
        if part in SKIP or part.startswith(".venv") or part in {"venv", "env", ".uv-cache"}:
            return "environment/cache/nested-metadata"
    if any(part in {"docx_render", "docx_render_a06", "docx_render_a06_v2", "docx_render_a06_v3", "docx_render_a06_verified", "contact_sheets", "node_modules"} for part in parts):
        return "intermediate-report-render"
    if path.endswith((".pyc", ".pyo", ".log", ".tsbuildinfo")):
        return "generated-cache/log"
    if PurePosixPath(path).name == ".env" or PurePosixPath(path).name.startswith(".env.") and not path.endswith(".env.example"):
        return "private-env-do-not-read"
    if "dist" in parts or "build" in parts or "coverage" in parts:
        return "generated-build"
    return None


def tree(commit: str) -> list[dict]:
    rows = []
    for entry in git("ls-tree", "-rlz", commit).split(b"\0"):
        if not entry:
            continue
        header, path = entry.split(b"\t", 1)
        mode, kind, oid, size = header.decode().split()
        rows.append({"path": path.decode("utf-8"), "oid": oid, "bytes": int(size) if size != "-" else 0, "mode": mode, "kind": kind})
    return rows


def blob(commit: str, path: str) -> bytes:
    return git("show", f"{commit}:{path}")


def notebook_info(payload: bytes, path: str) -> dict:
    doc = json.loads(payload)
    assert isinstance(doc.get("cells"), list), path
    codes = ["".join(c.get("source", [])) for c in doc["cells"] if c.get("cell_type") == "code"]
    text = "\n".join(codes)
    imports = sorted(set(re.findall(r"^\s*(?:from|import)\s+([\w.]+)", text, re.M)))
    interesting = [line.strip()[:400] for line in text.splitlines() if re.search(r"read_csv|read_excel|load_dataset|fetch_|download|DATA_DIR|DATA_ROOT|PROJECT_ROOT|BASE_DIR|Path\(|datasets[/\\]|data[/\\]|load_model|torch.load|joblib.load|\.fit\(|train\(|runpy|sys.path", line, re.I)]
    heads = ["".join(c.get("source", []))[:650] for c in doc["cells"] if c.get("cell_type") == "markdown"][:6]
    return {"path": path, "cells": len(doc["cells"]), "code_cells": len(codes), "output_cells": sum(bool(c.get("outputs")) for c in doc["cells"] if c.get("cell_type") == "code"), "imports": imports, "headings": heads, "io_and_execution_lines": interesting[:170], "contains_training_calls": bool(re.search(r"\.fit\(|\btrain\(|run_training", text)), "kernel": doc.get("metadata", {}).get("kernelspec")}


def survey() -> None:
    assert sys.version_info[:2] == (3, 11)
    OUT.mkdir(parents=True, exist_ok=True)
    cp = json.loads((OUT / "checkpoint.json").read_text(encoding="utf-8"))
    cp.update(status="IN_PROGRESS", active_phase=1, last_action="Survey started; historical code is not executed.", next_action="Read survey and select restoration payload.")
    cp["phases"]["1"]["status"] = "IN_PROGRESS"
    write("checkpoint.json", cp)
    status = json.loads((OUT / "windows_status_before.json").read_text(encoding="utf-8-sig"))
    write("phase1_preflight.json", {"head": git("rev-parse", "HEAD").decode().strip(), "git_status": status, "git_status_source": "native Windows Git; WSL NTFS stat scan stopped because slow", "python": sys.version, "executable": sys.executable, "free_bytes": shutil.disk_usage(ROOT).free, "packages": {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "scikit-learn", "torch", "nbformat", "nbclient")}, "process_names": subprocess.check_output(["ps", "-eo", "pid,comm"], text=True).splitlines(), "actions": "inventory only; no train/evaluation/import of historical code"})
    summaries = []
    notes = []
    all_selected = []
    for project, (ref, scopes) in SPECS.items():
        commit = git("rev-parse", ref).decode().strip()
        entries = tree(commit)
        selected = []
        reasons = collections.Counter()
        for row in entries:
            if not any(row["path"] == s or s.endswith("/") and row["path"].startswith(s) for s in scopes):
                reasons["outside-project-dependency-scope"] += 1
                continue
            reason = excluded(row["path"])
            if reason:
                reasons[reason] += 1
                continue
            selected.append(dict(row, project=project, commit=commit))
        write(f"survey/{project}_tree.json", {"commit": commit, "scopes": scopes, "selected": selected, "excluded_counts": dict(reasons), "tree_files": len(entries)})
        notebooks = []
        texts = []
        for row in selected:
            path = row["path"]
            if path.endswith(".ipynb"):
                notebooks.append(notebook_info(blob(commit, path), path))
            if (PurePosixPath(path).name.lower() in {"readme.md", "requirements.txt", "pyproject.toml", "config.py", "settings.py", "package.json", "render.yaml", "metadata.json", "feature_schema.json"} or path.endswith(("data_sources.json", "dataset_registry.json"))) and row["bytes"] < 100_000:
                texts.append({"path": path, "text": blob(commit, path).decode("utf-8", errors="replace")[:18000]})
        note = {"project": project, "commit": commit, "notebooks": notebooks, "documents": texts}
        write(f"survey/{project}_notes.json", note)
        notes.append(note)
        summaries.append({"project": project, "commit": commit, "selected_files": len(selected), "selected_bytes": sum(r["bytes"] for r in selected), "notebooks": [r["path"] for r in notebooks], "excluded_counts": dict(reasons), "largest": sorted(selected, key=lambda x: x["bytes"], reverse=True)[:6]})
        all_selected.extend(selected)
        print(project, len(selected), sum(r["bytes"] for r in selected), "bytes", len(notebooks), "notebooks", flush=True)
    for ref, path in [("0c27b1d2f", "A01_CT_anhtt.053.ipynb"), ("be8442eff", "Assignment01_Final_5_Models.ipynb")]:
        write(f"survey/A01_compare_{ref}.json", notebook_info(blob(ref, path), path))
    archive = ROOT / "releases/v2/source_snapshot.zip"
    with zipfile.ZipFile(archive) as z:
        members = [{"path": i.filename, "bytes": i.file_size, "compressed_bytes": i.compress_size} for i in z.infolist() if not i.is_dir()]
    write("survey/v2_snapshot_members.json", {"archive": str(archive.relative_to(ROOT)), "sha256": sha(archive), "members": members})
    write("survey/summary.json", {"projects": summaries, "staging_estimated_bytes": sum(r["bytes"] for r in all_selected), "unique_git_blob_bytes": sum({r["oid"]: r["bytes"] for r in all_selected}.values()), "free_bytes": shutil.disk_usage(ROOT).free})
    print("Survey saved; no historical file executed.", flush=True)


def local_files(base: Path, *, keep_metadata: bool = False):
    for current, dirs, files in os.walk(base):
        dirs[:] = sorted(d for d in dirs if keep_metadata or d not in SKIP and not d.startswith(".venv"))
        for name in sorted(files):
            path = Path(current) / name
            rel = path.relative_to(ROOT).as_posix()
            if name == ".env" or name.startswith(".env.") and name != ".env.example":
                continue
            if not keep_metadata and excluded(rel):
                continue
            yield path


def prepare() -> None:
    """Freeze explicit selection decisions, preserve uncommitted payload and index local data."""
    selected = []
    exclusions = []
    for project in SPECS:
        doc = json.loads((OUT / f"survey/{project}_tree.json").read_text())
        for row in doc["selected"]:
            path = row["path"]
            reason = None
            if project == "A05" and ("/annotations/trimaps/" in path or "/annotations/xmls/" in path):
                reason = "unused Pet segmentation/bounding-box annotation; classification uses trainval/test/list; exact original remains in Git"
            if any(part.startswith("._") for part in PurePosixPath(path).parts):
                reason = "AppleDouble metadata; not image/training payload"
            if reason:
                exclusions.append(dict(row, reason=reason))
            else:
                selected.append(row)
    # Latest submitted A01 has fuller feature analysis; preserve earlier version as history.
    secondary = tree("0c27b1d2f")
    for row in secondary:
        if row["path"] in {"A01_CT_anhtt.053.ipynb", "A01_CT_anhtt.053.html", "A01_CT_anhtt.053.pdf"}:
            selected.append(dict(row, project="A01", commit=git("rev-parse", "0c27b1d2f").decode().strip(), role="primary-submission"))
    # A04's comparisons explicitly read A03 notebook, metadata and comparisons.
    for row in tree("3be831e88"):
        if row["path"].startswith("pipeline/") and not excluded(row["path"]):
            selected.append(dict(row, project="A04", commit=git("rev-parse", "3be831e88").decode().strip(), role="A03-reference-dependency"))
    write("selection.json", {"files": selected, "excluded_selected_rows": exclusions, "selected_bytes": sum(x["bytes"] for x in selected), "scientific_execution": False, "decisions": {"A01": "primary A01_CT_anhtt.053.ipynb at assignment02 commit:107 cells/48 code+outputs; previous be8442 notebook 107/46 retained as history; A01 deployed model blobs unchanged between those commits", "A03": "d68985e touches only web/mobile header text; model/notebook data unchanged from8b3ba02", "tieuluan1": "e7cf49bce preserves4-chapter release and fixes CRLF-sensitive JSON artifact hash; do not replace by5-chapterV2", "A05": "53080 files are largely raw images/annotations, not an environment; no venv detected in selected tree; preserve27000EuroSAT+7390Petimages, exclude unused masks/xml/AppleDouble only", "A04": "restore27pipeline reference files required for A03-vs-A04 comparisons"}})
    backups = []
    archive = OUT / "backups/uncommitted_web_and_controls.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for base in (ROOT / "discovering_ai_agent/web-demo", ROOT / "agent02_assignment/web-demo"):
        paths.extend(local_files(base, keep_metadata=True))
    for name in ("AGENTS.md", "README.md", ".gitignore", "ASSIGN_REORGANIZATION_EXECUTION_PLAN.md", "docs/reorganization/checkpoint.json"):
        paths.append(ROOT / name)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in paths:
            rel = path.relative_to(ROOT).as_posix()
            digest = sha(path)
            z.write(path, rel)
            backups.append({"path": rel, "bytes": path.stat().st_size, "sha256": digest, "nested_metadata": "/.git/" in rel or "/.openai/" in rel})
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for row in backups:
            assert hashlib.sha256(z.read(row["path"])).hexdigest() == row["sha256"]
    write("backup_manifest.json", {"archive": archive.relative_to(ROOT).as_posix(), "sha256": sha(archive), "files": backups, "backup_validation": "every member SHA256 verified", "private_env_files": "excluded without reading"})
    local = []
    roots = ("data", "artifacts/models", "artifacts/manifests", "releases", "agent02_assignment/data", "discovering_ai_agent/evidence")
    for base in roots:
        for path in local_files(ROOT / base):
            local.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size})
    write("local_resource_index.json", {"files": local, "bytes": sum(r["bytes"] for r in local), "hash_policy": "size/path discovery index; hashes for selected resources and live baseline are separate"})
    print(f"Selection {len(selected)} files/{sum(r['bytes'] for r in selected)}bytes; backup{len(backups)}files verified; local index{len(local)}files", flush=True)


def restore() -> None:
    selection = json.loads((OUT / "selection.json").read_text())
    rows = selection["files"]
    required = selection["selected_bytes"]
    assert shutil.disk_usage(ROOT).free > required + 5 * 1024**3, "Insufficient staging budget; 5GiB reserve retained"
    staging = OUT / "staging"
    receipts = []
    proc = subprocess.Popen(["git", "-C", str(ROOT), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    assert proc.stdin and proc.stdout
    try:
        for number, row in enumerate(rows, 1):
            rel = PurePosixPath(row["path"])
            assert not rel.is_absolute() and ".." not in rel.parts
            target = staging / row["project"] / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                payload = target.read_bytes()
                assert hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest() == row["oid"], f"Staging conflict {target}"
            else:
                proc.stdin.write((row["oid"] + "\n").encode())
                proc.stdin.flush()
                header = proc.stdout.readline().decode().strip().split()
                assert len(header) == 3 and header[1] == "blob", header
                size = int(header[2])
                payload = proc.stdout.read(size)
                assert len(payload) == size and proc.stdout.read(1) == b"\n"
                assert hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest() == row["oid"]
                target.write_bytes(payload)
            assert len(payload) == row["bytes"]
            assert not payload.startswith(b"version https://git-lfs.github.com/spec/v1"), f"LFS pointer: {target}"
            receipts.append(dict(row, staging_path=target.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(payload).hexdigest()))
            if number % 2000 == 0:
                print(f"Restored {number}/{len(rows)}: {row['project']}", flush=True)
        proc.stdin.close()
        assert proc.wait(timeout=20) == 0
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=10)
    write("restoration_manifest.json", {"files": receipts, "count": len(receipts), "bytes": sum(r["bytes"] for r in receipts), "git_blob_identity": "PASS every file", "sha256": "computed every file", "lfs_pointers": 0, "historical_code_executed": False})
    print(f"Restored+Git-verified {len(receipts)} files", flush=True)


def baseline() -> None:
    """Hash live scientific/source payload; no historical or current model is loaded."""
    folders = ["apps", "src", "experiments", "data", "artifacts", "report", "releases", "requirements", "deploy", "term_paper", "tests", "discovering_ai_agent", "agent02_assignment"]
    rows = []
    for folder in folders:
        count = 0
        for path in local_files(ROOT / folder):
            rows.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
            count += 1
        print(f"Live baseline {folder}: {count} files", flush=True)
    for name in ("pyproject.toml", "uv.lock", ".python-version", "render.yaml"):
        path = ROOT / name
        rows.append({"path": name, "bytes": path.stat().st_size, "sha256": sha(path)})
    for path in sorted((ROOT / "scripts").glob("*")):
        if path.is_file() and not path.name.startswith("reorganization_"):
            rows.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    write("live_baseline_manifest.json", {"files": rows, "count": len(rows), "bytes": sum(r["bytes"] for r in rows), "exclusions": "env/cache/build/dist/private-env/nested-Git metadata; agent web dist fully backed up independently", "scientific_execution": False})
    print(f"Live baseline sealed {len(rows)} files", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["survey", "prepare", "restore", "baseline"])
    args = parser.parse_args()
    if args.stage == "survey":
        survey()
    elif args.stage == "prepare":
        prepare()
    elif args.stage == "restore":
        restore()
    elif args.stage == "baseline":
        baseline()


if __name__ == "__main__":
    main()
