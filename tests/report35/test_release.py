import json
import pytest
from scripts.phase35_release import check_file, require_clean_tests, require_review_complete, audit


def test_hash_check_detects_mutation_and_escape(tmp_path):
    import hashlib

    path = tmp_path / "file"
    path.write_bytes(b"unit")
    row = {"path": "file", "sha256": hashlib.sha256(b"unit").hexdigest()}
    check_file(row, tmp_path)
    path.write_bytes(b"other")
    with pytest.raises(ValueError):
        check_file(row, tmp_path)
    with pytest.raises(ValueError):
        check_file({"path": "../escape", "sha256": "0" * 64}, tmp_path)


def test_clean_tests_reject_failed_or_skipped(tmp_path):
    path = tmp_path / "tests.xml"
    path.write_text('<testsuites><testsuite tests="2" failures="0" errors="0" skipped="0"/></testsuites>')
    assert require_clean_tests(path) == 2
    for key in ["failures", "errors", "skipped"]:
        path.write_text(
            f'<testsuites><testsuite tests="2" failures="{int(key == "failures")}" errors="{int(key == "errors")}" skipped="{int(key == "skipped")}"/></testsuites>'
        )
        with pytest.raises(ValueError):
            require_clean_tests(path)


def test_visual_gate_cannot_accept_partial_review(tmp_path):
    path = tmp_path / "batches"
    path.mkdir()
    (path / "unit.json").write_text(
        json.dumps(
            {"status": "PASS", "docx_sha256": "doc", "pages": [{"page": 1, "path": "image", "sha256": "x"}]}
        )
    )
    with pytest.raises(ValueError):
        require_review_complete(path, 2, "doc", tmp_path)


def test_real_final_structure_is_read_only():
    result = audit("candidate-r12")
    assert result["status"] == "PASS"
    assert result["pages"] == 202
    assert result["page_cache_targets"] == 256
    assert result["original_parts_byte_unchanged"] == 60
    assert result["scientific_inference_executed"] is False


def test_review_gate_checks_image_hash_and_candidate(tmp_path):
    import hashlib

    base = tmp_path / "batch"
    base.mkdir()
    (tmp_path / "image").write_bytes(b"synthetic")
    row = {"page": 1, "path": "image", "sha256": hashlib.sha256(b"synthetic").hexdigest()}
    path = base / "one.json"
    path.write_text(json.dumps({"status": "PASS", "docx_sha256": "doc", "pages": [row]}))
    assert require_review_complete(base, 1, "doc", tmp_path) == [row]
    with pytest.raises(ValueError):
        require_review_complete(base, 1, "other", tmp_path)
    (tmp_path / "image").write_bytes(b"changed")
    with pytest.raises(ValueError):
        require_review_complete(base, 1, "doc", tmp_path)


@pytest.mark.parametrize("name", ["../escape", "candidate-r12/other"])
def test_audit_rejects_candidate_path_escape(name):
    with pytest.raises(ValueError):
        audit(name)


def test_vendor_helpers_are_read_only_and_receipt_is_write_once(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import scripts.phase35_release as publication

    monkeypatch.setattr(publication, "ROOT", tmp_path)
    doc = tmp_path / "report/build/phase35/candidate-r1.docx"
    doc.parent.mkdir(parents=True)
    doc.write_bytes(b"SYNTHETIC NOT DOCX")
    calls = []

    def fake(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="SYNTHETIC UNIT REPORT", stderr="")

    monkeypatch.setattr(publication.subprocess, "run", fake)
    report = publication.vendor_audits("candidate-r1")
    assert len(calls) == 6 and report["source_unchanged"]
    receipt = tmp_path / "artifacts/manifests/phase35/vendor_audits_candidate-r1.json"
    original = receipt.read_bytes()
    publication.vendor_audits("candidate-r1")
    assert receipt.read_bytes() == original  # identical evidence is idempotent, not overwritten
    monkeypatch.setattr(
        publication.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=0, stdout="DIFFERENT", stderr=""),
    )
    with pytest.raises(FileExistsError):
        publication.vendor_audits("candidate-r1")
    with pytest.raises(ValueError):
        publication.vendor_audits("../escape")


def test_no_test_suites_or_zero_tests_is_not_a_pass(tmp_path):
    path = tmp_path / "empty.xml"
    for value in ["<testsuites/>", '<testsuites><testsuite tests="0"/></testsuites>']:
        path.write_text(value)
        with pytest.raises(ValueError):
            require_clean_tests(path)


def test_vendor_helper_nonzero_or_source_mutation_is_rejected(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import scripts.phase35_release as publication

    monkeypatch.setattr(publication, "ROOT", tmp_path)
    doc = tmp_path / "report/build/phase35/candidate-r1.docx"
    doc.parent.mkdir(parents=True)
    doc.write_bytes(b"SYNTHETIC")
    monkeypatch.setattr(
        publication.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=1, stdout="", stderr="SYNTHETIC ERROR"),
    )
    with pytest.raises(ValueError):
        publication.vendor_audits("candidate-r1")

    def mutate(*a, **kw):
        doc.write_bytes(doc.read_bytes() + b"changed")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(publication.subprocess, "run", mutate)
    with pytest.raises(ValueError):
        publication.vendor_audits("candidate-r1")
