"""Builder contract tests, with synthetic inputs only; no model inference."""

from pathlib import Path
import pytest
from lxml import etree as E
from scripts.phase35_docx import (
    W,
    NS,
    normalize_bibliography,
    column_widths,
    bookmark_name,
    resolve_asset,
    paragraph,
    field,
    parse_markdown,
    Builder,
    breakable,
)


def test_latex_name_normalization_is_narrow():
    assert normalize_bibliography(r"K\"uttler, L\Lukasz, L\'eon") == "Küttler, LŁukasz, Léon"
    assert normalize_bibliography("accuracy 0.123; C:\\data") == "accuracy 0.123; C:\\data"
    text = Path("report/phase34/sections/08_references.md").read_text(encoding="utf-8")
    clean = normalize_bibliography(text)
    assert "Küttler" in clean and "Jürgen" in clean and "Łukasz" in clean
    assert "K\\" not in clean and "L\\" not in clean
    assert "Vrandečić" in clean and "Krötzsch" in clean and "Büttcher" in clean
    assert "\\" not in clean


@pytest.mark.parametrize("n", [2, 3, 6, 9])
def test_column_widths_exact_budget(n):
    widths = column_widths([[str(i) * (i + 1) for i in range(n)]])
    assert len(widths) == n and sum(widths) == 9638
    assert min(widths) >= 620


def test_bookmark_valid_and_stable():
    assert bookmark_name("Hình 4.10.") == bookmark_name("Hình 4.10.")
    assert len(bookmark_name("a" * 100)) <= 40
    assert bookmark_name("123")[0].isalpha()


def test_long_identifiers_keep_every_original_character():
    text = "src/very_long_identifiers/another_directory/source.py"
    assert breakable(text).replace("\u200b", "") == text
    assert "\u200b" in breakable(text)


def test_asset_cannot_escape_workspace(tmp_path):
    with pytest.raises(ValueError):
        resolve_asset("../../outside.png", tmp_path / "x.md", tmp_path)


def test_xml_escaping_and_native_field():
    p = paragraph("A < B & C")
    p.append(field("PAGE", "1"))
    assert p.find("w:r/w:t", NS).text == "A < B & C"
    assert p.find("w:fldSimple", NS).get(W + "instr") == "PAGE"
    E.fromstring(E.tostring(p))


def test_parse_tables_and_fences():
    tokens = parse_markdown("| A | B |\n|---|---|\n| 1 | 2 |\n\n```python\nx = 1\n```")
    assert sum(t.type == "table_open" for t in tokens) == 1
    assert [t.content for t in tokens if t.type == "fence"] == ["x = 1\n"]


def test_builder_does_not_accept_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        Builder(tmp_path / "absent.docx")


def test_native_table_no_fixed_height():
    builder = Builder(Path("releases/v2/references/A06_Assignment_Report.docx"))
    table = builder.table([["A", "B"], ["one", "two"]])
    assert len(table.findall("w:tr", NS)) == 2
    assert table.find("w:tr/w:trPr/w:tblHeader", NS) is not None
    assert not table.findall(".//w:trHeight", NS)
    assert len(table.findall("w:tr/w:trPr/w:cantSplit", NS)) == 2
    huge = builder.table([["header"], ["x" * 20000]])
    assert huge.findall("w:tr", NS)[1].find("w:trPr/w:cantSplit", NS) is None


def test_math_is_editable_omml():
    builder = Builder(Path("releases/v2/references/A06_Assignment_Report.docx"))
    p = builder.math_paragraph("F = f₃ ∘ f₂ ∘ f₁")
    assert p.find("m:oMathPara/m:oMath/m:r/m:t", NS).text.startswith("F =")


def test_caption_has_bookmark_and_seq_cache():
    builder = Builder(Path("releases/v2/references/A06_Assignment_Report.docx"))
    p = builder.caption("Bảng 2.1. Kết quả", "table")
    assert p.find("w:bookmarkStart", NS) is not None
    assert p.find(".//w:fldSimple", NS).get(W + "instr").startswith("SEQ")
    assert "".join(p.itertext()).find("Kết quả") >= 0
    children = list(p)
    start = next(i for i, x in enumerate(children) if x.tag == W + "bookmarkStart")
    end = next(i for i, x in enumerate(children) if x.tag == W + "bookmarkEnd")
    assert "".join("".join(x.itertext()) for x in children[start + 1 : end]) == "Bảng 2.1"


