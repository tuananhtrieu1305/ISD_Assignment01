"""TRAIN-only CPU serving smoke and separately measured frozen preprocessing."""

import csv
import json

import numpy as np
import pandas as pd

from scripts.demo_phase26 import demo
from src.ch02_ml.protocol import BASE, DATASETS, METRICS, array_sha256, cache_data, ref
from src.ch02_ml.test_gate import atomic_json
from src.common.contracts import read_json
from src.common.data_access import DatasetView
from src.common.training_core import inference_timing


def main():
    results = []
    timings = []
    for dataset in DATASETS:
        arrays = cache_data(dataset)  # Verify cache hash, no TEST view or fit.
        source = read_json(BASE / "data" / (dataset + "_demo.json"))
        view = DatasetView(dataset)
        frame = pd.DataFrame(source["input_features"])
        x = view.adapter.transform(frame)
        np.testing.assert_array_equal(x, arrays["train_x"][:4])
        assert array_sha256(x) == source["canonical_x_sha256"]
        # Consumed synchronously in this iteration; no closure escapes the loop.
        measured = inference_timing(lambda: view.adapter.transform(frame.iloc[:1]))  # noqa: B023
        result = demo(dataset, 42)
        assert len(result["models"]) == 6 and result["input_split"] == "train"
        results.append({"dataset_id": dataset, "models": 6, "samples": 4, "status": "PASS", "output": result})
        timings.append(
            {
                "dataset_id": dataset,
                "device": "cpu",
                "input_split": "train",
                "batch_size": 1,
                "scope": "preloaded raw record to canonical float32 vector; no file load or target inverse; no refit",
                "preprocessing_p50_ms": measured["inference_p50_ms"],
                "preprocessing_p95_ms": measured["inference_p95_ms"],
                "warmup": 5,
                "repeats": 30,
            }
        )
    path = METRICS / "tables/preprocessing.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, list(timings[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(timings)
    atomic_json(
        BASE / "cpu_smoke.json",
        {
            "status": "PASS",
            "cases": results,
            "preprocessing": timings,
            "preprocessing_table": ref(path),
            "test_data_accessed": False,
            "test_model_forward_executed": False,
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "datasets": 3,
                "models_loaded": 18,
                "input_split": "train",
                "preprocessing": timings,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
