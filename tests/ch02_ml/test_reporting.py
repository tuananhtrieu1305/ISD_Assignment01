import pytest

from scripts.summarize_phase26 import aggregate


def test_seed_summary_uses_sample_sd_and_ignores_null():
    base = {"dataset_id": "synthetic", "method": "synthetic", "split": "validation"}
    summary = aggregate([{**base, "quality_score": value, "quality_undefined": None} for value in (1, 2, 3)])
    assert len(summary) == 1
    assert summary[0]["n"] == 3
    assert summary[0]["mean"] == 2
    assert summary[0]["sample_std"] == pytest.approx(1)
