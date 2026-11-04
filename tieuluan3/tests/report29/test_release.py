"""A release cannot skip a figure or treat a duplicate QA row as extra coverage."""

import pytest

from scripts.release_phase29 import validate_qa


def test_qa_requires_exact_png_set_and_pass():
    statistics = {
        "figures": [{"path": "artifacts/figures/phase29/a.png"}, {"path": "artifacts/figures/phase29/a.svg"}]
    }
    validate_qa(statistics, {"status": "PASS", "reviewed_png_names": ["a.png"]})
    for qa in (
        {"status": "PENDING", "reviewed_png_names": ["a.png"]},
        {"status": "PASS", "reviewed_png_names": []},
        {"status": "PASS", "reviewed_png_names": ["a.png", "a.png"]},
    ):
        with pytest.raises(ValueError):
            validate_qa(statistics, qa)
