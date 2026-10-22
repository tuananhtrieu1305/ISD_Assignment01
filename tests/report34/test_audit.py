"""Negative publication gates. Synthetic text only."""

import pytest

from scripts.verify_phase34 import check_navigation, check_scope


def test_navigation_accepts_continuous_chapters():
    text = "\n".join(f"# CHƯƠNG {i}. T\n## {i}.1. Mở đầu\n## {i}.2. Triển khai ngắn\n" for i in range(1, 7))
    assert check_navigation(text)["chapters"] == 6


@pytest.mark.parametrize(
    "old,new",
    [("# CHƯƠNG 6.", "# CHƯƠNG 7."), ("## 2.2.", "## 2.4."), ("## 2.2. Triển khai ngắn", "## 2.2. Khác")],
)
def test_navigation_rejects_bad_number_or_last_section(old, new):
    text = "\n".join(f"# CHƯƠNG {i}. T\n## {i}.1. Mở đầu\n## {i}.2. Triển khai ngắn\n" for i in range(1, 7))
    with pytest.raises(ValueError):
        check_navigation(text.replace(old, new))


def test_scope_rejects_placeholder_and_unresolved_citation():
    for text in ["TODO: write later", "[@missing]", "\ufffd"]:
        with pytest.raises(ValueError):
            check_scope(text)


def test_scope_allows_explicit_code_fragment():
    check_scope("Giải thích.\n```python\n# TODO in quoted source is not new prose\n```\n")


def test_actual_manuscript_audit_reads_saved_artifacts_only():
    from scripts.verify_phase34 import audit

    result, trace = audit()
    assert result["status"] == "PASS" and result["requirements"] == 54
    assert result["tables"] == 143 and result["figures"] == 37
    assert result["models_retrained"] == 0 and result["historical_test_evaluation_executed"] is False
    assert len(trace) == 54
    assert next(r for r in trace if r["requirement_id"] == "REQ-54")["deferred"]


def test_traceability_includes_implementation_evidence_before_phase24():
    from scripts.verify_phase34 import audit

    _, trace = audit()
    cleanup = next(r for r in trace if r["requirement_id"] == "REQ-32")
    environment = next(r for r in trace if r["requirement_id"] == "REQ-33")
    assert any(r["path"] == "docs/phase20_report.md" for r in cleanup["evidence"])
    assert any(r["path"] == "artifacts/manifests/environment.json" for r in environment["evidence"])


def test_integrity_ref_rejects_mismatch(monkeypatch, tmp_path):
    from scripts import verify_phase34 as verifier

    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    (tmp_path / "x").write_bytes(b"x")
    with pytest.raises(ValueError, match="Integrity"):
        verifier.checked({"path": "x", "sha256": "0" * 64})


@pytest.mark.parametrize("inner", ["<failure/>", "<skipped/>", "<error/>"])
def test_test_xml_rejects_failed_or_skipped(tmp_path, inner):
    from scripts.verify_phase34 import xml_tests

    path = tmp_path / "tests.xml"
    path.write_text(
        '<testsuites><testsuite><testcase name="x">' + inner + "</testcase></testsuite></testsuites>"
    )
    with pytest.raises(ValueError):
        xml_tests(path)


def test_test_xml_accepts_pass_and_rejects_empty(tmp_path):
    from scripts.verify_phase34 import xml_tests

    path = tmp_path / "tests.xml"
    path.write_text('<testsuites><testsuite><testcase name="x"/></testsuite></testsuites>')
    assert xml_tests(path) == 1
    path.write_text("<testsuites/>")
    with pytest.raises(ValueError):
        xml_tests(path)


def test_test_xml_rejects_duplicate_cases(tmp_path):
    from scripts.verify_phase34 import xml_tests

    path = tmp_path / "tests.xml"
    path.write_text(
        '<testsuites><testsuite><testcase name="x"/><testcase name="x"/></testsuite></testsuites>'
    )
    with pytest.raises(ValueError, match="duplicate"):
        xml_tests(path)


def test_release_packaging_and_readonly_verification(monkeypatch, tmp_path):
    """Synthetic release with no model/assets. Real publication audited separately."""
    import hashlib
    import json

    from scripts import verify_phase34 as verifier

    root = tmp_path
    base = root / "artifacts/manifests/phase34"
    out = root / "report/phase34"
    base.mkdir(parents=True)
    out.mkdir(parents=True)
    monkeypatch.setattr(verifier, "ROOT", root)
    monkeypatch.setattr(verifier, "BASE", base)
    monkeypatch.setattr(verifier, "OUT", out)
    monkeypatch.setattr(
        verifier,
        "ref",
        lambda path: {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        },
    )
    monkeypatch.setattr(
        verifier, "audit", lambda: ({"source_manuscript": {"sha256": "synthetic"}, "status": "PASS"}, [])
    )

    def put(name, value):
        (base / name).write_text(json.dumps(value))

    proof = {"status": "PASS", "locks": [], "unique_protected_files": 2}
    put("preserve_before.json", proof)
    put("preserve_after.json", proof)
    put("editorial_review.json", {"status": "PASS", "manuscript_sha256": "synthetic"})
    put(verifier.ACCEPTANCE_COVERAGE, {"totals": {"percent_covered": 90}})
    put(
        "manuscript_manifest.json",
        {
            name: []
            for name in [
                "data_cards",
                "eda_sources",
                "source_manifests",
                "model_contracts",
                "figures",
                "chapters",
            ]
        },
    )
    put(verifier.LINT, {"status": "FAIL", "source": []})
    (base / verifier.ACCEPTANCE_XML).write_text(
        '<testsuites><testsuite><testcase name="x"/></testsuite></testsuites>'
    )
    with pytest.raises(ValueError, match="Lint"):
        verifier.release()
    put(verifier.LINT, {"status": "PASS", "source": []})
    verifier.release()
    assert json.loads((base / "checkpoint.json").read_text())["status"] == "COMPLETE"
    verifier.verify_lock()
    with pytest.raises(ValueError, match="released"):
        verifier.release()
