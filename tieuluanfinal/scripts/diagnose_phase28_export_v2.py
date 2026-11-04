"""Isolate fused-cuDNN numerical drift, using fixed TRAIN inputs only."""

import os

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "2"
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import json

import numpy as np

from src.ch02_ml.experiment import configure, provenance
from src.ch04_rnn_lstm.protocol import BASE, MODELS, check_sources, checked, ref
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.artifact_core import ArtifactStore, write_once
from src.common.backend_models import TorchBackend
from src.common.contracts import read_json
from src.common.numpy_engine import NumpyNetwork


def main():
    if read_json(BASE / "active_controller.json").get("pid") is not None:
        raise ValueError("Stop the controller before a numerical probe")
    run = "ch4_household_power_rnn_pytorch_s17_main"
    entry = next(e for e in check_sources()["runs"] if e["run_id"] == run)
    config = read_json(checked(entry["config"]))
    metadata = ref(MODELS / run / "best.json")
    weights = ArtifactStore(MODELS / run).load_checkpoint("best", provenance(entry, config), expected_manifest_sha256=metadata["sha256"])
    configure("pytorch", 17)
    data = WindowData(entry["dataset_id"])
    x, _ = data.batch(data.train_ids[:4])
    portable = NumpyNetwork(config["plan"], weights).forward(x)
    gpu = TorchBackend(config["plan"], weights, "gpu")
    fused = gpu.predict(x)
    previous = gpu.torch.backends.cudnn.enabled
    try:
        gpu.torch.backends.cudnn.enabled = False
        unfused = gpu.predict(x)
    finally:
        gpu.torch.backends.cudnn.enabled = previous
    cpu = TorchBackend(config["plan"], weights, "cpu").predict(x)

    def compare(value):
        return {"strict_pass": bool(np.isclose(portable, value, rtol=1e-4, atol=1e-5).all()), "max_abs_error": float(np.max(np.abs(portable - value))), "output": value.tolist()}

    result = {"status": "DIAGNOSTIC_ONLY", "run_id": run, "input_split": "train", "ids": data.train_ids[:4], "checkpoint": ref(MODELS / run / "best.npz"), "numpy_cpu_float32": portable.tolist(), "gpu_fused": compare(fused), "gpu_unfused": compare(unfused), "native_cpu": compare(cpu), "rtol": 1e-4, "atol": 1e-5, "weights_updated": False, "test_executed": False, "validation_executed": False}
    write_once(BASE / "attempts/export_numeric_probe_v2.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