def test_repeated_appendix_subheadings_have_unique_anchors():
    builder = Builder(Path("releases/v2/references/A06_Assignment_Report.docx"))
    builder.heading("Nguồn, kích cỡ và cấu trúc", 4, True)
    builder.heading("Nguồn, kích cỡ và cấu trúc", 4, True)
    assert len(builder.bookmarks) == 2


def test_real_lstm_composition_is_wrapped_not_clipped():
    builder = Builder(Path("releases/v2/references/A06_Assignment_Report.docx"))
    p = paragraph()
    expression = "F = dense_8 ∘ activation_7 ∘ dense_6 ∘ activation_5 ∘ dense_4 ∘ lstm_3 ∘ lstm_2 ∘ lstm_1"
    builder.inline(p, "`" + expression + "`.")
    assert p.find(".//w:br", NS) is not None
    assert max(map(len, builder.math)) <= 55


def test_publication_metadata_does_not_claim_old_a06_tasks():
    from scripts.phase35_docx import publication_properties

    builder = Builder(Path("releases/v2/references/A06_Assignment_Report.docx"))
    core, app = publication_properties(
        builder.original["docProps/core.xml"], builder.original["docProps/app.xml"], 202
    )
    dc = {"dc": "http://purl.org/dc/elements/1.1/"}
    assert E.fromstring(core).find("dc:creator", dc).text == "Triệu Tuấn Anh"
    assert b"AAPL" not in core and b"Online Retail" not in core
    appxml = E.fromstring(app)
    ap = "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}"
    assert appxml.find(ap + "Pages").text == "202"
    assert appxml.find(ap + "Words") is None


def test_appendix_list_keeps_dataset_and_family_not_only_section_number():
    builder = Builder(Path("releases/v2/references/A06_Assignment_Report.docx"))
    entry = {"text": "Bảng B.1. B.1. ch2_cdc_diabetes / mlp", "key": "Bảng B.1", "anchor": "test"}
    result = builder.index_pages("DANH MỤC BẢNG", [entry], figures=True)
    assert "ch2_cdc_diabetes / mlp" in "".join(result[1].itertext())


def test_svg_fallback_retains_white_cards_not_black_rectangles():
    from PIL import Image
    import json

    root = Path("artifacts/manifests/phase35/timeline_browser_render.json")
    receipt = json.loads(root.read_text())
    with Image.open(receipt["output"]) as img:
        assert img.size == (3200, 2100)
        assert img.convert("RGB").getpixel((160, 470)) == (255, 255, 255)


def test_tensor_dimensions_are_not_bibliographic_hyperlinks():
    builder = Builder(Path("releases/v2/references/A06_Assignment_Report.docx"))
    table = builder.table([["shape"], ["[1]"]])
    assert not table.findall(".//w:hyperlink", NS)
    builder.source = Path("10_appendix_b.md")
    p = paragraph()
    builder.inline(p, "Dense [32] → Dense [16] → đầu ra [1]")
    assert not p.findall(".//w:hyperlink", NS)


def test_ch5_latex_is_presented_as_native_readable_math():
    source = (
        "\\[\n\\operatorname{RRF}(d)=\\sum_j\\frac{w_j}{60+r_j(d)}.\n\\]\n\nRetrieval (k\\in\\{1,3,5,10\\})."
    )
    tokens = parse_markdown(source)
    content = " ".join(t.content for t in tokens if t.type == "inline")
    assert "\\operatorname" not in content and "\\in" not in content
    assert "Σ_j" in content and "k ∈ {1,3,5,10}" in content
    builder = Builder(Path("releases/v2/references/A06_Assignment_Report.docx"))
    p = paragraph()
    builder.inline(p, "`RRF(d) = Σ_j w_j / (60 + r_j(d))`.")
    assert p.find(".//m:oMath", NS) is not None
