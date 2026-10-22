"""Synthetic end-to-end persistence and metrics; no real TEST values are opened."""

import numpy as np
import pytest

from src.ch02_ml import experiment
from src.ch02_ml.training import ScratchTrainer, fit
from src.common.artifact_core import ArtifactStore
from src.common.model_core import build_plan, canonical_weights
from src.common.numpy_engine import NumpyNetwork


def test_progress_and_safe_checkpoint_e2e(tmp_path, monkeypatch):
    monkeypatch.setattr(experiment, "MODELS", tmp_path)
    monkeypatch.setattr(experiment, "ROOT", tmp_path)
    monkeypatch.setattr(experiment, "PREDICTIONS", tmp_path / "predictions")
    monkeypatch.setattr(
        experiment,
        "ref",
        lambda path: {"path": path.relative_to(tmp_path).as_posix(), "sha256": experiment.sha256_file(path)},
    )
    rng = np.random.default_rng(42)
    x = rng.normal(size=(16, 2)).astype("float32")
    y = x[:, :1]
    plan = build_plan("mlp", [2], 1, tiny=True)
    trainer = ScratchTrainer(plan, canonical_weights(plan, 17))
    result = fit(
        trainer,
        x,
        y,
        x,
        y,
        "mse",
        seed=17,
        budget={
            "patience": 3,
            "min_delta": 1e-5,
            "max_epochs": 2,
            "batch_size": 8,
            "wall_time_limit_minutes": 1,
        },
        progress=lambda state: experiment.save_progress("synthetic", state, "a" * 64),
    )
    state = experiment.load_progress("synthetic", "a" * 64)
    assert state["trainer"]["iterations"] == 4
    assert experiment.load_progress("absent", "a" * 64) is None
    with pytest.raises(ValueError):
        experiment.load_progress("synthetic", "b" * 64)
    provenance = {key: "a" * 64 for key in ArtifactStore.PROVENANCE_KEYS}
    store = ArtifactStore(tmp_path / "safe")
    store.save_checkpoint("best", result["weights"], provenance)
    loaded = store.load_checkpoint("best", provenance)
    np.testing.assert_array_equal(trainer.predict(x), NumpyNetwork(plan, loaded).forward(x))
    row = experiment.save_predictions(
        "synthetic", "validation", [str(i) for i in range(16)], y.ravel(), trainer.predict(x)
    )
    assert row["sha256"]
    with pytest.raises(ValueError):
        experiment.save_predictions("synthetic", "validation", [], [], [])


def test_original_unit_metrics_and_diagnostics():
    class Adapter:
        def inverse_target(self, value):
            return value * 10000 + 200000

    metrics, pred, diagnostic = experiment.metrics_for(
        np.array([200000.0, 220000.0]), np.array([[0.0], [1.0]]), "mse", Adapter()
    )
    assert metrics["mae"]["value"] == 5000
    assert diagnostic is None and pred.shape == (2, 1)
    binary, probs, diagnostic = experiment.metrics_for(
        np.array([0, 1]), np.array([[-2.0], [2.0]]), "binary", None
    )
    assert probs.shape == (2, 2)
    assert binary["accuracy"]["value"] == 1 and diagnostic["brier"] < 0.1
    assert "recall_class_1" in {row["name"] for row in experiment.metric_rows(binary, "binary")}
