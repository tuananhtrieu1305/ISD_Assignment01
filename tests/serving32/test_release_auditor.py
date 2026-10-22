"""Release auditor fixtures; no model construction or historical TEST access."""

import json

import pytest

from scripts import verify_phase32 as audit


def test_unique_xml_count_and_duplicate(tmp_path):
    path = tmp_path / "tests.xml"
    path.write_text(
        '<testsuites><testsuite><testcase classname="fixture" name="a"/></testsuite></testsuites>',
        encoding="utf-8",
    )
    assert audit.xml_count([path]) == 1
    with pytest.raises(ValueError):
        audit.xml_count([path, path])


@pytest.mark.parametrize("tag", ["failure", "error", "skipped"])
def test_bad_xml_fails_closed(tmp_path, tag):
    path = tmp_path / "tests.xml"
    path.write_text(
        f'<testsuites><testsuite><testcase classname="fixture" name="a"><{tag}/></testcase></testsuite></testsuites>',
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        audit.xml_count([path])


def test_lock_verification_reads_every_hash(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "BASE", tmp_path)
    path = tmp_path / "asset.json"
    path.write_text("{}", encoding="utf-8")
    record = audit.ref(path)
    (tmp_path / "experiment_lock.json").write_text(json.dumps({"files": [record]}), encoding="utf-8")
    audit.verify_lock()
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        audit.verify_lock()
    with pytest.raises(ValueError):
        audit.checked({"path": "../escape.json", "sha256": "0" * 64})
