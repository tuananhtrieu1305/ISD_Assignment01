"""Phase29 presentation statistics preserve family/split and missing telemetry."""

import pytest

from scripts.summarize_phase29 import aggregate_rows, paired_deltas


def fixture():
    return [
        {
            "dataset_id": "ch4_gold_pink_sheet",
            "family": family,
            "method": "pytorch",
            "fold": None,
            "split": "test",
            "seed": seed,
            "rmse": value,
            "train_seconds": None if family == "rnn" and seed == 17 else float(seed),
        }
        for family, values in (("rnn", (2.0, 4.0, 6.0)), ("lstm", (1.0, 3.0, 5.0)))
        for seed, value in zip((17, 42, 73), values, strict=True)
    ]


def test_aggregation_keeps_family_split_and_null_cost_count():
    rows = fixture()
    rows += [{**r, "split": "validation", "rmse": 100.0} for r in rows.copy()]
    result = aggregate_rows(rows, fields=("rmse", "train_seconds"))
    selected = [r for r in result if r["family"] == "rnn" and r["split"] == "test"]
    quality = next(r for r in selected if r["metric"] == "rmse")
    cost = next(r for r in selected if r["metric"] == "train_seconds")
    assert quality["mean"] == 4.0 and quality["sample_std"] == 2.0 and quality["n"] == 3
    assert cost["n"] == 2 and cost["mean"] == 57.5


@pytest.mark.parametrize("fault", ["missing", "duplicate"])
def test_aggregation_rejects_incomplete_or_duplicate_seed(fault):
    rows = fixture()
    rows = rows[:-1] if fault == "missing" else rows + [rows[0]]
    with pytest.raises(ValueError):
        aggregate_rows(rows, fields=("rmse",))


def test_paired_delta_is_by_seed_and_does_not_select_a_winning_seed():
    result = paired_deltas(fixture())
    assert len(result) == 1 and result[0]["n"] == 3
    assert result[0]["rnn_minus_lstm_mean"] == 1.0
    assert result[0]["sample_std"] == 0.0
    assert result[0]["relative_improvement_percent"] == pytest.approx(100 / 4)
