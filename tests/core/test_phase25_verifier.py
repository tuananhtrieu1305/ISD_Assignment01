import pytest

from scripts.verify_phase25 import check_xml, verify_files


def test_verifier_checks_hashes_and_rejects_failed_or_skipped_evidence(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("unchanged")
    from src.common.artifact_core import sha256_file

    records = [{"path": "sample.txt", "sha256": sha256_file(path)}]
    assert verify_files(tmp_path, records) == 1
    path.write_text("changed")
    with pytest.raises(ValueError):
        verify_files(tmp_path, records)
    xml = tmp_path / "tests.xml"
    xml.write_text('<testsuites><testsuite tests="2" failures="0" errors="0" skipped="0"/></testsuites>')
    assert check_xml(xml) == 2
    xml.write_text('<testsuites><testsuite tests="2" failures="0" errors="0" skipped="1"/></testsuites>')
    with pytest.raises(ValueError):
        check_xml(xml)
