"""Read-only inventory and exact content guards for the migrated Chapter5 baseline."""

import csv
import gzip
import re
from pathlib import PurePosixPath

from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json

BASE = ROOT / "artifacts/manifests/phase30"
RUNTIME = "apps/api/models/kg_manifest.json"
RUNTIME_SHA = "8b58e70d6d892cd697e8174ccdbaad78bcd0098a9cd2bc23ca2fda5724823073"
SEAL = "artifacts/manifests/ch5/phase15_test_run.json"
SEAL_SHA = "64f4167eb039903d9a70f56cf6c24a761ec59ad6986faa03f866b97856c7b929"
LOCKED = "experiments/configs/ch5/phase15_locked.json"
LOCKED_SHA = "560c671a3920bd6bde9f7fc005f3c952f857c55969c989bb6109932623210c9e"


def checked(record, root=ROOT):
    name, digest = record["path"], record["sha256"]
    if (
        not isinstance(name, str)
        or not name
        or "\\" in name
        or ":" in name
        or PurePosixPath(name).is_absolute()
        or ".." in PurePosixPath(name).parts
        or not isinstance(digest, str)
        or not re.fullmatch("[a-f0-9]{64}", digest)
    ):
        raise ValueError("Unsafe artifact reference")
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Artifact missing or outside workspace")
    if sha256_file(path) != digest:
        raise ValueError("Artifact hash mismatch: " + name)
    return path


def ref(path, root=ROOT):
    return {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}


def verify_records(records, root=ROOT):
    seen = set()
    for row in records:
        if row["path"] in seen:
            raise ValueError("Duplicate artifact reference")
        checked(row, root)
        seen.add(row["path"])
    return len(seen)


def historical_baseline():
    counts = {"raw": 0, "config": 0, "metric": 0}
    mappings = (
        ("raw", "term_paper/knowledge_rag/data/raw/", "data/raw/ch5/"),
        ("config", "term_paper/knowledge_rag/config/", "experiments/configs/ch5/"),
        ("metric", "term_paper/knowledge_rag/artifacts/metrics/", "artifacts/metrics/ch5/"),
    )
    with gzip.open(
        ROOT / "artifacts/manifests/phase20/before-files.csv.gz", "rt", encoding="utf-8-sig", newline=""
    ) as stream:
        for row in csv.DictReader(stream):
            for kind, old, new in mappings:
                if row["path"].startswith(old):
                    checked({"path": new + row["path"][len(old) :], "sha256": row["sha256"]})
                    counts[kind] += 1
    if counts != {"raw": 11345, "config": 7, "metric": 23}:
        raise ValueError("Historical baseline inventory incomplete")
    checked({"path": SEAL, "sha256": SEAL_SHA})
    checked({"path": LOCKED, "sha256": LOCKED_SHA})
    seal = read_json(ROOT / SEAL)
    if seal["status"] != "COMPLETE" or seal["run_count"] != 1 or seal["locked_config_sha256"] != LOCKED_SHA:
        raise ValueError("Historical TEST seal changed")
    for record in seal["prediction_artifacts"]:
        checked(
            {
                "path": record["path"].replace(
                    "term_paper/knowledge_rag/artifacts/predictions/", "artifacts/predictions/ch5/"
                ),
                "sha256": record["sha256"],
            }
        )
    return {**counts, "sealed_predictions": len(seal["prediction_artifacts"]), "test_run_count": 1}


def create_snapshot():
    path = BASE / "preserved_snapshot.json"
    if path.exists():
        document = read_json(path)
        verify_records(document["files"])
        return document
    print("Phase30: checking original raw/config/metric/TEST baseline", flush=True)
    baseline = historical_baseline()
    print("Phase30: baseline PASS; inventory of preserved migrated assets", flush=True)
    folders = (
        "data/raw/ch5",
        "experiments/configs/ch5",
        "artifacts/manifests/ch5",
        "artifacts/metrics/ch5",
        "artifacts/predictions/ch5",
        "artifacts/figures/ch5",
        "src/term_paper/tools",
        "report/assets/ch5_knowledge_rag",
        "report/references/dataset_cards/ch5",
    )
    files = {
        p
        for folder in folders
        for p in (ROOT / folder).rglob("*")
        if p.is_file() and (folder == "data/raw/ch5" or "__pycache__" not in p.parts)
    }
    files.update((ROOT / "apps/api/models").glob("kg*"))
    files.update((ROOT / "report/references/dataset_cards").glob("ch5*.md"))
    for name in (
        "term_paper/__init__.py",
        "apps/api/knowledge_rag_service.py",
        "report/sections/05_knowledge_rag.md",
        "report/references/bibliography.bib",
        "uv.lock",
        "pyproject.toml",
        "artifacts/manifests/environment.json",
        "artifacts/manifests/phase29/experiment_lock.json",
        "releases/v2/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx",
    ):
        files.add(ROOT / name)
    dependencies = []
    for name in ("phase22/spec_lock.json", "phase24/data_lock.json", "phase25/core_lock.json"):
        lock_path = ROOT / "artifacts/manifests" / name
        lock = read_json(lock_path)
        verify_records(lock["files"])
        dependencies.append({**ref(lock_path), "verified_files": len(lock["files"])})
        files.add(lock_path)
    document = {
        "phase": 30,
        "status": "PASS",
        "baseline": baseline,
        "dependencies": dependencies,
        "files": [ref(p) for p in sorted(files)],
        "new_test_evaluation_executed": False,
        "policy": "Read-only original bytes; no rebuild, tuning, public TEST rerun or reserialization",
    }
    write_once(path, document)
    return document
