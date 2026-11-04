"""Synthetic tests for manuscript assembly; never construct models or open TEST."""

import pytest

from scripts.phase34_editor import (
    bibliography_entries,
    caption_tables,
    convert_citations,
    markdown_blocks,
    rebase_images,
    safe_path,
    section_replace,
)


def test_headings_inside_code_are_not_sections():
    text = "# Title\n\n## 2.1. One\n```python\n# comment\n## not a section\n```\n\n## 2.2. Two\n"
    assert [b["text"] for b in markdown_blocks(text) if b["kind"] == "heading"] == [
        "# Title",
        "## 2.1. One",
        "## 2.2. Two",
    ]


def test_unclosed_fence_fails():
    with pytest.raises(ValueError, match="fence"):
        markdown_blocks("```python\nx=1\n")


def test_replace_section_only_not_code_comment():
    text = "# T\n\n## 2.1. Before\n```python\n## 2.2. Fake\n```\n\n## 2.2. Deploy\nold\n\n## 2.3. End\nkeep\n"
    value = section_replace(text, "2.2.", "## 2.2. Deploy\nnew\n")
    assert "old" not in value and "new" in value and "## 2.2. Fake" in value and "keep" in value


def test_missing_section_fails():
    with pytest.raises(ValueError, match="section"):
        section_replace("# T\n", "2.2.", "new")


def test_safe_paths_reject_escape_and_missing(tmp_path):
    (tmp_path / "a").write_text("x")
    assert safe_path(tmp_path, "a") == tmp_path / "a"
    with pytest.raises(ValueError):
        safe_path(tmp_path, "../escape")
    with pytest.raises(ValueError):
        safe_path(tmp_path, "missing")


def test_safe_paths_reject_absolute(tmp_path):
    with pytest.raises(ValueError):
        safe_path(tmp_path, str(tmp_path / "outside"))


def test_images_rebased_without_changing_alt(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    target = tmp_path / "out"
    target.mkdir()
    (tmp_path / "a.png").write_bytes(b"png")
    value, images = rebase_images("![Hình 1.1. a](../a.png)", source / "a.md", target / "b.md", tmp_path)
    assert value == "![Hình 1.1. a](../a.png)"
    assert images == [tmp_path / "a.png"]


def test_remote_image_rejected(tmp_path):
    with pytest.raises(ValueError):
        rebase_images("![a](https://invalid.test/a.png)", tmp_path / "a.md", tmp_path / "b.md", tmp_path)


def test_tables_captioned_in_order_code_untouched():
    text = "# T\n\n## 3.1. Data\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n```\n| not a table |\n```\n"
    output, tables = caption_tables(text, 3)
    assert "Bảng 3.1." in output and len(tables) == 1
    assert tables[0]["markdown"] == "| a | b |\n|---|---|\n| 1 | 2 |"
    assert "```\n| not a table |\n```" in output


def test_bib_nested_braces_and_duplicates():
    parsed = bibliography_entries("@article{a, title={A {nested} title}, year={2000}}\n@misc{b, title={B}}")
    assert list(parsed) == ["a", "b"]
    assert "nested" in parsed["a"]
    with pytest.raises(ValueError, match="Duplicate"):
        bibliography_entries("@misc{a,title={A}}\n@misc{a,title={B}}")


def test_bib_broken_fails():
    with pytest.raises(ValueError):
        bibliography_entries("@misc{a,title={A}")


def test_citations_numbered_first_appearance_and_multi():
    registry = {}
    text = convert_citations("A [@b; @a]. B [@b].", {"a": "a", "b": "b"}, registry)
    assert text == "A [1, 2]. B [1]." and registry == {"b": 1, "a": 2}


def test_missing_citation_fails():
    with pytest.raises(ValueError, match="citation"):
        convert_citations("[@missing]", {}, {})


def test_no_citation_replacement_inside_code():
    assert convert_citations("```\n[@x]\n```\n", {}, {}) == "```\n[@x]\n```\n"


def test_contract_counts_learned_layers_not_activation():
    from scripts.build_phase34 import contract_counts

    assert contract_counts(
        {"layers": [{"parameter_count": 3}, {"parameter_count": 0}], "parameter_count": 3}
    ) == (1, 3)
    with pytest.raises(ValueError, match="count"):
        contract_counts({"layers": [{"parameter_count": 3}], "parameter_count": 4})


def test_local_links_rebased_for_single_file(tmp_path):
    from scripts.phase34_editor import rebase_links

    source = tmp_path / "sections"
    source.mkdir()
    (tmp_path / "card.md").write_text("x")
    text = "[card](../card.md) [source](https://example.test/)"
    assert (
        rebase_links(text, source / "a.md", tmp_path / "b.md", tmp_path)
        == "[card](card.md) [source](https://example.test/)"
    )


def test_figure_ledger_uses_numbered_caption():
    from scripts.phase34_editor import figure_captions

    assert figure_captions("![a](../a.png)\n\n**Hình 2.1. Caption.**\n")[0]["label"] == "Hình 2.1."
    with pytest.raises(ValueError, match="caption"):
        figure_captions("![a](a.png)\n")


def test_excerpt_is_exact_source_without_import(tmp_path):
    from scripts.phase34_editor import source_excerpt

    path = tmp_path / "x.py"
    path.write_text("class A:\n    def f(self):\n        return 1\n")
    assert source_excerpt(path, "A", "f") == ("    def f(self):\n        return 1", 2, 3)
    with pytest.raises(ValueError, match="excerpt"):
        source_excerpt(path, "A", "missing")
