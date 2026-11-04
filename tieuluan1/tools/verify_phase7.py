"""Acceptance checks for the Phase 7 manuscript and traceability manifest."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
TERM_ROOT = WORKSPACE / "term_paper"
REPORT_ROOT = TERM_ROOT / "report"
MANUSCRIPT_PATH = REPORT_ROOT / "manuscript.md"
MANIFEST_PATH = REPORT_ROOT / "report_manifest.json"

EXPECTED_H1 = [
    "TÓM TẮT",
    "MỞ ĐẦU",
    "CHƯƠNG 1. LỊCH SỬ PHÁT TRIỂN TRÍ TUỆ NHÂN TẠO",
    "CHƯƠNG 2. CÁC KỸ THUẬT MACHINE LEARNING CƠ BẢN",
    "CHƯƠNG 3. CONVOLUTIONAL NEURAL NETWORK",
    "CHƯƠNG 4. RECURRENT NEURAL NETWORK",
    "PHẦN 5. TRIỂN KHAI MÔ HÌNH",
    "KẾT LUẬN",
    "TÀI LIỆU THAM KHẢO",
]
EXPECTED_FIGURES = {
    "1.1",
    "2.1", "2.2", "2.3", "2.4",
    "3.1", "3.2", "3.3", "3.4", "3.5",
    "4.1", "4.2", "4.3", "4.4", "4.5", "4.6",
    "5.1", "5.2",
}
EXPECTED_TABLES = {
    "2.1", "2.2", "2.3", "2.4", "2.5",
    "3.1", "3.2", "3.3", "3.4", "3.5",
    "4.1", "4.2", "4.3", "4.4", "4.5",
    "K.1",
}
WORD_RANGES = {
    "00_mo_dau.md": (1800, 2600),
    "01_lich_su_ai.md": (3800, 5200),
    "02_ml_co_ban.md": (5200, 7200),
    "03_cnn.md": (4800, 6800),
    "04_rnn.md": (5000, 6800),
    "05_trien_khai.md": (1400, 2800),
    "06_ket_luan.md": (1000, 1900),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition: bool, message: str, failures: list[str]) -> None:
    if condition:
        print(f"PASS: {message}")
    else:
        failures.append(message)
        print(f"FAIL: {message}")


def main() -> None:
    failures: list[str] = []
    check(MANUSCRIPT_PATH.is_file() and MANUSCRIPT_PATH.stat().st_size > 100_000, "manuscript exists and is substantive", failures)
    check(MANIFEST_PATH.is_file(), "report manifest exists", failures)
    if failures:
        raise SystemExit("Phase 7 verification failed: " + "; ".join(failures))

    manuscript = MANUSCRIPT_PATH.read_text(encoding="utf-8")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    headings = re.findall(r"^#\s+(.+)$", manuscript, flags=re.MULTILINE)
    check(headings == EXPECTED_H1, "top-level section order is complete", failures)
    check("[@" not in manuscript, "all Pandoc citation keys were resolved", failures)
    check(not re.search(r"(?i)\b(TODO|TBD|PLACEHOLDER)\b|\[CẦN", manuscript), "no content placeholder remains", failures)
    check(not re.search(r"[A-Za-z]:\\", manuscript), "no absolute Windows path is exposed", failures)
    secret_pattern = r"(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,})"
    check(not re.search(secret_pattern, manuscript), "no common secret token pattern is exposed", failures)

    check(manifest["manuscript"]["sha256"] == sha256(MANUSCRIPT_PATH), "manuscript hash matches manifest", failures)
    estimate = manifest["page_budget"]["estimated_total_before_appendices"]
    low, high = manifest["page_budget"]["overall_allowed_range"]
    check(low <= estimate <= high, "page estimate is within the locked budget", failures)

    citation_data = manifest["citations"]
    refs = re.findall(r"^\[(\d+)\]\s", manuscript, flags=re.MULTILINE)
    check(len(refs) == 44 and refs == [str(i) for i in range(1, 45)], "44 references are sequential", failures)
    check(citation_data["count"] == 44 and not citation_data["missing"] and not citation_data["orphan"], "citation coverage has no missing or orphan entry", failures)
    used_citations = {int(number) for group in re.findall(r"\[((?:\d+(?:,\s*)?)+)\]", manuscript) for number in re.findall(r"\d+", group)}
    check(set(range(1, 45)).issubset(used_citations), "every bibliography item is cited in the body", failures)

    datasets = manifest["datasets"]
    check(len(datasets) == 8 and {item["chapter"] for item in datasets} == {2, 3, 4}, "8 dataset instances cover Chapters 2–4", failures)
    for dataset in datasets:
        check(dataset["source_url"] in manuscript, f"{dataset['dataset_id']} source link is present", failures)
        check(bool(dataset["license_status"] and dataset["license"]), f"{dataset['dataset_id']} license status is explicit", failures)
        check((WORKSPACE / dataset["local_path"]).exists(), f"{dataset['dataset_id']} local provenance exists", failures)

    figure_numbers = {item["number"] for item in manifest["figures"]}
    check(len(manifest["figures"]) == 18 and figure_numbers == EXPECTED_FIGURES, "18 expected figures are packaged", failures)
    for figure in manifest["figures"]:
        path = REPORT_ROOT / figure["path"]
        check(path.is_file() and sha256(path) == figure["sha256"], f"figure {figure['number']} exists and hash matches", failures)
        check(len(re.findall(rf"Hình\s+{re.escape(figure['number'])}(?!\d)", manuscript)) >= 2, f"figure {figure['number']} is cited outside its caption", failures)

    table_numbers = {item["number"] for item in manifest["tables"]}
    check(len(manifest["tables"]) == 16 and table_numbers == EXPECTED_TABLES, "16 expected tables are registered", failures)
    for table in manifest["tables"]:
        check(len(re.findall(rf"Bảng\s+{re.escape(table['number'])}(?!\d)", manuscript)) >= 2, f"table {table['number']} is cited outside its caption", failures)
        check(all((WORKSPACE / source).exists() for source in table["source_artifacts"]), f"table {table['number']} evidence exists", failures)

    code_blocks = re.findall(r"```[^\n]*\n(.*?)```", manuscript, flags=re.DOTALL)
    code_lengths = [len([line for line in block.strip("\n").splitlines() if line.strip()]) for block in code_blocks]
    check(bool(code_lengths) and all(10 <= count <= 25 for count in code_lengths), "all code excerpts contain 10–25 nonblank lines", failures)

    section_by_name = {Path(item["path"]).name: item for item in manifest["sections"]}
    for filename, (minimum, maximum) in WORD_RANGES.items():
        count = section_by_name[filename]["word_count"]
        check(minimum <= count <= maximum, f"{filename} word count {count} is within editorial range", failures)

    check(manuscript.count("Nguồn bảng:") >= 16, "every table has an artifact/source note", failures)
    check(all(term in manuscript for term in ["RQ1", "RQ2", "RQ3"]), "conclusion answers all three research questions", failures)
    negative_markers = ["vẫn dưới logistic regression", "collapse", "naive last-Close chỉ 3,8789"]
    check(all(term in manuscript for term in negative_markers), "negative findings are retained explicitly", failures)
    check(manifest["experiment_evidence"]["matched_runs"]["total"] == 63, "matched-run total is recorded", failures)
    check(manifest["experiment_evidence"]["test_prediction_rows"]["total"] == 287253, "TEST prediction-row total is recorded", failures)

    if failures:
        print(f"\nPhase 7 verification: FAIL ({len(failures)} checks)")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print("\nPhase 7 verification: PASS")


if __name__ == "__main__":
    main()
