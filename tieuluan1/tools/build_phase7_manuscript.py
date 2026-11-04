"""Build the traceable Phase 7 manuscript from reviewed section sources."""

from __future__ import annotations

import hashlib
import csv
import json
import re
import shutil
import struct
from datetime import date
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
TERM_ROOT = WORKSPACE / "term_paper"
REPORT_ROOT = TERM_ROOT / "report"
BIB_PATH = TERM_ROOT / "sources" / "bibliography.bib"
DATASET_REGISTRY_PATH = TERM_ROOT / "sources" / "source_registry.csv"
MANUSCRIPT_PATH = REPORT_ROOT / "manuscript.md"
REFERENCES_PATH = REPORT_ROOT / "references_ordered.md"
MANIFEST_PATH = REPORT_ROOT / "report_manifest.json"

SECTION_PATHS = [
    REPORT_ROOT / "front_matter.md",
    REPORT_ROOT / "sections" / "00_mo_dau.md",
    REPORT_ROOT / "sections" / "01_lich_su_ai.md",
    REPORT_ROOT / "sections" / "02_ml_co_ban.md",
    REPORT_ROOT / "sections" / "03_cnn.md",
    REPORT_ROOT / "sections" / "04_rnn.md",
    REPORT_ROOT / "sections" / "05_trien_khai.md",
    REPORT_ROOT / "sections" / "06_ket_luan.md",
]

FIGURE_SOURCES = {
    "ch2": TERM_ROOT / "artifacts" / "figures" / "ch2",
    "ch3": TERM_ROOT / "artifacts" / "figures" / "ch3",
    "ch4": TERM_ROOT / "artifacts" / "figures" / "ch4",
}

TABLE_EVIDENCE = {
    "2.1": ["term_paper/artifacts/metrics/ch2_dataset_summary.csv"],
    "2.2": ["term_paper/artifacts/manifests/ch2"],
    "2.3": ["term_paper/src/scratch/mlp.py", "term_paper/src/keras_impl/mlp.py", "term_paper/src/pytorch_impl/mlp.py"],
    "2.4": ["term_paper/artifacts/metrics/ch2_framework_summary.csv"],
    "2.5": ["term_paper/artifacts/metrics/ch2_best_vs_classical.csv"],
    "3.1": ["term_paper/artifacts/metrics/ch3_dataset_summary.csv"],
    "3.2": ["term_paper/config/ch3_experiment.json"],
    "3.3": ["term_paper/src/scratch/cnn.py", "term_paper/src/keras_impl/cnn.py", "term_paper/src/pytorch_impl/cnn.py"],
    "3.4": ["term_paper/artifacts/metrics/ch3_framework_summary.csv"],
    "3.5": ["term_paper/artifacts/metrics/ch3_a05_architecture_ablation.csv"],
    "4.1": ["term_paper/artifacts/metrics/ch4_dataset_summary.csv"],
    "4.2": ["term_paper/config/ch4_experiment.json"],
    "4.3": ["term_paper/artifacts/metrics/ch4_framework_summary.csv"],
    "4.4": ["term_paper/artifacts/metrics/ch4_framework_summary.csv"],
    "4.5": ["term_paper/artifacts/metrics/ch4_framework_comparison.csv"],
    "K.1": [
        "term_paper/artifacts/metrics/ch2_framework_summary.csv",
        "term_paper/artifacts/metrics/ch2_best_vs_classical.csv",
        "term_paper/artifacts/metrics/ch3_framework_summary.csv",
        "term_paper/artifacts/metrics/ch3_a05_architecture_ablation.csv",
        "term_paper/artifacts/metrics/ch4_framework_summary.csv",
    ],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def word_count(text: str) -> int:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"https?://\S+", " ", text)
    return len(re.findall(r"(?u)\b[\wÀ-ỹ]+\b", text))


