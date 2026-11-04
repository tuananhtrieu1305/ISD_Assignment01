"""Presentation must never turn missing telemetry or one seed into a fake SD."""

from scripts.write_phase29_manuscript import fmt


def test_missing_number_is_not_zero_or_recovery_peak():
    assert fmt({"mean": None, "sample_std": None, "n": 0}) == "không xác định"


def test_sd_and_count_are_explicit_without_fabricating_single_run_sd():
    assert fmt({"mean": 2.0, "sample_std": 1.0, "n": 3}) == "2,000 ± 1,000"
    assert fmt({"mean": 2.0, "sample_std": None, "n": 1}) == "2,000 (n=1)"
    assert fmt({"mean": 2.0, "sample_std": 1.0, "n": 2}, show_n=True).endswith("(n=2)")
