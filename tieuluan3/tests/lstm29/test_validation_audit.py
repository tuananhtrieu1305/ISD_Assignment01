"""History and numeric audit rules use synthetic scalar losses, never TEST."""

import copy

import pytest

from scripts.verify_phase29_validation import audit_history
from src.common.contracts import canonical_sha256
from src.common.training_core import batch_order


def history():
    return [
        {
            "epoch": i,
            "validation_loss": loss,
            "train_loss": 0.5,
            "gradient_norm_max": 2.0,
            "gradient_norm_mean": 1.0,
            "gradient_clip_fraction": 0.25,
            "batch_order_sha256": canonical_sha256(batch_order(4, 2, 17, i)),
        }
        for i, loss in enumerate([0.4, 0.2, 0.3, 0.4])
    ]


def test_history_requires_true_minimum_common_schedule_and_stopping_budget():
    budget = {"batch_size": 2, "max_epochs": 40, "patience": 2, "min_delta": 1e-5}
    assert audit_history(history(), 1, 17, 4, budget)["optimizer_steps"] == 8
    with pytest.raises(ValueError):
        audit_history(history(), 2, 17, 4, budget)
    with pytest.raises(ValueError):
        audit_history(history()[:3], 1, 17, 4, budget)


@pytest.mark.parametrize("fault", ["empty", "nan", "order", "clip", "epoch", "too_many"])
def test_bad_histories_fail(fault):
    rows = copy.deepcopy(history())
    budget = {"batch_size": 2, "max_epochs": 40, "patience": 2, "min_delta": 1e-5}
    if fault == "empty":
        rows = []
    elif fault == "nan":
        rows[0]["validation_loss"] = float("nan")
    elif fault == "order":
        rows[0]["batch_order_sha256"] = "0" * 64
    elif fault == "clip":
        rows[0]["gradient_clip_fraction"] = 1.2
    elif fault == "epoch":
        rows[0]["epoch"] = 9
    else:
        budget["max_epochs"] = 3
    with pytest.raises(ValueError):
        audit_history(rows, 1, 17, 4, budget)
