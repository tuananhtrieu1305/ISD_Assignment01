"""Record final artifact provenance after tests and all-page visual review."""

import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = BASE / "output/DISCOVERING_AI_Agent.docx"
    candidate = BASE / "qa/candidates/r3/DISCOVERING_AI_Agent.docx"
    assert digest(output) == digest(candidate)
    pagination = json.loads((BASE / "qa/final/pagination.json").read_text())
    assert pagination["page_count"] == 14
    assert pagination["practice_pages"] == [7]
    assert [item["pages"] for item in pagination["theory_headings"]] == [[i] for i in range(1, 7)]
    test_root = ET.parse(BASE / "evidence/final_tests.xml").getroot()
    cases = test_root.findall(".//testcase")
    assert len(cases) == 27
    assert not test_root.findall(".//failure")
    assert not test_root.findall(".//error")
    assert not test_root.findall(".//skipped")
    coverage = json.loads((BASE / "evidence/final_coverage.json").read_text())
    assert coverage["totals"]["percent_covered"] == 100
    reviewed = json.loads((BASE / "evidence/visual_review_r3.json").read_text())
    assert reviewed["reviewed_pages"] == list(range(1, 15))
    assert reviewed["status"] == "PASS"
    receipt = {
        "status": "COMPLETE",
        "recorded_at": datetime.now(UTC).isoformat(),
        "assignment": "DISCOVERING AI Agent, independent from V3",
        "output": {"path": str(output.relative_to(BASE)), "sha256": digest(output),
                   "bytes": output.stat().st_size},
        "pages": {"total": 14, "theory": 6, "practice": 7, "references": 1},
        "executed_notebook_cells": 9,
        "embedded_screenshots": 9,
        "tests": {"passed": len(cases), "failed": 0, "skipped": 0,
                  "core_statement_branch_coverage_percent": 100,
                  "coverage_scope": "discovering_ai_agent.experiment only"},
        "color_checks": "DOCX text black; screenshot and rendered page RGB channels identical",
        "visual_review": "evidence/visual_review_r3.json",
        "environment": "Existing pinned Ubuntu code runtime and approved Phase35 document runtime; no installation",
        "notebook_sha256": digest(BASE / "notebooks/Discovering_AI_Agent.ipynb"),
        "source_manifest_sha256": digest(BASE / "sources/manifest.json"),
        "test_receipt_sha256": digest(BASE / "evidence/final_tests.xml"),
        "screenshot_manifest_sha256": digest(BASE / "evidence/screenshot_manifest.json"),
        "pdf_sha256": digest(BASE / "qa/final/DISCOVERING_AI_Agent.pdf"),
        "limitations": ["Single maze and seed", "CPU NumPy, not GPU training",
                        "Pagination verified in existing LibreOffice renderer, not every Word version"],
    }
    (BASE / "evidence/verification.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
