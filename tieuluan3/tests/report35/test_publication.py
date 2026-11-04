"""Full-source publication checks; builds only, no model imports or inference."""

import json
from pathlib import Path
import zipfile
from lxml import etree as E
import pytest
from docx import Document
from scripts.phase35_docx import (
    Builder,
    ROOT,
    W,
    NS,
    EDITABLE,
    parse_markdown,
    column_widths,
    paragraph,
)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    directory = tmp_path_factory.mktemp("publication")
    builder = Builder()
    manifest = json.loads((ROOT / "artifacts/manifests/phase34/manuscript_manifest.json").read_text())
    output = directory / "synthetic_acceptance.docx"
    evidence = builder.build(manifest, output)
    return builder, output, evidence, manifest


def test_complete_source_native_objects(built):
    _, path, evidence, _ = built
    doc = Document(path)
    assert len(doc.tables) == 144
    assert len(evidence["captions"]) == 180
    assert len(evidence["images"]) == 37
    assert len(doc.sections) == 1
    assert all(x["anchor"] in evidence["bookmarks"] for x in evidence["links"] if x.get("anchor"))


def test_opaque_parts_and_original_style_nodes_unchanged(built):
    builder, _, evidence, _ = built
    assert set(evidence["changed_parts"]) <= EDITABLE
    for part, data in builder.original.items():
        if part not in EDITABLE:
            assert builder.parts[part] == data
    before = E.fromstring(builder.original["word/styles.xml"])
    after = E.fromstring(builder.parts["word/styles.xml"])
    assert len(after) > len(before)
    for index, node in enumerate(before):
        assert E.tostring(node, method="c14n") == E.tostring(after[index], method="c14n")


def test_all_parts_parse_and_ids_unique(built):
    builder, path, _, _ = built
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            if name.endswith((".xml", ".rels")):
                E.fromstring(archive.read(name))
    starts = builder.document.findall(".//w:bookmarkStart", NS)
    ends = builder.document.findall(".//w:bookmarkEnd", NS)
    assert len({n.get(W + "id") for n in starts}) == len(starts) == len(ends)
    rels = builder.relationships
    assert len({n.get("Id") for n in rels}) == len(rels)


def test_all_code_methods_preserved_exact(built):
    builder, _, _, manifest = built
    text_runs = [t.text or "" for t in builder.document.findall(".//w:t", NS)]
    count = 0
    for source in manifest["publication_order"]:
        for token in parse_markdown((ROOT / source).read_text(encoding="utf-8")):
            if token.type in ("fence", "code_block"):
                for line in token.content.rstrip("\n").split("\n"):
                    assert line in text_runs
                    count += 1
    assert count > 150


def test_footer_native_fields_and_cover(built):
    builder, _, _, _ = built
    footer = E.fromstring(builder.parts["word/footer1.xml"])
    assert [x.get(W + "instr") for x in footer.findall(".//w:fldSimple", NS)] == ["PAGE", "NUMPAGES"]
    for f in footer.findall(".//w:fldSimple", NS):
        assert f.find("w:r/w:rPr/w:rFonts", NS).get(W + "ascii") == "Times New Roman"
    text = "".join(builder.document.itertext())
    for value in ["Triệu Tuấn Anh", "B23DCCN053", "D23CTPM01", "Trần Đình Quế", "TIỂU LUẬN MÔN HỌC"]:
        assert value in text
    assert "ASSIGNMENT 06" not in text
    assert len(builder.document.findall(".//m:oMath", NS)) > 5


def test_ragged_and_overwide_tables_rejected():
    with pytest.raises(ValueError):
        column_widths([["one"], ["two", "three"]])
    with pytest.raises(ValueError):
        column_widths([list("abcdefghijklmn")])


def test_duplicate_primary_bookmark_rejected():
    builder = Builder()
    builder.mark(paragraph(), "test", "test")
    with pytest.raises(ValueError):
        builder.mark(paragraph(), "test", "test")
    with pytest.raises(ValueError):
        builder.caption("invalid caption", "table")


def test_branch_inline_lists_math_and_invalid(tmp_path):
    builder = Builder()
    p = paragraph()
    builder.inline(p, "**bold** *italic* `shape` [source](https://example.test/x) [1]\nnext")
    assert p.find(".//w:b", NS) is not None
    assert p.find(".//w:i", NS) is not None
    builder.inline(p, "`F = " + " ∘ ".join(["function_long"] * 10) + "`")
    assert p.find(".//w:br", NS) is not None
    with pytest.raises(ValueError):
        builder.inline(p, "![alt](x.png)")
    source = tmp_path / "unit.md"
    source.write_text("# Unique\n\n1. ordered\n2. next\n\n- bullet\n\n> quote\n\n---\n", encoding="utf-8")
    builder.blocks(source)
    assert any("ordered" in "".join(x.itertext()) for x in builder.body)


def test_all_numeric_table_cells_preserved(built):
    builder, _, _, manifest = built
    all_text = "".join(builder.document.itertext()).replace("\u200b", "")
    sources = [
        ROOT / source
        for source in manifest["publication_order"]
        if Path(source).name not in ["contents.md", "figures_and_tables.md"]
    ]
    for source in sources:
        for token in parse_markdown(source.read_text(encoding="utf-8")):
            if token.type == "inline" and token.level >= 4 and token.content:
                # Pure-number cells retain every decimal, sign and unit, without rounding.
                import re

                if re.fullmatch(r"[-+\d.,% /×±eE]+", token.content):
                    assert token.content in all_text
