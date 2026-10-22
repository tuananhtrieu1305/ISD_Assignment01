"""Tests for the Phase 18 manuscript migration and renumber contract."""

from __future__ import annotations

from pathlib import Path

from term_paper.tools.build_phase18_manuscript import (
    SECTION_FILENAMES,
    estimate_pages,
    main as build_manuscript,
)
from term_paper.tools.verify_phase18 import (
    expected_top_level_order,
    run_verification,
    validate_deployment_distribution,
    validate_heading_sequence,
)


def test_section_order_includes_knowledge_rag_and_excludes_standalone_deploy():
    assert SECTION_FILENAMES == [
        "front_matter.md",
        "00_mo_dau.md",
        "01_lich_su_ai.md",
        "02_ml_co_ban.md",
        "03_cnn.md",
        "04_rnn.md",
        "05_knowledge_rag.md",
        "06_ket_luan.md",
    ]
    assert "05_trien_khai.md" not in SECTION_FILENAMES


def test_page_estimate_is_derived_from_content_counts():
    first = estimate_pages(words=34_000, figures=24, tables=21, references=57)
    second = estimate_pages(words=35_000, figures=24, tables=21, references=57)
    assert 82 <= first <= 90
    assert second > first


def test_heading_sequence_rejects_standalone_deployment():
    headings = expected_top_level_order().copy()
    headings.insert(-2, "PHẦN 5. TRIỂN KHAI MÔ HÌNH")
    failures = validate_heading_sequence(headings)
    assert any("standalone" in failure.lower() for failure in failures)


def test_deployment_distribution_requires_all_four_chapters():
    sections = {
        "02_ml_co_ban.md": "## 2.9. Triển khai minh họa\nhealth hash cảnh báo y khoa",
        "03_cnn.md": "## 3.9. Triển khai minh họa\nPNG JPEG top-3 confidence",
        "04_rnn.md": "## 4.9. Triển khai minh họa\n8 × 5 30 × 5 naive last-Close",
        "05_knowledge_rag.md": "không có deploy",
    }
    failures = validate_deployment_distribution(sections)
    assert any("05_knowledge_rag.md" in failure for failure in failures)


def test_repository_migration_contract_passes():
    workspace = Path(__file__).resolve().parents[2]
    sections_root = workspace / "term_paper/report/sections"
    sections = {
        name: (sections_root / name).read_text(encoding="utf-8")
        for name in ("02_ml_co_ban.md", "03_cnn.md", "04_rnn.md", "05_knowledge_rag.md")
    }
    assert validate_deployment_distribution(sections) == []


def test_repository_builder_and_full_verifier_pass():
    workspace = Path(__file__).resolve().parents[2]
    assert build_manuscript() == 0
    report = run_verification(workspace)
    assert report["status"] == "PASS"
    assert report["checks_passed"] == report["checks_total"] == 15
