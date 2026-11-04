#!/usr/bin/env python3
"""Independent release verifier for the Phase 19 extended term paper."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


WORKSPACE = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
QA = REPORT / "qa_phase19"
DOCX = REPORT / "Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx"
BASELINE = REPORT / "Tieu_luan_AI_ML_CNN_RNN.docx"
BASELINE_SHA256 = "0c82a1e90d394420a7143534ca2b06ebc912648b1c9ea17dd58784d095ce1e9d"
PHASE15_LOCK = "560c671a3920bd6bde9f7fc005f3c952f857c55969c989bb6109932623210c9e"
CORE_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    validation = read_json(REPORT / "report_validation_kg_rag.json")
    page_map = read_json(QA / "word_page_map_final.json")
    visual = read_json(QA / "visual_qa.json")
    a11y = read_json(QA / "a11y.json")
    exceptions = read_json(QA / "accessibility_exceptions.json")
    renderer = read_json(QA / "render_docx_attempt.json")
    regression = read_json(QA / "regression_summary.json")
    phase15 = read_json(WORKSPACE / "term_paper/knowledge_rag/artifacts/manifests/phase15_test_run.json")
    manifest = read_json(REPORT / "report_manifest.json")
    final_hash = sha256(DOCX)

    check("docx_exists_and_is_zip", DOCX.is_file() and DOCX.stat().st_size > 0, DOCX.stat().st_size)
    with zipfile.ZipFile(DOCX) as package:
        broken_member = package.testzip()
        core = ET.fromstring(package.read("docProps/core.xml"))
        body = ET.fromstring(package.read("word/document.xml"))
    check("docx_package_integrity", broken_member is None, broken_member or "ZIP package valid")

    check(
        "structural_validation",
        validation.get("status") == "PASS" and not validation.get("failures"),
        f"{len(validation.get('checks', []))} checks; {len(validation.get('failures', []))} failures",
    )
    check(
        "validation_hash_matches_release",
        validation.get("document_sha256") == final_hash,
        {"validation": validation.get("document_sha256"), "release": final_hash},
    )
    check(
        "navigation_and_pagination",
        page_map.get("page_count") == 86
        and page_map.get("resolved_targets") == 178
        and not page_map.get("missing_targets"),
        {"pages": page_map.get("page_count"), "resolved": page_map.get("resolved_targets")},
    )
    w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    hyperlinks = body.findall(f".//{{{w_ns}}}hyperlink")
    internal_anchors = [node.get(f"{{{w_ns}}}anchor") for node in hyperlinks if node.get(f"{{{w_ns}}}anchor")]
    external_ids = [node.get(f"{{{rel_ns}}}id") for node in hyperlinks if node.get(f"{{{rel_ns}}}id")]
    check(
        "hyperlink_targets",
        set(internal_anchors) == set(page_map.get("pages", {})) and len(external_ids) >= 57,
        {"internal_links": len(internal_anchors), "unique_internal_targets": len(set(internal_anchors)), "external_links": len(external_ids)},
    )

    starts = {
        "intro": page_map["pages"]["heading_002"],
        "chapter1": page_map["pages"]["heading_007"],
        "chapter2": page_map["pages"]["heading_027"],
        "chapter3": page_map["pages"]["heading_056"],
        "chapter4": page_map["pages"]["heading_084"],
        "chapter5": page_map["pages"]["heading_110"],
        "conclusion": page_map["pages"]["heading_131"],
        "references": page_map["pages"]["heading_135"],
    }
    budgets = {
        "intro": starts["chapter1"] - starts["intro"],
        "chapter1": starts["chapter2"] - starts["chapter1"],
        "chapter2": starts["chapter3"] - starts["chapter2"],
        "chapter3": starts["chapter4"] - starts["chapter3"],
        "chapter4": starts["chapter5"] - starts["chapter4"],
        "chapter5": starts["conclusion"] - starts["chapter5"],
    }
    budget_ok = (
        3 <= budgets["intro"] <= 4
        and budgets["chapter1"] == 8
        and all(10 <= budgets[name] <= 15 for name in ("chapter2", "chapter3", "chapter4"))
        and 12 <= budgets["chapter5"] <= 15
    )
    check("chapter_page_budgets", budget_ok, budgets)

    inspected = visual.get("inspected_pages", [])
    check(
        "visual_qa_100_percent",
        visual.get("status") == "PASS" and inspected == list(range(1, 87)),
        f"{len(inspected)}/86 pages",
    )
    a11y_findings = a11y.get("findings", [])
    high_count = sum(item.get("severity") == "high" for item in a11y_findings)
    medium = [item for item in a11y_findings if item.get("severity") == "medium"]
    a11y_ok = (
        high_count == 0
        and len(medium) == 3
        and all(item.get("kind") == "table_no_header_row" for item in medium)
        and exceptions.get("status") == "ACCEPTED"
        and exceptions.get("medium_findings") == 3
    )
    check("accessibility", a11y_ok, {"high": high_count, "medium": len(medium), "exception": exceptions.get("status")})
    check(
        "renderer_exception_documented",
        renderer.get("status") == "UNAVAILABLE"
        and "soffice.exe" in renderer.get("reason", "")
        and renderer.get("authoritative_fallback", {}).get("page_count") == 86,
        renderer.get("reason"),
    )

    creator = core.find("dc:creator", CORE_NS)
    modified_by = core.find("cp:lastModifiedBy", CORE_NS)
    metadata = {"creator": creator.text if creator is not None else None, "lastModifiedBy": modified_by.text if modified_by is not None else None}
    check("release_metadata", set(metadata.values()) == {"Triệu Tuấn Anh"}, metadata)
    check("baseline_docx_unchanged", BASELINE.is_file() and sha256(BASELINE) == BASELINE_SHA256, sha256(BASELINE))
    check(
        "phase15_public_test_lock",
        phase15.get("status") == "COMPLETE"
        and phase15.get("run_count") == 1
        and phase15.get("locked_config_sha256") == PHASE15_LOCK,
        {"status": phase15.get("status"), "run_count": phase15.get("run_count"), "lock": phase15.get("locked_config_sha256")},
    )

    requirements = (WORKSPACE / "term_paper/config/requirements_matrix.md").read_text(encoding="utf-8")
    unresolved = re.findall(r"\|\s*(PLANNED|PENDING_INPUT)\s*\|", requirements)
    check("requirements_matrix_closed", not unresolved, unresolved or "no PLANNED/PENDING_INPUT rows")
    manuscript = (REPORT / "manuscript.md").read_text(encoding="utf-8")
    standalone_deploy = bool(re.search(r"(?mi)^#\s+(?:PHẦN\s+5\.|DEPLOYMENT|TRIỂN KHAI MÔ HÌNH)", manuscript))
    check("no_standalone_deployment_chapter", not standalone_deploy, standalone_deploy)
    check(
        "report_inventory",
        len(manifest.get("figures", [])) == 22
        and len(manifest.get("tables", [])) == 21
        and manifest.get("citations", {}).get("count") == 57,
        {"figures": len(manifest.get("figures", [])), "tables": len(manifest.get("tables", [])), "references": manifest.get("citations", {}).get("count")},
    )
    required_passes = [item for item in regression.get("checks", []) if item.get("name") != "tensorflow_unit_collection"]
    check(
        "regression_suite",
        regression.get("status") == "PASS_WITH_DOCUMENTED_ENVIRONMENT_LIMIT"
        and required_passes
        and all(item.get("status") == "PASS" for item in required_passes),
        {item.get("name"): item.get("status") for item in regression.get("checks", [])},
    )

    failures = [item for item in checks if item["status"] == "FAIL"]
    result = {
        "schema_version": 1,
        "phase": 19,
        "status": "PASS" if not failures else "FAIL",
        "checks_passed": len(checks) - len(failures),
        "checks_total": len(checks),
        "document": DOCX.relative_to(WORKSPACE).as_posix(),
        "document_sha256": final_hash,
        "document_bytes": DOCX.stat().st_size,
        "page_count": page_map.get("page_count"),
        "page_budgets": budgets,
        "inventory": {"navigation_targets": 178, "figures": 22, "tables": 21, "references": 57},
        "checks": checks,
        "failures": failures,
    }
    (QA / "phase19_verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    release = {
        "schema_version": 1,
        "release": "phase19-final",
        "status": result["status"],
        "created_on": "2026-10-14",
        "artifact": result["document"],
        "sha256": final_hash,
        "bytes": DOCX.stat().st_size,
        "pages": page_map.get("page_count"),
        "navigation_targets": {"resolved": 178, "missing": 0},
        "inventory": result["inventory"],
        "page_budgets": budgets,
        "authoritative_renderer": "Microsoft Word 16 PDF export",
        "visual_qa": "86/86 pages PASS",
        "baseline_sha256": BASELINE_SHA256,
        "phase15_locked_config_sha256": PHASE15_LOCK,
        "verification": "term_paper/report/qa_phase19/phase19_verification.json",
    }
    (QA / "final_release_manifest.json").write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": f"{result['checks_passed']}/{result['checks_total']}", "sha256": final_hash}, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
