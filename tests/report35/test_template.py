"""Read-only source template inventory contracts."""

import zipfile

import pytest

from scripts.phase35_template import inspect_template, parse_story

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def test_story_includes_table_header_footer_math_and_direct_formatting():
    xml = f'''<w:document xmlns:w="{W}" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
    <w:body><w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman"/></w:rPr><w:t>Title</w:t></w:r></w:p>
    <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Cell</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
    <m:oMath/><w:sdt/><w:bookmarkStart w:id="1" w:name="target"/>
    <w:p><w:fldSimple w:instr="PAGE"/></w:p><w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr>
    </w:body></w:document>'''.encode()
    result = parse_story(xml, "word/document.xml")
    assert [p["text"] for p in result["paragraphs"]] == ["Title", "Cell", ""]
    assert result["paragraphs"][0]["style"] == "Heading1"
    assert result["direct_fonts"] == {"Times New Roman": 1}
    assert result["tables"] == 1
    assert result["math"] == 1
    assert result["content_controls"] == 1
    assert result["fields"] == ["PAGE"]


def test_inspect_real_reference_is_read_only():
    from scripts.phase35_runtime import ROOT, digest

    path = ROOT / "releases/v2/references/A06_Assignment_Report.docx"
    before = digest(path)
    result = inspect_template(path)
    assert result["source"]["sha256"] == before == digest(path)
    assert len(result["sections"]) == 1
    assert any(s["id"] == "Normal" for s in result["styles"])
    assert any(s["id"] == "Heading1" for s in result["styles"])
    assert result["package_parts"]
    assert result["stories"]["word/document.xml"]["paragraphs"]


@pytest.mark.parametrize("name", ["../escape", "/absolute", "a\\b"])
def test_zip_rejects_unsafe_member(tmp_path, name):
    path = tmp_path / "invalid.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(name, b"not a document")
    with pytest.raises(ValueError):
        inspect_template(path)
