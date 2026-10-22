"""Pure auditor fixtures. No neural or historical TEST forward."""

import pytest

from scripts import verify_phase33 as audit


def test_xml_counts_unique_and_refuses_skip_or_failure(tmp_path):
    first = tmp_path / "a.xml"
    first.write_text(
        '<testsuites><testsuite><testcase classname="fixture" name="a"/></testsuite></testsuites>'
    )
    assert audit.xml_count([first]) == 1
    with pytest.raises(ValueError):
        audit.xml_count([first, first])
    for tag in ["failure", "error", "skipped"]:
        first.write_text(
            f'<testsuites><testsuite><testcase classname="fixture" name="a"><{tag}/></testcase></testsuite></testsuites>'
        )
        with pytest.raises(ValueError):
            audit.xml_count([first])


def test_ref_checks_path_and_byte_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    path = tmp_path / "file.txt"
    path.write_text("original")
    record = audit.ref(path)
    assert audit.checked(record) == path
    path.write_text("changed")
    with pytest.raises(ValueError):
        audit.checked(record)
    with pytest.raises(ValueError):
        audit.checked({"path": "../escape", "sha256": "0" * 64})


@pytest.mark.parametrize("metric", ["statements", "branches", "functions", "lines"])
def test_coverage_threshold_every_dimension(metric):
    summary = {"total": {key: {"pct": 90} for key in ["statements", "branches", "functions", "lines"]}}
    audit.validate_coverage(summary)
    summary["total"][metric]["pct"] = 79.9
    with pytest.raises(ValueError):
        audit.validate_coverage(summary)


def test_live_matrix_is_not_a_new_scientific_evaluation():
    assert len(audit.LIVE_MATRIX) == 18
    assert len(set(audit.LIVE_MATRIX)) == 18


def test_probe_split_marker_matches_actual_parent_roles():
    assert audit.expected_probe_split("ch3_idrid") == "train"
    assert audit.expected_probe_split("ch6_gold_tasks") == "parent_train"
    assert audit.expected_probe_split("ch5_finqa") == "demo_not_benchmark"
