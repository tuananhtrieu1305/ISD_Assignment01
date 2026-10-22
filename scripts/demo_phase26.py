"""CPU-only Chapter2 demo over fixed TRAIN samples; never opens TEST."""

import argparse
import json

import numpy as np

from src.ch02_ml.baselines import PortableBaseline
from src.ch02_ml.experiment import metrics_for, provenance
from src.ch02_ml.protocol import BASE, CACHE, DATASETS, IMPLEMENTATIONS, MODELS, check_sources
from src.ch02_ml.workflow import checked_reference
from src.common.artifact_core import ArtifactStore
from src.common.contracts import read_json
from src.common.data_access import DatasetView
from src.common.numpy_engine import NumpyNetwork


def demo(dataset, seed=42):
    release = check_sources()
    view = DatasetView(dataset)
    samples = read_json(BASE / "data" / (dataset + "_demo.json"))
    with np.load(CACHE / f"{dataset}_development.npz", allow_pickle=False) as data:
        x = data["train_x"][:4].copy()
    rows = []
    for entry in release["runs"]:
        if entry["dataset_id"] != dataset or entry["seed"] != seed:
            continue
        selected = read_json(BASE / "runs" / entry["run_id"] / "selection.json")
        config = read_json(checked_reference(entry["config"]))
        weights = ArtifactStore(MODELS / entry["run_id"]).load_checkpoint(
            "best",
            provenance(entry, config),
            expected_manifest_sha256=selected["checkpoint_metadata"]["sha256"],
        )
        if entry["method"] in IMPLEMENTATIONS:
            raw = NumpyNetwork(config["plan"], weights).forward(x)
        else:
            raw = PortableBaseline(
                read_json(checked_reference(selected["classical_metadata"])), weights
            ).predict(x)
        _, predictions, _ = metrics_for(
            np.asarray(samples["known_outputs"]), raw, config["task"], view.adapter
        )
        rows.append(
            {
                "run_id": entry["run_id"],
                "trained_implementation": entry["method"],
                "inference_backend": "numpy_cpu_portable",
                "prediction": predictions.tolist(),
                "checkpoint": selected["checkpoint"],
            }
        )
    return {
        "dataset_id": dataset,
        "seed": seed,
        "input_split": "train",
        "ids": samples["ids"],
        "known_outputs": samples["known_outputs"],
        "models": rows,
        "warning": "Academic demonstration, not clinical diagnosis or current market appraisal.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=DATASETS, required=True)
    parser.add_argument("--seed", choices=[17, 42, 73], type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(demo(args.dataset, args.seed), ensure_ascii=False, indent=2))
