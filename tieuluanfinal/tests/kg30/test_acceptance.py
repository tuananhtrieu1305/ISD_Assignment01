"""Final gate rejects incomplete QA, duplicate tests and rounded coverage below80%."""

import pytest

from scripts.verify_phase30 import validate_gate, xml_tests


def fixture():
    return {
        "status": "PASS",
        "notebooks_executed": 3,
        "qa_slots_executed": 10,
        "wikidata_entities_inspected": 10,
        "new_test_evaluation_executed": False,
    }


def test_gate_accepts_exact_seven_qa_figures_and_nonempty_coverage():
    figures = [{"path": f"fig/{i}.png"} for i in range(7)]
    qa = {"status": "PASS", "reviewed_pngs": [r["path"] for r in figures]}
    validate_gate(fixture(), {"percent_covered": 80, "num_statements": 100}, qa, figures)


@pytest.mark.parametrize(
    "change", ["coverage", "empty", "missing_qa", "duplicate_qa", "notebook", "test_rerun"]
)
def test_gate_rejects_incomplete_acceptance(change):
    export = fixture()
    figures = [{"path": f"fig/{i}.png"} for i in range(7)]
    qa = {"status": "PASS", "reviewed_pngs": [r["path"] for r in figures]}
    totals = {"percent_covered": 90, "num_statements": 100}
    if change == "coverage":
        totals["percent_covered"] = 79.999
    if change == "empty":
        totals["num_statements"] = 0
    if change == "missing_qa":
        qa["reviewed_pngs"].pop()
    if change == "duplicate_qa":
        qa["reviewed_pngs"].append(qa["reviewed_pngs"][0])
    if change == "notebook":
        export["notebooks_executed"] = 2
    if change == "test_rerun":
        export["new_test_evaluation_executed"] = True
    with pytest.raises(ValueError):
        validate_gate(export, totals, qa, figures)


def test_unique_test_count_rejects_duplicate_and_skipped_xml(tmp_path):
    first = tmp_path / "first.xml"
    first.write_text(
        '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"><testcase classname="c" name="n"/></testsuite></testsuites>'
    )
    assert xml_tests([first]) == 1
    with pytest.raises(ValueError):
        xml_tests([first, first])
    second = tmp_path / "skip.xml"
    second.write_text(
        '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="1"><testcase classname="c" name="s"><skipped/></testcase></testsuite></testsuites>'
    )
    with pytest.raises(ValueError):
        xml_tests([second])
