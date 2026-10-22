"""Phase34 content/provenance audit and release. No model/TEST imports or forward."""

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET

from scripts.build_phase34 import BASE, CHAPTERS, OUT, load_text, ref
from scripts.phase34_editor import figure_captions, markdown_blocks, safe_path, source_excerpt
from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json

ACCEPTANCE_XML = "acceptance-tests-r3.xml"
ACCEPTANCE_COVERAGE = "acceptance_coverage_r3.json"
LINT = "lint-r3.json"


def checked(row):
    path = safe_path(ROOT, row["path"])
    if sha256_file(path) != row["sha256"]:
        raise ValueError("Integrity mismatch " + row["path"])
    return path


def check_scope(text):
    prose = "\n".join(b["text"] for b in markdown_blocks(text) if b["kind"] != "code")
    if re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b|\[@|\ufffd", prose):
        raise ValueError("Unresolved manuscript content")


def check_navigation(text):
    headings = [b["text"] for b in markdown_blocks(text) if b["kind"] == "heading"]
    chapters = [int(m[1]) for h in headings if (m := re.match(r"# CHƯƠNG (\d+)\.", h))]
    if chapters != list(range(1, 7)):
        raise ValueError("Expected six chapters in order")
    for number in chapters:
        sections = [
            (int(m[1]), h) for h in headings if (m := re.match(r"## " + str(number) + r"\.(\d+)\.", h))
        ]
        if [s[0] for s in sections] != list(range(1, len(sections) + 1)):
            raise ValueError("Non-continuous section numbering")
        if number > 1 and "Triển khai" not in sections[-1][1]:
            raise ValueError("Deployment must be last content section")
    return {"chapters": 6, "numbered_sections": sum(bool(re.match(r"## \d+\.\d+\.", h)) for h in headings)}


def make_traceability(manifest):
    rows = list(csv.DictReader((ROOT / "docs/traceability_v3.csv").open(encoding="utf-8-sig", newline="")))
    headings = manifest["headings"]
    groups = {
        1: [1, 2],
        2: [2, 11, 16],
        3: [12],
        4: [3, 13, 14, 26],
        5: [4, 28],
        6: [5, 41, 42, 43],
    }
    by_requirement = {
        requirement: chapter for chapter, requirements in groups.items() for requirement in requirements
    }
    proofs = []
    for row in rows:
        number = int(row["requirement_id"].split("-")[1])
        chapter = by_requirement.get(number)
        locators = (
            [h for h in headings if h.startswith("## " + str(chapter) + ".")]
            if chapter
            else [h for h in headings if h.startswith("## C.")]
        )
        if number in [6, 7, 8, 9, 10, 50]:
            locators = [h for h in headings if h.startswith("## A.")]
        if number in [15, 18, 19, 21, 39]:
            locators = [h for h in headings if h.startswith("## B.")]
        if number in [20, 22, 23, 24, 25, 27, 29, 30, 31, 47]:
            locators = [h for h in headings if re.match(r"## [2-6]\.\d+\.", h)]
        status = "CONTENT_AND_PRIOR_EVIDENCE_LINKED"
        deferred = []
        if number in [1, 46, 54]:
            status, deferred = (
                "CONTENT_READY_FINAL_DOCX_QA_DEFERRED",
                ["Phase35 DOCX pagination/render/Word release"],
            )
        if number == 45:
            status, deferred = (
                "LOCAL_API_UI_VERIFIED_CLOUD_NOT_DEPLOYED",
                ["Cloud deployment not authorized/performed; no cloud SLA claim"],
            )
        phases = [int(p) for p in row["phases"].split(";") if p.isdigit() and 20 <= int(p) <= 33]
        evidence = []
        for phase in phases:
            evidence.append(ref(ROOT / f"docs/phase{phase}_report.md"))
            if phase == 20:
                path = ROOT / "artifacts/manifests/phase20/outcomes-summary.json"
            elif phase == 21:
                path = ROOT / "artifacts/manifests/environment.json"
            elif phase == 22:
                path = ROOT / "artifacts/manifests/phase22/spec_lock.json"
            elif phase == 23:
                path = (
                    ROOT / "artifacts/manifests/phase23/updates/idrid_20261017_8a9f4752b35d/dataset_lock.json"
                )
            elif phase == 24:
                path = ROOT / "artifacts/manifests/phase24/data_lock.json"
            elif phase == 25:
                path = ROOT / "artifacts/manifests/phase25/core_lock.json"
            elif phase == 26:
                path = ROOT / "artifacts/manifests/phase26/revisions/r2/experiment_lock.json"
            else:
                path = ROOT / f"artifacts/manifests/phase{phase}/experiment_lock.json"
            evidence.append(ref(path))
        if not evidence:
            evidence = [ref(ROOT / "artifacts/manifests/phase22/spec_lock.json")]
        proofs.append(
            {
                "requirement_id": row["requirement_id"],
                "requirement": row["requirement"],
                "report_locators": locators,
                "evidence": evidence,
                "status": status,
                "deferred": deferred,
            }
        )
    if len(proofs) != 54 or any(not row["report_locators"] for row in proofs):
        raise ValueError("Traceability incomplete")
    return proofs


def audit():
    manifest = read_json(BASE / "manuscript_manifest.json")
    text = load_text(checked(manifest["manuscript"]))
    check_scope(text)
    navigation = check_navigation(text)
    if (
        any(
            manifest[name]
            for name in ["historical_test_evaluation_executed", "models_retrained", "docx_authored"]
        )
        or manifest["page_count"] is not None
    ):
        raise ValueError("False scope claim")
    for category in ["data_cards", "eda_sources", "source_manifests", "model_contracts", "figures"]:
        for row in manifest[category]:
            checked(row)
    if len(manifest["data_cards"]) != 18 or len(manifest["model_contracts"]) != 36:
        raise ValueError("Incomplete data/model contract matrix")
    for chapter in manifest["chapters"]:
        checked(chapter["source"])
        checked(chapter["output"])
        if len(chapter["dataset_ids"]) != 3 or chapter["source"]["path"] != CHAPTERS[chapter["chapter"]]:
            raise ValueError("Wrong active chapter or data matrix")
    captions = figure_captions(text)
    if captions != read_json(BASE / "figure_ledger.json") or len(captions) != len(manifest["figures"]):
        raise ValueError("Figure ledger mismatch")
    for chapter in range(1, 7):
        ids = [
            int(m[1]) for r in captions if (m := re.match(r"Hình " + str(chapter) + r"\.(\d+)\.", r["label"]))
        ]
        if ids != list(range(1, len(ids) + 1)):
            raise ValueError("Figure numbering mismatch")
    tables = read_json(BASE / "table_ledger.json")
    for row in tables:
        if (
            row["markdown"] not in text
            or hashlib.sha256(row["markdown"].encode()).hexdigest() != row["sha256"]
        ):
            raise ValueError("Numeric table not byte-identical")
    for chapter in [1, 2, 3, 4, 5, 6, "A", "B", "C", "D"]:
        labels = [r["label"] for r in tables if r["chapter"] == chapter]
        if labels != [f"Bảng {chapter}.{i}." for i in range(1, len(labels) + 1)]:
            raise ValueError("Table numbering mismatch")
    available = {row["label"].rstrip(".") for row in tables + captions}
    prose = "\n".join(b["text"] for b in markdown_blocks(text) if b["kind"] != "code")
    for match in re.finditer(r"\b(Hình|Bảng)\s+([1-6]\.\d+)", prose):
        if match[1] + " " + match[2] not in available:
            raise ValueError("Unresolved figure/table cross-reference")
    extension = read_json(OUT / "outline_extension.json")
    outline = read_json(ROOT / "report/outline_v3.json")
    expected = {section["id"] for chapter in outline["chapters"] for section in chapter["sections"]}
    if set(extension["mapping"]) != expected:
        raise ValueError("Outline extension incomplete")
    for targets in extension["mapping"].values():
        if any(
            not any(re.match(r"^#{2,4}\s+" + re.escape(target) + r"\.", h) for h in manifest["headings"])
            for target in targets
        ):
            raise ValueError("Outline extension target missing")
    # Check all relative Markdown targets in the single-file handoff, not only image links.
    local_targets = 0
    for match in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", text):
        target = match[1]
        if re.match(r"^(?:https?://|mailto:|#)", target):
            continue
        path = (OUT / target).resolve()
        safe_path(ROOT, path.relative_to(ROOT))
        local_targets += 1
    for row in read_json(BASE / "code_excerpt_ledger.json"):
        code, first, last = source_excerpt(checked(row["source"]), row["class"], row["method"])
        if (
            code not in text
            or (first, last) != (row["first_line"], row["last_line"])
            or hashlib.sha256(code.encode()).hexdigest() != row["code_sha256"]
        ):
            raise ValueError("Code excerpt altered")
    for row in read_json(BASE / "formula_ledger.json"):
        checked(row["source"])
        if any(
            not row[key] for key in ["expression", "symbols", "why_needed", "plain_explanation", "example"]
        ):
            raise ValueError("Formula lacks explanation")
    trace = make_traceability(manifest)
    return {
        **navigation,
        "status": "PASS",
        "tables": len(tables),
        "figures": len(captions),
        "citations": len(manifest["citation_order"]),
        "data_cards": 18,
        "contracts": 36,
        "requirements": 54,
        "relative_targets": local_targets,
        "source_manuscript": manifest["manuscript"],
        "docx_authored": False,
        "page_qa": "deferred_phase35",
        "historical_test_evaluation_executed": False,
        "models_retrained": 0,
    }, trace


def xml_tests(path):
    rows = ET.parse(path).findall(".//testcase")
    names = [(row.get("classname", ""), row.get("name")) for row in rows]
    if len(names) != len(set(names)):
        raise ValueError("Acceptance XML has duplicate cases")
    if not rows or any(
        row.find(name) is not None for row in rows for name in ["failure", "error", "skipped"]
    ):
        raise ValueError("Acceptance tests incomplete")
    return len(rows)


def verify_lock():
    lock = read_json(BASE / "experiment_lock.json")
    for row in lock["files"]:
        checked(row)
    print(
        json.dumps({"status": "PASS", "files": len(lock["files"]), "mode": "read_only_no_inference"}),
        flush=True,
    )


def release():
    if (BASE / "experiment_lock.json").exists():
        raise ValueError("Phase34 already released; verify-only or a new revision")
    result, trace = audit()
    before = read_json(BASE / "preserve_before.json")
    after = read_json(BASE / "preserve_after.json")
    if before != after or before["status"] != "PASS":
        raise ValueError("Preservation incomplete")
    for row in before["locks"]:
        checked(row)
    qa = read_json(BASE / "editorial_review.json")
    if qa["status"] != "PASS" or qa["manuscript_sha256"] != result["source_manuscript"]["sha256"]:
        raise ValueError("Editorial review stale or absent")
    count = xml_tests(BASE / ACCEPTANCE_XML)
    coverage = read_json(BASE / ACCEPTANCE_COVERAGE)["totals"]["percent_covered"]
    if coverage < 80:
        raise ValueError("New editor/assembler/auditor code coverage below80")
    lint = read_json(BASE / LINT)
    if lint["status"] != "PASS":
        raise ValueError("Lint/entrypoint review incomplete")
    for row in lint["source"]:
        checked(row)
    write_once(BASE / "traceability.json", trace)
    matrix = "# MA TRẬN YÊU CẦU VÀ BẰNG CHỨNG\n\n54 yêu cầu gốc được giữ nguyên. CONTENT_AND_PRIOR_EVIDENCE_LINKED chỉ xác nhận nội dung và liên kết bằng chứng nghiệm thu trước; không thay thế DOCX render hay cloud deploy. Các trạng thái deferred ghi rõ công việc chưa thực hiện.\n\n| ID | Yêu cầu | Locator nội dung | Trạng thái / việc còn lại |\n|---|---|---|---|\n"
    for row in trace:
        locator = "; ".join(row["report_locators"][:3]).replace("|", "/")
        matrix += (
            "| "
            + row["requirement_id"]
            + " | "
            + row["requirement"].replace("|", "/")
            + " | "
            + locator
            + " | "
            + row["status"]
            + ("; " + "; ".join(row["deferred"]) if row["deferred"] else "")
            + " |\n"
        )
    (OUT / "requirements_matrix.md").write_text(matrix, encoding="utf-8")
    paths = {
        *OUT.glob("*.md"),
        *OUT.glob("*.bib"),
        *OUT.glob("inputs/*"),
        *OUT.glob("sections/*.md"),
        *ROOT.glob("docs/phase34*.md"),
        *ROOT.glob("scripts/*phase34*.*"),
        *ROOT.glob("tests/report34/*.py"),
    }
    paths.add(OUT / "outline_extension.json")
    paths.update(
        BASE / name
        for name in [
            "manuscript_manifest.json",
            "table_ledger.json",
            "figure_ledger.json",
            "formula_ledger.json",
            "code_excerpt_ledger.json",
            "reference_style_evidence.json",
            "preserve_before.json",
            "preserve_after.json",
            "editorial_review.json",
            ACCEPTANCE_XML,
            ACCEPTANCE_COVERAGE,
            "traceability.json",
            LINT,
            "powershell_parser.json",
            "source_review_r1.zip",
            "lint.json",
            "acceptance-tests.xml",
            "acceptance_coverage.json",
            "source_review_r2.zip",
            "lint-r2.json",
            "acceptance-tests-r2.xml",
            "acceptance_coverage_r2.json",
        ]
    )
    for category in ["data_cards", "eda_sources", "source_manifests", "model_contracts", "figures"]:
        paths.update(checked(r) for r in read_json(BASE / "manuscript_manifest.json")[category])
    paths.update(checked(row["source"]) for row in read_json(BASE / "manuscript_manifest.json")["chapters"])
    pointer = ROOT / "report/active_manuscript_v3.json"
    if pointer.exists():
        paths.add(pointer)
    paths.update(checked(r) for r in before["locks"])
    paths.update(checked(r) for item in trace for r in item["evidence"])
    write_once(
        BASE / "experiment_lock.json",
        {
            "phase": 34,
            "files": [ref(path) for path in sorted(paths) if path.is_file()],
            "scope": "Integrated manuscript and evidence; DOCX/render deferred35",
            "historical_test_evaluation_executed": False,
        },
    )
    verify_lock()
    write_once(
        BASE / "verification.json",
        {
            **result,
            "tests": count,
            "coverage": coverage,
            "protected_files": before["unique_protected_files"],
            "experiment_lock": ref(BASE / "experiment_lock.json"),
        },
    )
    (BASE / "checkpoint.json").write_text(
        json.dumps(
            {
                "phase": 34,
                "status": "COMPLETE",
                "controller_pid": None,
                "experiment_lock": ref(BASE / "experiment_lock.json"),
                "verification": ref(BASE / "verification.json"),
                "docx_authored": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["audit", "release", "verify-only"], required=True)
    args = parser.parse_args()
    if args.stage == "verify-only":
        verify_lock()
    elif args.stage == "release":
        release()
    else:
        result, _ = audit()
        print(json.dumps(result), flush=True)
