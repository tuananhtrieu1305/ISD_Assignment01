"""End-to-end offline core journey, not a real-data experiment/UI test."""

import ast

import numpy as np
import pytest

from src.common.artifact_core import ArtifactStore, sha256_file
from src.common.backend_models import TorchBackend
from src.common.contracts import ROOT, canonical_sha256
from src.common.model_core import (
    ModelRegistry,
    build_plan,
    canonical_weights,
    make_contract,
    render_functions,
)
from src.common.numpy_engine import NumpyNetwork
from src.common.training_core import Adam, EarlyStopping, clip_gradients


@pytest.mark.parametrize(
    "family,shape", [("mlp", [2]), ("cnn", [8, 8, 3]), ("rnn", [3, 2]), ("lstm", [3, 2])]
)
def test_synthetic_train_checkpoint_restore_explain_compare(tmp_path, family, shape):
    plan = build_plan(family, shape, 1, tiny=True)
    weights = canonical_weights(plan, 42)
    contract = make_contract(plan, "scratch", "synthetic_fixture")
    registry = ModelRegistry()
    registry.register(contract)
    network = NumpyNetwork(plan, weights)
    optimizer = Adam(network.weights)
    stop = EarlyStopping()
    rng = np.random.default_rng(73)
    x = rng.normal(size=(2, *shape)).astype("float32")
    y = np.ones((2, 1), dtype="float32")
    for epoch in range(3):
        loss, grad, _ = network.loss_gradients(x, y, "mse")
        grad, _ = clip_gradients(grad)
        optimizer.step(network.weights, grad)
        stop.observe(loss, epoch)
    store = ArtifactStore(tmp_path)
    provenance = {
        key: canonical_sha256({"synthetic_fixture": True, "name": key, "plan": plan})
        for key in store.PROVENANCE_KEYS
    }
    provenance["model_contract_sha256"] = canonical_sha256(contract)
    store.save_checkpoint("synthetic", network.weights, provenance)
    restored = store.load_checkpoint(
        "synthetic", provenance, expected_manifest_sha256=sha256_file(tmp_path / "synthetic.json")
    )
    clone = NumpyNetwork(plan, restored)
    np.testing.assert_array_equal(clone.forward(x), network.forward(x))
    torch = TorchBackend(plan, restored, "cpu")
    np.testing.assert_allclose(torch.predict(x), network.forward(x), rtol=1e-4, atol=1e-5)
    assert render_functions(registry.get(contract["model_id"]))["plain"].startswith("đầu vào")


def test_scratch_has_no_autograd_or_framework_import():
    tree = ast.parse((ROOT / "src/common/numpy_engine.py").read_text())
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    assert not any(name.startswith(("torch", "keras", "tensorflow", "jax", "autograd")) for name in names)
