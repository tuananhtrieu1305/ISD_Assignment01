"""Outer filename normalization must never bless different dataset bytes."""

import pytest

from scripts.update_phase23_idrid import check_rename_evidence
from src.common.acquisition import AcquisitionError


def test_outer_rename_preserves_exact_bytes():
    original = [{"path": "old name.zip", "size_bytes": 10, "sha256": "a" * 64}]
    current = [{**original[0], "path": "canonical.zip"}]
    check_rename_evidence(original, current)


@pytest.mark.parametrize("field,value", [("sha256", "b" * 64), ("size_bytes", 11)])
def test_outer_rename_rejects_changed_bytes(field, value):
    original = [{"path": "old name.zip", "size_bytes": 10, "sha256": "a" * 64}]
    current = [{**original[0], "path": "canonical.zip", field: value}]
    with pytest.raises(AcquisitionError):
        check_rename_evidence(original, current)


def test_outer_rename_rejects_extra_files():
    with pytest.raises(AcquisitionError):
        check_rename_evidence([], [{"path": "canonical.zip", "size_bytes": 1, "sha256": "a" * 64}])
