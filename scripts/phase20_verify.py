"""Verify Phase 20 preservation and cleanup without training or opening sealed TEST."""

from __future__ import annotations

import argparse
import ast
import csv
import gzip
import hashlib
import json
import os
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DOCX_HASH = "d7286dd4867e6216f197414e42fc112a3759621c017839fa9b1491b7c5dbfa51"


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-validation-environment", action="store_true")
    parser.add_argument("--deploy", action="store_true", help="Verify only committed inference/release assets")
    args = parser.parse_args()
    checks: list[dict] = []

    def check(name: str, passed: bool, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    release = ROOT / "releases/v2"
    docx = release / "Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx"
    check("v2_docx_hash", docx.is_file() and sha256(docx) == EXPECTED_DOCX_HASH, EXPECTED_DOCX_HASH)
    if docx.is_file():
        with zipfile.ZipFile(docx) as archive:
            check("v2_docx_reopens", archive.testzip() is None and "word/document.xml" in archive.namelist(), len(archive.namelist()))

    seal_path = ROOT / "artifacts/manifests/ch5/phase15_test_run.json"
    seal = read_json(seal_path)
    check("ch5_test_run_count", seal.get("run_count") == 1, seal.get("run_count"))
    check("ch5_locked_config_identity", seal.get("locked_config_sha256") == "560c671a3920bd6bde9f7fc005f3c952f857c55969c989bb6109932623210c9e", seal.get("locked_config_sha256"))
    prediction_failures = []
    for artifact in seal["prediction_artifacts"]:
        moved = artifact["path"].replace(
            "term_paper/knowledge_rag/artifacts/predictions/phase15/",
            "artifacts/predictions/ch5/phase15/",
        )
        path = ROOT / moved
        if not path.is_file() or sha256(path) != artifact["sha256"]:
            prediction_failures.append(moved)
    check("ch5_sealed_predictions", not prediction_failures, {"files": len(seal["prediction_artifacts"]), "failures": prediction_failures})

    runtime_manifest = read_json(ROOT / "apps/api/models/kg_manifest.json")
    # The original runtime manifest is intentionally kept byte-for-byte; only its containing folder moved.
    runtime_failures = []
    for entry in runtime_manifest["files"]:
        path = ROOT / "apps/api/models" / entry["path"]
        if not path.is_file() or sha256(path) != entry["sha256"] or path.stat().st_size != entry["size_bytes"]:
            runtime_failures.append(entry["path"])
    check("kg_runtime_hashes", not runtime_failures, {"files": len(runtime_manifest["files"]), "failures": runtime_failures})

    for use_case in ("diabetes", "eurosat", "customer", "aapl"):
        demo = read_json(ROOT / f"data/processed/v2/demos/{use_case}.json")
        check(f"frozen_demo_{use_case}", demo.get("use_case") == use_case and "input" in demo, use_case)

    syntax_failures = []
    parsed = 0
    for directory in ("src", "apps/api", "tests", "scripts", "report", "term_paper"):
        for parent, directories, filenames in os.walk(ROOT / directory):
            directories[:] = [name for name in directories if not name.startswith(".venv") and name not in {"__pycache__", "node_modules"}]
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                path = Path(parent) / filename
                try:
                    ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
                    parsed += 1
                except (SyntaxError, UnicodeError) as error:
                    syntax_failures.append({"path": path.relative_to(ROOT).as_posix(), "error": str(error)})
    check("python_syntax", not syntax_failures, {"parsed": parsed, "failures": syntax_failures})

    if not args.deploy:
        forbidden = []
        for directory in ("apps", "src", "tests", "report", "experiments"):
            for parent, directories, _ in os.walk(ROOT / directory):
                for name in list(directories):
                    if name in {"node_modules", "__pycache__", ".pytest_cache", ".ipynb_checkpoints"} or name.startswith(".venv"):
                        directories.remove(name)
                        if args.allow_validation_environment and name.startswith(".venv"):
                            continue
                        forbidden.append((Path(parent) / name).relative_to(ROOT).as_posix())
        check("no_dependency_or_cache_directories", not forbidden, forbidden[:20])
        retired = [name for name in ("A05", "A06", "mobile", "datasets", "pipeline", "pipeline04", "backend", "web") if (ROOT / name).exists()]
        check("legacy_roots_retired", not retired, retired)

        notebook_failures = []
        notebooks = list((ROOT / "experiments/notebooks").rglob("*.ipynb"))
        for path in notebooks:
            try:
                notebook = read_json(path)
                if notebook.get("nbformat") != 4 or not isinstance(notebook.get("cells"), list):
                    notebook_failures.append(path.relative_to(ROOT).as_posix())
            except (ValueError, OSError):
                notebook_failures.append(path.relative_to(ROOT).as_posix())
        check("preserved_notebooks_valid", not notebook_failures, {"count": len(notebooks), "failures": notebook_failures})

        before_path = ROOT / "artifacts/manifests/phase20/before-files.csv"
        if before_path.exists():
            before_handle = before_path.open(encoding="utf-8-sig", newline="")
        else:
            before_handle = gzip.open(str(before_path) + ".gz", "rt", encoding="utf-8-sig", newline="")
        with before_handle as handle:
            before = list(csv.DictReader(handle))
        raw_records = [row for row in before if row["path"].startswith("term_paper/knowledge_rag/data/raw/")]
        raw_failures = []
        def verify_raw(row):
            moved = row["path"].replace("term_paper/knowledge_rag/data/raw/", "data/raw/ch5/")
            path = ROOT / moved
            if not path.is_file() or sha256(path) != row["sha256"]:
                return moved
            return None
        with ThreadPoolExecutor(max_workers=8) as workers:
            raw_failures = [failure for failure in workers.map(verify_raw, raw_records) if failure]
        check("ch5_raw_snapshot_unchanged", bool(raw_records) and not raw_failures, {"files": len(raw_records), "failures": raw_failures[:20]})

        snapshot = release / "source_snapshot.zip"
        snapshot_failures = []
        with (release / "source_snapshot_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
            members = list(csv.DictReader(handle))
        with zipfile.ZipFile(snapshot) as archive:
            for member in members:
                with archive.open(member["path"]) as handle:
                    if hashlib.file_digest(handle, "sha256").hexdigest() != member["sha256"]:
                        snapshot_failures.append(member["path"])
        check("source_snapshot_members", not snapshot_failures, {"count": len(members), "failures": snapshot_failures})

    result = {"status": "PASS" if all(item["passed"] for item in checks) else "FAIL", "checks": checks}
    output = ROOT / "artifacts/manifests/phase20" / ("deploy-verification.json" if args.deploy else "verification.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
