"""Saved-output aggregates, explicit denominators and publication metadata."""

import pytest

from scripts.build_phase31 import aggregate, check_summary, markdown_table


def sample(value=1, numeric=None):
    return {
        "domain": "gold",
        "split": "test",
        "category": "numeric",
        "variant": "A0",
        "stratum": "benign",
        "metrics": {
            "task_success": value,
            "numeric_parity": numeric,
            "routing_accuracy": None,
            "latency_ms": 10,
            "message_count": 1,
            "tool_calls": 1,
            "peak_child_rss_bytes": 1024,
            "citation_correctness": 1,
            "answer_completion": 1,
            "unsafe_claim": 0,
            "unsupported_claim": 0,
            "refusal_correctness": None,
        },
    }


def test_aggregate_preserves_undefined_denominator():
    rows = aggregate([sample(), sample(0)])
    group = next(r for r in rows if r["scope"] == "numeric")
    assert group["task_success"] == 0.5 and group["task_success_n"] == 2
    assert group["numeric_parity"] is None and group["numeric_parity_n"] == 0
    assert group["routing_accuracy"] is None
    assert group["latency_p95_ms"] == 10


def test_numeric_aggregate_not_zero_filled():
    rows = aggregate([sample(numeric=1), sample(numeric=None)])
    assert rows[0]["numeric_parity"] == 1 and rows[0]["numeric_parity_n"] == 1


def test_markdown_escapes_newline_and_pipes():
    value = markdown_table(["a", "b"], [["x|y", "line\nnext"]])
    assert "x\\|y" in value and "line next" in value


@pytest.mark.parametrize("rows", [[], [sample()], [sample()] * 900])
def test_reject_incomplete_or_duplicate_release_matrix(rows):
    with pytest.raises(ValueError):
        check_summary(rows)
