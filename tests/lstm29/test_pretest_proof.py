"""Pretest evidence rejects skips, duplicate test IDs and the wrong coverage total."""

import json

import pytest

from scripts.prepare_phase29_pretest import test_evidence as read_test_evidence
from scripts.prepare_phase29_pretest import verified_coverage


def test_pretest_counts_only_unique_passing_cases(tmp_path):
    first = tmp_path / "first.xml"
    first.write_text(
        '<testsuites><testsuite tests="1" errors="0" failures="0" skipped="0"><testcase classname="synthetic" name="one"/></testsuite></testsuites>'
    )
    assert read_test_evidence([first]) == 1
    second = tmp_path / "second.xml"
    second.write_text(first.read_text())
    with pytest.raises(ValueError):
        read_test_evidence([first, second])
    second.write_text(
        '<testsuites><testsuite tests="1" skipped="1"><testcase classname="synthetic" name="two"><skipped/></testcase></testsuite></testsuites>'
    )
    with pytest.raises(ValueError):
        read_test_evidence([second])


def test_coverage_uses_global_totals_not_an_empty_init_file(tmp_path):
    path = tmp_path / "coverage.json"
    path.write_text(
        json.dumps(
            {"files": {"init.py": {"summary": {"percent_covered": 100}}}, "totals": {"percent_covered": 79.9}}
        )
    )
    with pytest.raises(ValueError):
        verified_coverage(path)
    path.write_text(json.dumps({"totals": {"percent_covered": 85.5}}))
    assert verified_coverage(path) == 85.5
