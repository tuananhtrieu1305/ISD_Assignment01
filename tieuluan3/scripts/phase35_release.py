"""Read-only publication checks and fail-closed Phase35 release packaging."""

import argparse
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from lxml import etree as E
from scripts.phase35_runtime import ROOT, digest, write_once_json
from scripts.phase35_docx import NS, W, TEMPLATE, EDITABLE, bookmark_name


def check_file(row, root=ROOT):
    root = Path(root).resolve()
    path = (root / row["path"]).resolve()
    if not path.is_relative_to(root) or path.is_symlink():
        raise ValueError("Reference escapes root")
    if digest(path) != row["sha256"]:
        raise ValueError("Hash mismatch: " + row["path"])
    return path


def ref(path):
    path = Path(path)
    return {"path": str(path.relative_to(ROOT)), "sha256": digest(path), "bytes": path.stat().st_size}


def require_clean_tests(path):
    root = ET.parse(path).getroot()
    suites = list(root.iter("testsuite"))
    if not suites or any(int(s.get(k, 0)) for s in suites for k in ["failures", "errors", "skipped"]):
        raise ValueError("Tests failed, errored, skipped or absent")
    count = sum(int(s.get("tests", 0)) for s in suites)
    if count <= 0:
        raise ValueError("No tests")
    return count


def require_review_complete(directory, total, sha, root=ROOT):
    rows = []
    for path in sorted(Path(directory).glob("*.json")):
        witness = json.loads(path.read_text())
        if witness["status"] != "PASS" or witness["docx_sha256"] != sha:
            raise ValueError("Review belongs to a different/failed candidate")
        rows.extend(witness["pages"])
    if sorted(r["page"] for r in rows) != list(range(1, total + 1)):
        raise ValueError("Incomplete or duplicated manual page review")
    for row in rows:
        check_file(row, root)
    return rows


