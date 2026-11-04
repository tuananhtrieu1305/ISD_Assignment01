"""Saved-output audit only: no native model and no fresh TEST prediction."""

from types import SimpleNamespace

import numpy as np
import pytest

from scripts.verify_phase29_test import audit_saved_rows
from src.common.metric_core import regression_metrics


@pytest.fixture
def saved():
    target = np.asarray([[2.0, 3.0], [4.0, 5.0]], "float64")
    prediction = target + 0.25
    rows = [
        {
            "id": k,
            "series": "S",
            "target_times": ["2000-01-01", "2000-02-01"],
            "target": y.tolist(),
            "prediction": p.tolist(),
        }
        for k, y, p in zip(("a", "b"), target, prediction, strict=True)
    ]
    cache = SimpleNamespace(
        ids=["a", "b"],
        rows={r["id"]: r for r in rows},
        horizons=[1, 2],
        targets=lambda ids: target,
        series=lambda ids: ["S", "S"],
    )
    metrics = regression_metrics(target, prediction, cache.horizons, ["S", "S"])
    return cache, rows, metrics


def test_saved_prediction_audit_recomputes_metrics_without_forward(saved):
    assert audit_saved_rows(*saved) == 2


@pytest.mark.parametrize("change", ["ids", "target", "calendar", "prediction", "metrics"])
def test_saved_prediction_audit_rejects_changed_identity_labels_or_quality(saved, change):
    cache, rows, metrics = saved
    if change == "ids":
        rows.reverse()
    elif change == "target":
        rows[0]["target"][0] += 1
    elif change == "calendar":
        rows[0] = {**rows[0], "target_times": ["1999-01-01", "2000-02-01"]}
    elif change == "prediction":
        rows[0]["prediction"][0] += 1
    else:
        metrics = {**metrics, "rmse": 123.0}
    with pytest.raises(ValueError):
        audit_saved_rows(cache, rows, metrics)
