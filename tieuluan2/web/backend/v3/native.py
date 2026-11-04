"""Sequential native GPU subprocesses in the two existing locked environments."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from src.common.contracts import ROOT


def invoke_native(registry, spec, x):
    runtime = Path(
        os.environ.get("AI_NATIVE_RUNTIME", str(Path.home() / ".local/share/ai-term-paper-v3"))
    ).resolve()
    env_name = "keras" if spec["implementation"] == "keras" else "torch"
    python = runtime / f".venv-{env_name}/bin/python"
    if not python.is_file():
        raise RuntimeError("Locked native environment unavailable")
    env = {
        **os.environ,
        "KERAS_BACKEND": "tensorflow",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "TF_NUM_INTEROP_THREADS": "1",
        "TF_NUM_INTRAOP_THREADS": "1",
        "TF_CPP_MIN_LOG_LEVEL": "3",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if env_name == "keras":
        libraries = sorted((runtime / ".venv-keras/lib/python3.11/site-packages/nvidia").glob("*/lib"))
        env["LD_LIBRARY_PATH"] = ":".join(str(p) for p in libraries) + ":/usr/lib/wsl/lib"
    payload = json.dumps({"model_id": spec["model_id"], "x": x.tolist()}, allow_nan=False)
    # The command/module are fixed; HTTP data only enters bounded stdin JSON.
    try:
        child = subprocess.run(
            [str(python), "-m", "apps.api.v3.native"],
            input=payload,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
    except subprocess.SubprocessError as error:
        raise RuntimeError("Native worker deadline; no fallback") from error
    if child.returncode or len(child.stdout) > 1_000_000:
        raise RuntimeError("Native GPU worker failed; no fallback")
    document = json.loads(child.stdout)
    if document["actual_device"] != "cuda:0":
        raise RuntimeError("Native worker did not use GPU")
    return (
        np.asarray(document["raw"], dtype="float32"),
        document["inference_ms"],
        document["actual_backend"],
        document["actual_device"],
    )


def main():
    from apps.api.v3.inference import load_model
    from apps.api.v3.registry import Registry
    from src.common.backend_models import KerasBackend, TorchBackend

    payload = sys.stdin.read(2_000_001)
    if len(payload) > 2_000_000:
        raise ValueError("Native stdin budget")
    request = json.loads(payload)
    registry = Registry()
    spec = registry.models[request["model_id"]]
    config, _, _, weights = load_model(registry, spec)
    x = np.asarray(request["x"], dtype="float32")
    if list(x.shape) != [1, *config["plan"]["input_shape"]] or not np.isfinite(x).all():
        raise ValueError("Native input shape")
    if spec["implementation"] == "keras":
        import keras
        import tensorflow as tf

        if keras.backend.backend() != "tensorflow":
            raise RuntimeError("No Keras backend fallback")
        tf.config.set_soft_device_placement(False)
        for gpu in tf.config.list_physical_devices("GPU"):
            tf.config.experimental.set_memory_growth(gpu, True)
        model, backend = KerasBackend(config["plan"], weights, "gpu"), "tensorflow"
    elif spec["implementation"] == "pytorch":
        model, backend = TorchBackend(config["plan"], weights, "gpu"), "torch"
    else:
        raise ValueError("Scratch is NumPy CPU only")
    start = time.perf_counter()
    raw = model.predict(x)
    elapsed = (time.perf_counter() - start) * 1000
    print(
        json.dumps(
            {
                "raw": raw.tolist(),
                "inference_ms": elapsed,
                "actual_backend": backend,
                "actual_device": "cuda:0",
            },
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
