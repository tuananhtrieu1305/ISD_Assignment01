"""Prospective CNN experiment contract; configuration must precede updates."""

import subprocess
from pathlib import Path

from scripts.prepare_phase25 import CORE_FILES
from src.ch02_ml.protocol import PHASE26_FILES
from src.common.artifact_core import code_fingerprint, sha256_file
from src.common.contracts import PROTOCOL, ROOT, read_json

BASE = ROOT / "artifacts/manifests/phase27"
MODELS = ROOT / "artifacts/models/v3/ch03_cnn"
METRICS = ROOT / "artifacts/metrics/phase27"
PREDICTIONS = ROOT / "artifacts/predictions/phase27"
DATASETS = ("ch3_idrid", "ch3_eurosat", "ch3_cifar10")
SEEDS = (17, 42, 73)
IMPLEMENTATIONS = ("scratch", "keras", "pytorch")
SOURCE_FILES = sorted(
    set(
        CORE_FILES
        + PHASE26_FILES
        + [
            f"src/ch03_cnn/{name}.py"
            for name in ("image_cache", "training", "workflow", "protocol", "experiment")
        ]
        + [
            "scripts/prepare_phase27.py",
            "scripts/phase27_worker.py",
            "scripts/phase27_controller.py",
            "experiments/configs/v3/phase27_coverage.ini",
        ]
        + [
            f"src/common/{name}.py"
            for name in (
                "contracts",
                "acquisition",
                "source_inspection",
                "provenance",
                "eda_sources",
                "eda_artifacts",
                "data_v3",
            )
        ]
    )
)


def ref(path):
    return {"path": Path(path).relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}


def code_info():
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    return {"git_commit": head, "dirty_tree_sha256": code_fingerprint(ROOT, SOURCE_FILES)}


def run_ids():
    return [
        f"{dataset}_{'cnn_' + method if method in IMPLEMENTATIONS else method}_s{seed}"
        for dataset in DATASETS
        for seed in SEEDS
        for method in (*IMPLEMENTATIONS, "majority")
    ]


def check_sources():
    release = read_json(BASE / "release.json")
    if (
        release["code"] != code_info()
        or release["protocol"] != ref(PROTOCOL)
        or release["environment"] != ref(ROOT / "uv.lock")
    ):
        raise ValueError("CNN declared source/protocol/environment changed; versioned revision required")
    for record in release["source_files"]:
        if ref(ROOT / record["path"]) != record:
            raise ValueError("CNN source hash mismatch")
    for entry in release["runs"]:
        for key in ("config", "model_contract"):
            if ref(ROOT / entry[key]["path"]) != entry[key]:
                raise ValueError("CNN config/contract hash mismatch")
    return release
