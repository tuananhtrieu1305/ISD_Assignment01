"""Phase29 validation-only declaration; Phase29 is the only joint TEST owner."""

from pathlib import Path

from src.ch04_rnn_lstm.protocol import SOURCE_FILES as PREVIOUS_FILES
from src.common.artifact_core import code_fingerprint, sha256_file
from src.common.contracts import PROTOCOL, ROOT, read_json

BASE = ROOT / "artifacts/manifests/phase29"
MODELS = ROOT / "artifacts/models/v3/ch04_lstm"
METRICS = ROOT / "artifacts/metrics/phase29"
PREDICTIONS = ROOT / "artifacts/predictions/phase29"
DATASETS = ("ch4_gold_pink_sheet", "ch4_bis_house_prices", "ch4_household_power")
SEEDS = (17, 42, 73)
IMPLEMENTATIONS = ("scratch", "keras", "pytorch")
FOLDS = (None, 1, 2, 3)
SOURCE_FILES = sorted(
    set(
        PREVIOUS_FILES
        + [
            "src/ch04_rnn_lstm/export_r2.py",
            *[
                f"src/ch04_rnn_lstm/phase29/{name}.py"
                for name in ("__init__", "protocol", "training", "diagnostics", "experiment", "joint_gate")
            ],
            *[
                f"scripts/{name}.py"
                for name in ("prepare_phase29", "phase29_controller", "phase29_worker", "phase29_preflight")
            ],
            "experiments/configs/v3/phase29_coverage.ini",
            "tests/lstm29/test_lstm_core.py",
            "tests/lstm29/test_experiment.py",
            "tests/lstm29/test_protocol.py",
            "tests/lstm29/test_joint_gate.py",
            "docs/phase29_operations.md",
        ]
    )
)


def ref(path):
    return {"path": Path(path).relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}


def label(fold):
    return "main" if fold is None else f"fold{fold}"


def run_id(dataset, method, seed, fold):
    return f"{dataset}_{'lstm_' if method in IMPLEMENTATIONS else ''}{method}_s{seed}_{label(fold)}"


def code_info():
    import subprocess

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    return {"git_commit": head, "dirty_tree_sha256": code_fingerprint(ROOT, SOURCE_FILES)}


def checked(record):
    path = (ROOT / record["path"]).resolve()
    if not path.is_relative_to(ROOT.resolve()) or ref(path) != record:
        raise ValueError("Approved artifact is missing, changed or escaping workspace")
    return path


def check_sources():
    release = read_json(BASE / "release.json")
    if (
        release["code"] != code_info()
        or release["protocol"] != ref(PROTOCOL)
        or release["environment"] != ref(ROOT / "uv.lock")
    ):
        raise ValueError("Declared recurrent source/protocol/environment changed; revision required")
    for record in release["source_files"]:
        checked(record)
    for entry in release["runs"]:
        for key in ("config", "model_contract"):
            checked(entry[key])
    return release
