"""Forensic read-only TRAIN-only CPU export comparison; no training or TEST."""

import os

for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[name] = "2"
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import json

import numpy as np

from src.ch02_ml.experiment import configure, provenance
from src.ch04_rnn_lstm.experiment import load_progress
from src.ch04_rnn_lstm.protocol import BASE, MODELS, check_sources, checked, ref
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.artifact_core import ArtifactStore, write_once
from src.common.backend_models import TorchBackend
from src.common.contracts import read_json
from src.common.numpy_engine import NumpyNetwork


def main():
    active = read_json(BASE / "active_controller.json")
    if active.get("pid") is not None:
        raise ValueError("Do not run a GPU probe beside the active controller")
    release = check_sources()
    run = "ch4_household_power_rnn_pytorch_s17_main"
    entry = next(e for e in release["runs"] if e["run_id"] == run)
    config = read_json(checked(entry["config"]))
    state = load_progress(run, entry["config"]["sha256"])
    metadata = ref(MODELS / run / "best.json")
    weights = ArtifactStore(MODELS / run).load_checkpoint("best", provenance(entry, config), expected_manifest_sha256=metadata["sha256"])
    if any(not np.array_equal(weights[k], state["best_weights"][k]) for k in weights):
        raise ValueError("Exported checkpoint differs from selected immutable optimizer snapshot")
    configure("pytorch", 17)
    data = WindowData(entry["dataset_id"])
    x, _ = data.batch(data.train_ids[:4])
    gpu = TorchBackend(config["plan"], weights, "gpu")
    expected = gpu.predict(x)
    cpu = TorchBackend(config["plan"], weights, "cpu")
    values = {
        "numpy_float32": NumpyNetwork(config["plan"], weights).forward(x),
        "numpy_float64": NumpyNetwork(config["plan"], {k: v.astype("float64") for k, v in weights.items()}).forward(x.astype("float64")),
        "torch_cpu_float32": cpu.predict(x),
    }
    cpu.ops.double()
    with cpu.torch.no_grad():
        values["torch_cpu_float64"] = cpu.forward(cpu.torch.as_tensor(x.astype("float64"))).cpu().numpy()
    comparisons = {}
    for name, value in values.items():
        good = np.isclose(value, expected, rtol=1e-4, atol=1e-5)
        comparisons[name] = {"strict_forward_pass": bool(good.all()), "failures": int((~good).sum()), "max_abs_error": float(np.max(np.abs(value - expected))), "output": value.tolist()}
    result = {"status": "DIAGNOSTIC_ONLY", "run_id": run, "input_split": "train", "ids": data.train_ids[:4], "checkpoint": ref(MODELS / run / "best.npz"), "checkpoint_metadata": metadata, "immutable_progress": read_json(MODELS / run / "progress.json"), "best_epoch": state["early_stopping"]["best_epoch"], "completed_epochs": len(state["history"]), "native_gpu_float32": expected.tolist(), "comparisons": comparisons, "weights_equal_saved_best": True, "weights_updated": False, "test_executed": False, "validation_executed": False, "source_changed": False}
    write_once(BASE / "attempts/export_numeric_probe_v1.json", result)
    print(json.dumps({key: value for key, value in result.items() if key not in {"native_gpu_float32"}}, indent=2))


if __name__ == "__main__":
    main()
