"""Release packaging must pin supplemental report references, not change evaluation."""

import pytest

from scripts.release_phase31 import merge_references


def test_reference_union_keeps_report_bibliography():
    a = {"path": "artifacts/a.json", "sha256": "a" * 64}
    b = {"path": "report/references/ch06_sources_v3.bib", "sha256": "b" * 64}
    assert merge_references([a], [b, a]) == [a, b]


def test_conflicting_hash_fails_not_last_wins():
    with pytest.raises(ValueError):
        merge_references(
            [{"path": "artifacts/a.json", "sha256": "a" * 64}],
            [{"path": "artifacts/a.json", "sha256": "b" * 64}],
        )


def test_empty_release_rejected():
    with pytest.raises(ValueError):
        merge_references([], [])
