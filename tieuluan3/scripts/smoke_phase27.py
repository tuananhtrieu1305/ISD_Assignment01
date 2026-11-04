"""CPU/API TRAIN demo and separately measured model-resolution PNG preprocessing."""

import json
import sys

from scripts.demo_phase27 import decode_request, infer, sample_request
from src.ch03_cnn.protocol import BASE, DATASETS
from src.common.artifact_core import write_once
from src.common.training_core import inference_timing


def main():
    path = BASE / "cpu_smoke.json"
    if path.exists():
        print(json.dumps({"status": "PASS", "mode": "already_recorded_read_only"}))
        return
    cases = []
    for dataset in DATASETS:
        request, key = sample_request(dataset)
        timing = inference_timing(lambda: decode_request(request))  # noqa: B023
        output = infer(request, seed=42)
        if not output["comparison_valid"] or len(output["results"]) != 3:
            raise ValueError("Incomplete CPU comparison")
        cases.append(
            {
                "dataset_id": dataset,
                "input_split": "train",
                "sample_id": key,
                "models_loaded": 3,
                "serving_backend": "numpy_cpu_portable",
                "preprocessing_scope": "preloaded base64 PNG at MODEL resolution to RGB decode, resize/rescale and frozen contract lookup/hash checks; excludes image-file/network I/O, includes contract metadata I/O; not full-resolution IDRiD cost",
                "preprocessing_timing": timing,
                "job": output,
            }
        )
    if any(name in sys.modules for name in ("torch", "tensorflow", "keras")):
        raise RuntimeError("CPU smoke imported native GPU framework")
    write_once(
        path,
        {"status": "PASS", "cases": cases, "test_data_accessed": False, "test_model_forward_executed": False},
    )
    print(json.dumps({"status": "PASS", "datasets": 3, "models_loaded": 9, "test_executed": False}))


if __name__ == "__main__":
    main()
