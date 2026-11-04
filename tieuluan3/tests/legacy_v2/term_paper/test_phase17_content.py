"""Tests for the Phase 17 Chapter 5 content contract."""

from __future__ import annotations

from pathlib import Path

from term_paper.tools.verify_phase17 import (
    estimate_pages,
    extract_citation_keys,
    run_verification,
    validate_chapter,
)


def sample_chapter() -> str:
    sections = "\n\n".join(
        f"## 5.{number}. Mục {number}\n\nNội dung có dẫn nguồn [@source]."
        for number in range(1, 8)
    )
    return f"""<!-- page_target: 12-15; style: term_paper/config/style_spec.md -->

# CHƯƠNG 5. KNOWLEDGE BASE, KNOWLEDGE GRAPH VÀ RETRIEVAL-AUGMENTED GENERATION

{sections}

**Bảng 5.1. Bảng thử nghiệm**

| Cột | Giá trị |
|---|---:|
| a | 1 |

*Nguồn: artifact nội bộ `metrics.json`.*

![Sơ đồ thử nghiệm](../assets/ch5_knowledge_rag/figure.svg)

**Hình 5.1. Sơ đồ thử nghiệm.**

*Nguồn: tác giả tổng hợp từ artifact nội bộ `metrics.json`.*
"""


def test_extract_citation_keys_is_ordered_and_deduplicated():
    text = "A [@alpha; @beta], B [@alpha]."
    assert extract_citation_keys(text) == ["alpha", "beta"]


def test_estimate_pages_counts_words_and_visuals():
    text = ("từ " * 4800) + "\n" + ("![x](a.png)\n" * 4) + ("**Bảng 5.1. x**\n" * 4)
    estimate = estimate_pages(text)
    assert 11.5 <= estimate <= 13.5


def test_validate_chapter_accepts_complete_contract(tmp_path: Path):
    assets = tmp_path / "assets/ch5_knowledge_rag"
    assets.mkdir(parents=True)
    (assets / "figure.svg").write_text("<svg viewBox='0 0 1 1'></svg>", encoding="utf-8")
    bibliography = "@article{source,\n title={Source},\n year={2026}\n}\n"
    failures, summary = validate_chapter(sample_chapter(), bibliography, tmp_path)
    assert failures == []
    assert summary["figure_count"] == 1
    assert summary["table_count"] == 1


def test_validate_chapter_rejects_missing_numbered_section(tmp_path: Path):
    text = sample_chapter().replace("## 5.4. Mục 4", "## 5.8. Sai mục")
    failures, _ = validate_chapter(text, "@article{source, title={x}}", tmp_path)
    assert any("5.4" in failure for failure in failures)


def test_validate_chapter_rejects_untraceable_visual(tmp_path: Path):
    text = sample_chapter().replace("*Nguồn: tác giả tổng hợp từ artifact nội bộ `metrics.json`.*", "")
    failures, _ = validate_chapter(text, "@article{source, title={x}}", tmp_path)
    assert any("nguồn" in failure.lower() for failure in failures)


def test_validate_chapter_rejects_missing_bibliography_key(tmp_path: Path):
    failures, _ = validate_chapter(sample_chapter(), "", tmp_path)
    assert any("source" in failure for failure in failures)


def test_validate_chapter_rejects_excess_figures_and_tables(tmp_path: Path):
    text = sample_chapter() + "\n" + "\n".join(
        f"![x](../assets/ch5_knowledge_rag/f{i}.svg)\n\n**Hình 5.{i}. x.**\n\n*Nguồn: artifact nội bộ.*"
        for i in range(2, 8)
    )
    text += "\n" + "\n".join(f"**Bảng 5.{i}. x**" for i in range(2, 7))
    failures, _ = validate_chapter(text, "@article{source, title={x}}", tmp_path)
    assert any("6 hình" in failure for failure in failures)
    assert any("5 bảng" in failure for failure in failures)


def test_validate_chapter_rejects_heading_level_four(tmp_path: Path):
    failures, _ = validate_chapter(
        sample_chapter() + "\n#### 5.1.1.1. Không hợp lệ\n",
        "@article{source, title={x}}",
        tmp_path,
    )
    assert any("Heading 4" in failure for failure in failures)


def test_repository_chapter_passes_full_phase17_verification():
    workspace = Path(__file__).resolve().parents[2]
    report = run_verification(workspace)
    assert report["status"] == "PASS"
    assert report["checks_passed"] == report["checks_total"] == 9
    assert 12 <= report["chapter"]["estimated_pages"] <= 15