def vendor_audits(candidate):
    if not re.fullmatch(r"candidate-r\d+", candidate):
        raise ValueError("Invalid candidate")
    doc = ROOT / "report/build/phase35" / (candidate + ".docx")
    before = digest(doc)
    vendor = ROOT / "report/tools/documents_vendor_26_1020/scripts"
    outputs = []
    for name in [
        "section_audit",
        "style_lint",
        "heading_audit",
        "images_audit",
        "fields_report",
        "content_controls",
    ]:
        command = [sys.executable, str(vendor / (name + ".py")), str(doc)]
        if name == "content_controls":
            command += ["list", "--json"]
        result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
        outputs.append(
            {"helper": name, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        )
        if result.returncode:
            raise ValueError("Vendor audit failed: " + name)
    if digest(doc) != before:
        raise ValueError("Read-only helper changed document")
    result = {
        "status": "EXECUTED",
        "candidate": candidate,
        "sha256": before,
        "source_unchanged": True,
        "reports": outputs,
        "note": "Advisory output requires interpretation; not a substitute for manual page QA",
    }
    write_once_json(ROOT / "artifacts/manifests/phase35" / ("vendor_audits_" + candidate + ".json"), result)
    return result


def audit(candidate):
    if not re.fullmatch(r"candidate-r\d+", candidate):
        raise ValueError("Invalid candidate")
    base = ROOT / "report/build/phase35"
    doc = base / (candidate + ".docx")
    build = json.loads((base / (candidate + ".build.json")).read_text())
    if digest(doc) != build["sha256"]:
        raise ValueError("DOCX changed after build")
    pdf_dir = ROOT / "report/qa35" / candidate
    report = json.loads((pdf_dir / "inspection.json").read_text())
    if digest(pdf_dir / (candidate + ".pdf")) != report["sha256"]:
        raise ValueError("PDF changed")
    if any(row["outside_safe"] for row in report["pages_detail"]):
        raise ValueError("PDF geometry overflow")
    with zipfile.ZipFile(TEMPLATE) as z:
        original = {n: z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(doc) as z:
        if len(z.namelist()) != len(set(z.namelist())) or z.testzip() is not None:
            raise ValueError("Invalid ZIP")
        parts = {n: z.read(n) for n in z.namelist()}
    for name, data in original.items():
        if name not in EDITABLE and parts[name] != data:
            raise ValueError("Opaque part changed: " + name)
    before = E.fromstring(original["word/styles.xml"])
    after = E.fromstring(parts["word/styles.xml"])
    if len(after) <= len(before):
        raise ValueError("Missing appended styles")
    for index, node in enumerate(before):
        if E.tostring(node, method="c14n") != E.tostring(after[index], method="c14n"):
            raise ValueError("Original style changed")
    xml = E.fromstring(parts["word/document.xml"])
    text = "".join(xml.itertext())
    if any(raw in text for raw in [r"\operatorname", r"\frac", r"\sum_j", r"\in\{"]):
        raise ValueError("Unconverted TeX")
    old = E.fromstring(original["word/document.xml"])
    if E.tostring(xml.find(".//w:sectPr", NS), method="c14n") != E.tostring(
        old.find(".//w:sectPr", NS), method="c14n"
    ):
        raise ValueError("Template page geometry changed")
    if len(xml.findall(".//w:tbl", NS)) != 144 or len(build["captions"]) != 180 or len(build["images"]) != 37:
        raise ValueError("Missing publication objects")
    if xml.findall(".//w:trHeight", NS):
        raise ValueError("Fixed table row heights are prohibited")
    if len(xml.findall(".//m:oMath", NS)) < 5:
        raise ValueError("Math not native")
    starts = xml.findall(".//w:bookmarkStart", NS)
    names = {x.get(W + "name") for x in starts}
    ids = {x.get(W + "id") for x in starts}
    if len(names) != len(starts) or len(ids) != len(starts):
        raise ValueError("Duplicate bookmarks")
    for index in range(1, 44):
        if bookmark_name("reference_" + str(index)) not in names:
            raise ValueError("Missing bibliography target")
    instructions = []
    for f in xml.findall(".//w:fldSimple", NS):
        instruction = f.get(W + "instr").split()
        instructions.append(instruction[0])
        if instruction[0] not in {"SEQ", "REF", "PAGEREF"}:
            raise ValueError("Unexpected body field")
        if instruction[0] in {"REF", "PAGEREF"} and instruction[1] not in names:
            raise ValueError("Unresolved field")
        if instruction[0] == "PAGEREF":
            cached = "".join(t.text or "" for t in f.findall(".//w:t", NS))
            if cached != str(report["page_map"][instruction[1]]):
                raise ValueError("Stale page cache " + instruction[1])
    if (
        instructions.count("SEQ") != 180
        or instructions.count("REF") != 180
        or instructions.count("PAGEREF") != 256
    ):
        raise ValueError("Incomplete indices")
    for h in xml.findall(".//w:hyperlink", NS):
        if h.get(W + "anchor") and h.get(W + "anchor") not in names:
            raise ValueError("Unresolved hyperlink")
    footer = E.fromstring(parts["word/footer1.xml"])
    fields = footer.findall(".//w:fldSimple", NS)
    if [f.get(W + "instr") for f in fields] != ["PAGE", "NUMPAGES"]:
        raise ValueError("Footer fields missing")
    if "".join(t.text or "" for t in fields[1].findall(".//w:t", NS)) != str(report["pages"]):
        raise ValueError("Stale NUMPAGES cache")
    word = json.loads(
        (ROOT / f"artifacts/manifests/phase35/word_open_{candidate.replace('-', '_')}_r2.json").read_text()
    )
    if (
        word["status"] != "PASS"
        or word["sha256"] != build["sha256"]
        or word["pages"] != report["pages"]
        or word["field_update_first_error_index"] != 0
        or not word["source_unchanged"]
        or word["saved"]
    ):
        raise ValueError("Word-open/update verification incomplete")
    required = [x for x in build["headings"] if x["toc"]] + build["captions"]
    if any(report["page_map"][x["anchor"]] != build["page_map"][x["anchor"]] for x in required):
        raise ValueError("Pagination not stable")
    return {
        "status": "PASS",
        "docx": ref(doc),
        "pdf": ref(pdf_dir / (candidate + ".pdf")),
        "pages": report["pages"],
        "tables": 144,
        "captioned_tables": 143,
        "figures": 37,
        "captions": 180,
        "bookmarks": len(names),
        "native_equations": len(xml.findall(".//m:oMath", NS)),
        "page_cache_targets": len(required),
        "original_parts_byte_unchanged": sum(parts[n] == v for n, v in original.items()),
        "original_styles_canonical_unchanged": True,
        "word": word,
        "scientific_inference_executed": False,
    }


def release(candidate, tests, coverage):
    result = audit(candidate)
    count = require_clean_tests(tests)
    ui_count = require_clean_tests(ROOT / "artifacts/manifests/phase35/ui-r2.xml")
    if ui_count != 23:
        raise ValueError("UI smoke incomplete")
    cov = json.loads(coverage.read_text())
    if cov["totals"]["percent_covered"] < 80:
        raise ValueError("Coverage below 80 percent")
    rows = require_review_complete(
        ROOT / "artifacts/manifests/phase35/visual_batches" / candidate,
        result["pages"],
        result["docx"]["sha256"],
    )
    preservation = json.loads((ROOT / "artifacts/manifests/phase35/preserve_after.json").read_text())
    if preservation["status"] != "PASS" or preservation["unique_protected_files"] != 31848:
        raise ValueError("Preservation incomplete")
    for row in preservation["locks"]:
        check_file(row)
    required_docs = [
        ROOT / "docs/phase35_report.md",
        ROOT / "docs/phase35_operations.md",
        ROOT / "docs/demo_v3.md",
    ]
    if not all(p.is_file() for p in required_docs):
        raise ValueError("Handoff documentation absent")
    target = ROOT / "releases/v3/Tieu_luan_AI_6_chuong.docx"
    pdf_target = ROOT / "releases/v3/Tieu_luan_AI_6_chuong_QA.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    pairs = [(ROOT / result["docx"]["path"], target), (ROOT / result["pdf"]["path"], pdf_target)]
    for dest in [
        target,
        pdf_target,
        ROOT / "releases/v3/release_manifest.json",
        ROOT / "artifacts/manifests/phase35/release_lock.json",
    ]:
        if dest.exists():
            raise FileExistsError("Release destination exists: " + str(dest))
    for source, dest in pairs:
        with source.open("rb") as inp, dest.open("xb") as out:
            shutil.copyfileobj(inp, out)
        if digest(source) != digest(dest):
            raise ValueError("Copy integrity failure")
    evidence = {
        "status": "PASS",
        "candidate": candidate,
        "docx": ref(target),
        "pdf_qa": ref(pdf_target),
        "structure": result,
        "tests": {
            "python": count,
            "ui": ui_count,
            "xml": ref(tests),
            "coverage": ref(coverage),
            "combined_percent": cov["totals"]["percent_covered"],
        },
        "manual_visual_review": {
            "pages": len(rows),
            "scope": "Every final page individually inspected, or exact PNG-identical carry from an inspected page",
        },
        "preservation": ref(ROOT / "artifacts/manifests/phase35/preserve_after.json"),
        "parent_locks": preservation["locks"],
        "runtime": ref(ROOT / "artifacts/manifests/phase35/runtime_ready.json"),
        "gpu_environment_modified": False,
        "models_retrained": 0,
        "historical_test_evaluation_executed": False,
        "cloud_deployed": False,
        "production_smoke": "Frozen CPU bundle on local Linux ext4, existing pinned environment, not a fresh CPU-only install or Render deployment",
        "handoff": [ref(p) for p in required_docs],
    }
    write_once_json(ROOT / "releases/v3/release_manifest.json", evidence)
    paths = set(
        required_docs + [target, pdf_target, ROOT / "releases/v3/release_manifest.json", tests, coverage]
    )
    for pattern in [
        "docs/phase35*.md",
        "scripts/phase35*.py",
        "scripts/run_docs_v3.*",
        "scripts/check_word_phase35.ps1",
        "scripts/check_phase35.ps1",
        "scripts/preserve_phase35.ps1",
        "scripts/render_svg_phase35.mjs",
        "scripts/phase35*.sh",
        "tests/report35/*.py",
        "experiments/environment/docs35/*",
        "report/phase35/**/*",
        "artifacts/manifests/phase35/**/*",
        "report/tools/documents_vendor_26_1020/**/*",
    ]:
        paths.update(
            p
            for p in ROOT.glob(pattern)
            if p.is_file()
            and p.suffix not in {".pyc"}
            and p.name not in {"checkpoint.json", "release_lock.json", "verification.json"}
        )
    paths.update(ROOT / r["path"] for r in rows)
    paths.update(
        [
            ROOT / "report/qa35" / candidate / "inspection.json",
            ROOT / "report/qa35" / candidate / "page_map.json",
            ROOT / "report/build/phase35" / (candidate + ".build.json"),
        ]
    )
    write_once_json(
        ROOT / "artifacts/manifests/phase35/release_lock.json",
        {
            "files": [ref(p) for p in sorted(paths)],
            "parent_locks": preservation["locks"],
            "scope": "Phase35 publication, evidence and source closure; prior scientific releases remain read-only",
        },
    )
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["audit", "helpers", "release", "verify"], required=True)
    parser.add_argument("--candidate", default="candidate-r12")
    parser.add_argument("--tests", default="artifacts/manifests/phase35/final_tests_r2.xml")
    parser.add_argument("--coverage", default="artifacts/manifests/phase35/final_coverage_r2.json")
    args = parser.parse_args()
    if args.stage == "audit":
        result = audit(args.candidate)
        write_once_json(
            ROOT / "artifacts/manifests/phase35" / ("structure_" + args.candidate + ".json"), result
        )
        print(
            json.dumps(
                {
                    k: result[k]
                    for k in [
                        "status",
                        "pages",
                        "tables",
                        "figures",
                        "captions",
                        "bookmarks",
                        "page_cache_targets",
                    ]
                }
            )
        )
    elif args.stage == "helpers":
        result = vendor_audits(args.candidate)
        print(json.dumps({"status": result["status"], "helper_count": len(result["reports"])}))
    elif args.stage == "release":
        result = release(args.candidate, ROOT / args.tests, ROOT / args.coverage)
        print(
            json.dumps(
                {"status": result["status"], "docx": result["docx"], "pages": result["structure"]["pages"]}
            )
        )
    else:
        lock = json.loads((ROOT / "artifacts/manifests/phase35/release_lock.json").read_text())
        for row in lock["files"] + lock["parent_locks"]:
            check_file(row)
        print(json.dumps({"status": "PASS", "files": len(lock["files"]), "mode": "read_only_no_inference"}))


if __name__ == "__main__":
    main()
