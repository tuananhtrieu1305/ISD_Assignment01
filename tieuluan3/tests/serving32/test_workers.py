"""Unit fixtures for process adapters; real GPU evidence is a separate HTTP probe."""

import io
import json
import sys
import types

import numpy as np
import pytest

from apps.api.v3 import native, worker
from apps.api.v3.inference import failure_job
from apps.api.v3.jobs import JobStore
from apps.api.v3.registry import Registry


@pytest.mark.parametrize("method", ["keras", "pytorch"])
def test_native_command_is_fixed_and_backend_label(tmp_path, monkeypatch, method):
    folder = tmp_path / (".venv-keras" if method == "keras" else ".venv-torch") / "bin"
    folder.mkdir(parents=True)
    (folder / "python").write_text("fixture", encoding="utf-8")
    monkeypatch.setenv("AI_NATIVE_RUNTIME", str(tmp_path))

    def fake_run(command, **kwargs):
        assert command[1:] == ["-m", "apps.api.v3.native"]
        assert kwargs["env"]["KERAS_BACKEND"] == "tensorflow"
        assert json.loads(kwargs["input"])["model_id"] == "fixture_model"
        return types.SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "raw": [[1]],
                    "inference_ms": 1,
                    "actual_backend": "tensorflow" if method == "keras" else "torch",
                    "actual_device": "cuda:0",
                }
            ),
        )

    monkeypatch.setattr(native.subprocess, "run", fake_run)
    raw, elapsed, backend, device = native.invoke_native(
        None, {"implementation": method, "model_id": "fixture_model"}, np.zeros((1, 2))
    )
    assert device == "cuda:0" and elapsed == 1 and raw[0, 0] == 1
    assert backend == ("tensorflow" if method == "keras" else "torch")


def test_native_no_silent_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_NATIVE_RUNTIME", str(tmp_path))
    spec = {"implementation": "pytorch", "model_id": "fixture_model"}
    with pytest.raises(RuntimeError):
        native.invoke_native(None, spec, np.zeros((1, 2)))
    folder = tmp_path / ".venv-torch/bin"
    folder.mkdir(parents=True)
    (folder / "python").write_text("fixture", encoding="utf-8")
    monkeypatch.setattr(
        native.subprocess, "run", lambda *a, **k: types.SimpleNamespace(returncode=1, stdout="")
    )
    with pytest.raises(RuntimeError):
        native.invoke_native(None, spec, np.zeros((1, 2)))
    monkeypatch.setattr(
        native.subprocess,
        "run",
        lambda *a, **k: types.SimpleNamespace(returncode=0, stdout='{"actual_device":"cpu"}'),
    )
    with pytest.raises(RuntimeError):
        native.invoke_native(None, spec, np.zeros((1, 2)))

    def timeout(*a, **k):
        raise native.subprocess.TimeoutExpired("fixture", 1)

    monkeypatch.setattr(native.subprocess, "run", timeout)
    with pytest.raises(RuntimeError):
        native.invoke_native(None, spec, np.zeros((1, 2)))


@pytest.mark.parametrize("method", ["keras", "pytorch"])
def test_native_main_protocol_with_injected_backend(monkeypatch, capsys, method):
    from apps.api.v3 import inference
    from src.common import backend_models

    registry = Registry()
    identity = next(
        m["model_id"]
        for m in registry.models.values()
        if m["family"] == "mlp" and m["implementation"] == method
    )
    spec = registry.models[identity]
    config = inference.load_model(registry, spec)[0]
    x = np.zeros((1, *config["plan"]["input_shape"]), dtype="float32")

    class FakeBackend:
        def __init__(self, plan, weights, device):
            assert device == "gpu"

        def predict(self, x):
            return np.zeros((1, 1), dtype="float32")

    monkeypatch.setattr(backend_models, "TorchBackend", FakeBackend)
    monkeypatch.setattr(backend_models, "KerasBackend", FakeBackend)
    monkeypatch.setitem(
        sys.modules,
        "keras",
        types.SimpleNamespace(backend=types.SimpleNamespace(backend=lambda: "tensorflow")),
    )
    monkeypatch.setitem(
        sys.modules,
        "tensorflow",
        types.SimpleNamespace(
            config=types.SimpleNamespace(
                set_soft_device_placement=lambda _: None,
                list_physical_devices=lambda _: [],
                experimental=types.SimpleNamespace(set_memory_growth=lambda *a: None),
            )
        ),
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"model_id": identity, "x": x.tolist()})))
    native.main()
    output = json.loads(capsys.readouterr().out)
    assert output["actual_device"] == "cuda:0"
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"model_id": identity, "x": [[0]]})))
    with pytest.raises(ValueError):
        native.main()


def test_worker_persists_failure_and_missing_job(tmp_path, monkeypatch):
    registry = Registry()
    request = registry.json(registry.document["samples"])["ch2_cdc_diabetes"]["request"]
    store = JobStore(tmp_path / "jobs.db")
    row = store.create(request, "worker_key", "owner")
    store.claim()

    def broken(*args):
        raise ValueError("synthetic worker failure")

    monkeypatch.setattr(worker, "compare", broken)
    worker.run(store.path, row["job_id"], "cpu")
    assert store.get(row["job_id"], "owner")["status"] == "failed"
    assert (
        store.extras(row["job_id"], "owner")["serving_runtime"]["historical_test_evaluation_executed"]
        is False
    )
    worker.run(store.path, "missing", "cpu")


def test_worker_success_protocol(tmp_path, monkeypatch):
    registry = Registry()
    request = registry.json(registry.document["samples"])["ch2_cdc_diabetes"]["request"]
    store = JobStore(tmp_path / "jobs.db")
    row = store.create(request, "worker_key", "owner")
    store.claim()
    monkeypatch.setattr(
        worker, "compare", lambda *a: (failure_job(request, "fixture_unavailable"), {"fixture": True})
    )
    worker.run(store.path, row["job_id"], "cpu")
    assert store.extras(row["job_id"], "owner")["fixture"] is True
