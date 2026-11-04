"""Chapter2 prospective configuration and protected development data access."""

from __future__ import annotations

import hashlib
import os
import subprocess
import uuid
from pathlib import Path

import numpy as np

from scripts.prepare_phase25 import CORE_FILES
from src.ch02_ml.diagnostics import groups_for_frame
from src.common.artifact_core import code_fingerprint, sha256_file, write_once
from src.common.contracts import PROTOCOL, ROOT, canonical_sha256, read_json
from src.common.data_access import DatasetView
from src.common.eda_artifacts import read_rows
from src.common.eda_sources import load_tabular
from src.common.tensor_adapters import select_rows

BASE = ROOT / "artifacts/manifests/phase26/revisions/r2"
CACHE = ROOT / "data/processed/v3/phase26/r2"
MODELS = ROOT / "artifacts/models/v3/ch02_ml"
METRICS = ROOT / "artifacts/metrics/phase26"
PREDICTIONS = ROOT / "artifacts/predictions/phase26"
DATASETS = ("ch2_cdc_diabetes", "ch2_ames_housing", "ch2_bank_marketing")
SEEDS = (17, 42, 73)
IMPLEMENTATIONS = ("scratch", "keras", "pytorch")
PHASE26_FILES = [
    f"src/ch02_ml/{name}.py"
    for name in ("protocol", "training", "baselines", "diagnostics", "test_gate", "experiment", "workflow")
] + [
    "scripts/phase26_worker.py",
    "scripts/prepare_phase26.py",
    "scripts/phase26_controller.py",
    "scripts/verify_phase26.py",
    "experiments/configs/v3/phase26_coverage.ini",
    "scripts/run_experiment.sh",
    "scripts/runtime_common.sh",
    "scripts/tensorflow_libraries.py",
]
SOURCE_FILES = sorted(
    set(
        CORE_FILES
        + PHASE26_FILES
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


def array_sha256(value):
    value = np.ascontiguousarray(value)
    return hashlib.sha256(
        canonical_sha256({"shape": list(value.shape), "dtype": str(value.dtype)}).encode() + value.tobytes()
    ).hexdigest()


def dataset_spec(dataset):
    if dataset not in DATASETS:
        raise ValueError("Not a Chapter2 dataset")
    return next(row for row in read_json(PROTOCOL)["datasets"] if row["dataset_id"] == dataset)


def task_for(dataset):
    return "mse" if dataset_spec(dataset)["task"] == "regression" else "binary"


def baseline_names(dataset):
    return dataset_spec(dataset)["baselines"]


def run_ids():
    return [
        f"{dataset}_{'mlp_' + method if method in IMPLEMENTATIONS else method}_s{seed}"
        for dataset in DATASETS
        for seed in SEEDS
        for method in (*IMPLEMENTATIONS, *baseline_names(dataset))
    ]


def code_info():
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    return {"git_commit": head, "dirty_tree_sha256": code_fingerprint(ROOT, SOURCE_FILES)}


def check_sources():
    release = read_json(BASE / "release.json")
    if release["code"]["dirty_tree_sha256"] != code_info()["dirty_tree_sha256"]:
        raise ValueError("Phase26 source changed; do not resume/release old configuration silently")
    return release


def development_data(dataset, partition):
    dataset_spec(dataset)
    if partition not in {"train", "validation"}:
        raise ValueError("Development data excludes TEST")
    view = DatasetView(dataset)
    ids = view.ids(partition)
    x, y = view.batch(ids, "scratch")
    return {"ids": ids, "x": x, "y": y, "view": view}


def cache_data(dataset):
    path = CACHE / f"{dataset}_development.npz"
    receipt_path = BASE / "data" / f"{dataset}.json"
    if path.exists() and receipt_path.exists():
        receipt = read_json(receipt_path)
        if sha256_file(path) != receipt["cache"]["sha256"]:
            raise ValueError("Development tensor cache hash mismatch")
        with np.load(path, allow_pickle=False) as archive:
            arrays = {k: archive[k] for k in archive.files}
        return arrays
    train = development_data(dataset, "train")
    view = train["view"]
    val_ids = view.ids("validation")
    val_x, val_y = view.batch(val_ids, "scratch")
    positions = select_rows(view._source_ids, val_ids)
    arrays = {
        "train_x": train["x"],
        "train_y": train["y"],
        "train_ids": np.asarray(train["ids"]),
        "validation_x": val_x,
        "validation_y": val_y,
        "validation_ids": np.asarray(val_ids),
        "validation_target_original": view._targets[positions].astype(float),
        "validation_groups": groups_for_frame(dataset, view._frame.iloc[positions]),
    }
    if any(value.dtype.kind == "O" for value in arrays.values()):
        raise ValueError("Development cache must not contain pickle/object arrays")
    from src.common.eda_artifacts import clean

    demo_positions = select_rows(view._source_ids, train["ids"][:4])
    demo = {
        "dataset_id": dataset,
        "split": "train",
        "ids": train["ids"][:4],
        "input_features": clean(view._frame.iloc[demo_positions].to_dict(orient="records")),
        "known_outputs": clean(view._targets[demo_positions].tolist()),
        "canonical_x_sha256": array_sha256(train["x"][:4]),
    }
    write_once(BASE / "data" / f"{dataset}_demo.json", demo)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{uuid.uuid4().hex}.tmp")
    with temporary.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    os.replace(temporary, path)
    receipt = {
        "dataset_id": dataset,
        "cache": ref(path),
        "array_hashes": {k: array_sha256(v) for k, v in arrays.items()},
        "provenance": view.provenance,
        "training_ids": len(train["ids"]),
        "validation_ids": len(val_ids),
        "test_accessed": False,
    }
    write_once(receipt_path, receipt)
    return arrays


def test_data(dataset, gate):
    """Only this evaluator path opens target values; caller must already own a claim."""
    if gate.state()["state"] != "evaluating" or gate.state()["dataset_id"] != dataset:
        raise ValueError("No active dataset TEST authorization")
    view = DatasetView(dataset)
    split = read_json(view.split_dir / "split_contract.json")
    if gate.state()["split_sha256"] != view.provenance["split_sha256"]:
        raise ValueError("TEST split hash changed")
    partition = next(row for row in split["partitions"] if row["name"] == "test")
    if sha256_file(ROOT / partition["ids"]["path"]) != partition["ids"]["sha256"]:
        raise ValueError("TEST IDs changed")
    ids = read_rows(ROOT / partition["ids"]["path"])
    frame, target, source_ids, _, _ = load_tabular(dataset)
    positions = select_rows(source_ids, ids)
    x = view.adapter.transform(frame.iloc[positions])
    y = view.adapter.target(target.to_numpy()[positions]).reshape(-1, 1)
    return {
        "ids": ids,
        "x": x,
        "y": y,
        "target_original": target.to_numpy()[positions].astype(float),
        "view": view,
        "raw": frame.iloc[positions].reset_index(drop=True),
    }