def parse_bibtex(text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    start_pattern = re.compile(r"@(\w+)\{([^,]+),")
    position = 0
    while match := start_pattern.search(text, position):
        depth = 1
        index = match.end()
        while index < len(text) and depth:
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
            index += 1
        if depth:
            raise ValueError(f"Unclosed BibTeX entry: {match.group(2)}")
        block = text[match.end() : index - 1]
        fields: dict[str, str] = {"entry_type": match.group(1)}
        for line in block.splitlines():
            field_match = re.match(r"\s*([A-Za-z]+)\s*=\s*\{(.*)\}\s*,?\s*$", line)
            if field_match:
                fields[field_match.group(1).lower()] = field_match.group(2).strip()
        entries[match.group(2)] = fields
        position = index
    return entries


def clean_latex(value: str) -> str:
    replacements = {
        r"{\'e}": "é",
        r'{\"u}': "ü",
        r"{\L}": "Ł",
        "--": "–",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value.replace("{", "").replace("}", "")


def format_reference(number: int, entry: dict[str, str]) -> str:
    author = clean_latex(entry.get("author", "Không rõ tác giả")).replace(" and ", ", ")
    year = clean_latex(entry.get("year", "không rõ năm"))
    title = clean_latex(entry.get("title", "Không có tiêu đề"))
    venue = clean_latex(
        entry.get("journal")
        or entry.get("booktitle")
        or entry.get("publisher")
        or entry.get("institution")
        or ""
    )
    details: list[str] = []
    if venue:
        details.append(f"*{venue}*")
    volume = clean_latex(entry.get("volume", ""))
    issue = clean_latex(entry.get("number", ""))
    if volume:
        details.append(f"vol. {volume}" + (f", no. {issue}" if issue else ""))
    pages = clean_latex(entry.get("pages", ""))
    if pages:
        details.append(f"pp. {pages}")
    doi = entry.get("doi")
    url = entry.get("url")
    if doi:
        details.append(f"https://doi.org/{doi}")
    elif url:
        details.append(url)
    accessed = entry.get("urldate")
    if accessed and url and not doi:
        details.append(f"truy cập {accessed}")
    suffix = ", ".join(details)
    return f"[{number}] {author} ({year}), “{title}”" + (f", {suffix}." if suffix else ".")


def replace_citations(text: str, bib_entries: dict[str, dict[str, str]]) -> tuple[str, list[str]]:
    order: list[str] = []

    def replace(match: re.Match[str]) -> str:
        keys = re.findall(r"@([A-Za-z0-9_:-]+)", match.group(0))
        numbers: list[int] = []
        for key in keys:
            if key not in bib_entries:
                raise KeyError(f"Citation key missing from bibliography: {key}")
            if key not in order:
                order.append(key)
            numbers.append(order.index(key) + 1)
        return "[" + ", ".join(str(number) for number in numbers) + "]"

    return re.sub(r"\[@[^\]]+\]", replace, text), order


def image_dimensions(path: Path) -> dict[str, object]:
    if path.suffix.lower() == ".png":
        with path.open("rb") as stream:
            header = stream.read(24)
        if header[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"Invalid PNG: {path}")
        width, height = struct.unpack(">II", header[16:24])
        return {"width_px": width, "height_px": height}
    if path.suffix.lower() == ".svg":
        svg = path.read_text(encoding="utf-8")
        viewbox = re.search(r"viewBox=[\"']([^\"']+)", svg)
        return {"viewBox": viewbox.group(1) if viewbox else None}
    return {}


def copy_figure_assets() -> None:
    for chapter, source_dir in FIGURE_SOURCES.items():
        destination = REPORT_ROOT / "assets" / chapter
        destination.mkdir(parents=True, exist_ok=True)
        for source in sorted(source_dir.glob("*.png")):
            shutil.copy2(source, destination / source.name)


def normalize_image_paths(text: str) -> str:
    text = text.replace("../../artifacts/figures/ch2/", "assets/ch2/")
    text = text.replace("../../artifacts/figures/ch3/", "assets/ch3/")
    text = text.replace("../../artifacts/figures/ch4/", "assets/ch4/")
    return text.replace("../assets/", "assets/")


def collect_figures(text: str) -> list[dict[str, object]]:
    lines = text.splitlines()
    figures: list[dict[str, object]] = []
    image_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    for index, line in enumerate(lines):
        match = image_pattern.search(line)
        if not match:
            continue
        alt, relative_path = match.groups()
        nearby = " ".join(lines[index : min(index + 4, len(lines))])
        caption_match = re.search(r"Hình\s+([1-5]\.\d+)\.\**\s*([^\n*]+?)(?:\*|$)", alt + " " + nearby)
        if not caption_match:
            raise ValueError(f"Figure without numbered caption near: {line}")
        number = caption_match.group(1)
        report_path = REPORT_ROOT / relative_path
        if not report_path.is_file():
            raise FileNotFoundError(report_path)
        figures.append(
            {
                "number": number,
                "caption": re.sub(r"\s+", " ", caption_match.group(2)).strip(" ."),
                "path": relative_path.replace("\\", "/"),
                "bytes": report_path.stat().st_size,
                "sha256": sha256(report_path),
                **image_dimensions(report_path),
            }
        )
    return figures


def collect_tables(text: str) -> list[dict[str, object]]:
    tables: list[dict[str, object]] = []
    for number, caption in re.findall(r"\*\*Bảng\s+((?:[2-4]\.\d+)|K\.1)\.\s*([^*]+)\*\*", text):
        evidence = TABLE_EVIDENCE[number]
        for relative in evidence:
            if not (WORKSPACE / relative).exists():
                raise FileNotFoundError(WORKSPACE / relative)
        tables.append({"number": number, "caption": caption.strip(), "source_artifacts": evidence})
    return tables


def main() -> None:
    copy_figure_assets()
    section_texts = [path.read_text(encoding="utf-8").strip() for path in SECTION_PATHS]
    body_with_keys = normalize_image_paths("\n\n<!-- SECTION_BREAK -->\n\n".join(section_texts))
    bib_entries = parse_bibtex(BIB_PATH.read_text(encoding="utf-8"))
    body, citation_order = replace_citations(body_with_keys, bib_entries)

    all_bib_keys = list(bib_entries)
    missing = [key for key in citation_order if key not in bib_entries]
    orphan = [key for key in all_bib_keys if key not in citation_order]
    if missing or orphan:
        raise ValueError(f"Bibliography mismatch: missing={missing}, orphan={orphan}")

    reference_lines = ["# TÀI LIỆU THAM KHẢO"]
    reference_lines.extend(
        format_reference(index, bib_entries[key]) for index, key in enumerate(citation_order, start=1)
    )
    references = "\n\n".join(reference_lines).strip() + "\n"
    REFERENCES_PATH.write_text(references, encoding="utf-8")

    manuscript = body.rstrip() + "\n\n<!-- SECTION_BREAK -->\n\n" + references
    MANUSCRIPT_PATH.write_text(manuscript, encoding="utf-8")

    sections = []
    for path, text in zip(SECTION_PATHS, section_texts):
        headings = re.findall(r"^#{1,3}\s+(.+)$", text, flags=re.MULTILINE)
        sections.append(
            {
                "path": path.relative_to(WORKSPACE).as_posix(),
                "sha256": sha256(path),
                "word_count": word_count(text),
                "headings": headings,
            }
        )

    figures = collect_figures(manuscript)
    tables = collect_tables(manuscript)
    code_lengths = [
        len([line for line in block.strip("\n").splitlines() if line.strip()])
        for block in re.findall(r"```[^\n]*\n(.*?)```", manuscript, flags=re.DOTALL)
    ]
    citation_map = {key: index for index, key in enumerate(citation_order, start=1)}
    with DATASET_REGISTRY_PATH.open(encoding="utf-8", newline="") as stream:
        dataset_rows = list(csv.DictReader(stream))
    datasets = [
        {
            "dataset_id": row["dataset_id"],
            "chapter": int(row["chapter"]),
            "canonical_name": row["canonical_name"],
            "source_url": row["official_or_primary_url"],
            "license_status": row["license_status"],
            "license": row["license"],
            "local_path": row["local_path"],
            "physical_size_bytes": int(row["physical_size_bytes"]),
            "logical_size": row["logical_size"],
            "citation_key": row["citation_key"],
        }
        for row in dataset_rows
    ]
    manifest = {
        "schema_version": 1,
        "phase": 7,
        "generated_on": date.today().isoformat(),
        "manuscript": {
            "path": MANUSCRIPT_PATH.relative_to(WORKSPACE).as_posix(),
            "sha256": sha256(MANUSCRIPT_PATH),
            "bytes": MANUSCRIPT_PATH.stat().st_size,
            "word_count": word_count(manuscript),
        },
        "sections": sections,
        "page_budget": {
            "overall_allowed_range": [59, 69],
            "estimated_total_before_appendices": 65,
            "estimate_status": "IN_BUDGET_PENDING_DOCX_LAYOUT",
            "basis": "section word counts, 18 figures, 16 native-table candidates and 44 references; exact count is deferred to Phase 8 render",
        },
        "citations": {
            "style": "numeric_by_first_appearance",
            "count": len(citation_order),
            "order": citation_order,
            "map": citation_map,
            "missing": missing,
            "orphan": orphan,
            "bibliography_source": BIB_PATH.relative_to(WORKSPACE).as_posix(),
            "ordered_references": REFERENCES_PATH.relative_to(WORKSPACE).as_posix(),
        },
        "figures": figures,
        "tables": tables,
        "datasets": datasets,
        "code_excerpts": {
            "count": len(code_lengths),
            "line_counts": code_lengths,
            "allowed_lines_per_excerpt": [10, 25],
        },
        "experiment_evidence": {
            "matched_runs": {"chapter_2": 27, "chapter_3": 18, "chapter_4": 18, "total": 63},
            "test_prediction_rows": {"chapter_2": 196713, "chapter_3": 14850, "chapter_4": 75690, "total": 287253},
            "seeds": [42, 52, 62],
            "result_split": "TEST",
        },
        "terminology_policy": (REPORT_ROOT / "terminology.md").relative_to(WORKSPACE).as_posix(),
        "cover_metadata": {
            "status": "PENDING_INPUT",
            "allowed_placeholders_only_in_manifest": True,
            "fields": ["school", "faculty", "course", "student_name", "student_id", "class", "instructor", "location"],
        },
        "quality_contract": {
            "content_placeholders_allowed": False,
            "absolute_machine_paths_allowed": False,
            "negative_results_retained": True,
            "all_figures_and_tables_cross_referenced": True,
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Built {MANUSCRIPT_PATH.relative_to(WORKSPACE)}: "
        f"{manifest['manuscript']['word_count']} words, {len(figures)} figures, "
        f"{len(tables)} tables, {len(citation_order)} references."
    )


if __name__ == "__main__":
    main()
