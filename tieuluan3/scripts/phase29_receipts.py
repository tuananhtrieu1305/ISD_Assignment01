"""Independent native CPU export receipts; CUDA hidden before framework import.

Only first four fixed TRAIN windows, no validation/TEST forwards or optimizer.
Run implementations sequentially after the training/coverage queue exits.
"""

import argparse
import os
from pathlib import Path

from src.ch04_rnn_lstm.phase29.protocol import BASE, IMPLEMENTATIONS, MODELS, check_sources, checked, ref
from src.common.contracts import read_json


def receipts(method):
    if method not in IMPLEMENTATIONS:
        raise ValueError("Unknown receipt implementation")
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[key] = "2"
    import numpy as np

    from src.ch02_ml.experiment import provenance
    from src.ch02_ml.protocol import array_sha256
    from src.ch04_rnn_lstm.export_r2 import compare_outputs, native_cpu
    from src.ch04_rnn_lstm.window_data import WindowData
    from src.common.artifact_core import ArtifactStore, write_once
    from src.common.numpy_engine import NumpyNetwork

    release = check_sources()
    active = read_json(BASE / "active_controller.json")
    if active.get("pid") is not None or active.get("status") != "finished":
        raise ValueError("Wait for training controller/coverage writer to exit")
    cache = {}
    count = 0
    for entry in release["runs"]:
        if entry["method"] != method:
            continue
        run = entry["run_id"]
        path = BASE / "cpu_receipts" / (run + ".json")
        selected_ref = ref(BASE / "runs" / run / "selection.json")
        selected = read_json(checked(selected_ref))
        if path.exists():
            old = read_json(path)
            for key in ("selection", "checkpoint", "checkpoint_metadata", "config", "writer_source"):
                checked(old[key])
            if old["status"] != "PASS" or old["selection"] != selected_ref:
                raise ValueError("Existing strict CPU receipt changed")
            count += 1
            continue
        key = (entry["dataset_id"], entry["fold"])
        if key not in cache:
            cache[key] = WindowData(*key)
        data = cache[key]
        config = read_json(checked(entry["config"]))
        weights = ArtifactStore(MODELS / run).load_checkpoint(
            "best",
            provenance(entry, config),
            expected_manifest_sha256=selected["checkpoint_metadata"]["sha256"],
        )
        x, _ = data.batch(data.train_ids[:4])
        portable = NumpyNetwork(config["plan"], weights).forward(x)
        native = native_cpu(config["plan"], weights, method, x)
        demo = read_json(checked(selected["cpu_demo"]))
        gpu = np.asarray(demo["comparisons"]["original_gpu_cpu_gate"]["output"], "float32")
        comparison = compare_outputs(portable, native, gpu)
        write_once(
            path,
            {
                "status": "PASS",
                "run_id": run,
                "selection": selected_ref,
                "checkpoint": selected["checkpoint"],
                "checkpoint_metadata": selected["checkpoint_metadata"],
                "config": entry["config"],
                "writer_source": ref(Path(__file__)),
                "input_split": "train",
                "ids": data.train_ids[:4],
                "canonical_x_sha256": array_sha256(x),
                "native_cpu_device": "cpu",
                "cuda_visible_devices": "-1",
                "portable_cpu_output": portable.tolist(),
                "comparisons": comparison,
                "optimizer_updates": 0,
                "validation_executed": False,
                "test_executed": False,
            },
        )
        count += 1
        print({"cpu_receipt": run, "status": "PASS"}, flush=True)
    if count != 36:
        raise ValueError("Expected 36 strict CPU receipts per implementation")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", required=True, choices=IMPLEMENTATIONS)
    receipts(parser.parse_args().method)
