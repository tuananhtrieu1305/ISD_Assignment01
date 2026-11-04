from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def p(text: str = "") -> str:
    return (
        '<w:p><w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/></w:pPr>'
        f'<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/></w:rPr><w:t>{text}</w:t></w:r></w:p>'
    )


def cell(text: str, width: int, bold: bool = False) -> str:
    b = "<w:b/><w:bCs/>" if bold else ""
    return (
        f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>'
        '<w:tcMar><w:top w:w="90" w:type="dxa"/><w:left w:w="90" w:type="dxa"/>'
        '<w:bottom w:w="90" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tcMar>'
        '<w:vAlign w:val="center"/></w:tcPr>'
        '<w:p><w:pPr><w:spacing w:after="0" w:line="300" w:lineRule="auto"/></w:pPr>'
        f'<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>{b}</w:rPr><w:t>{text}</w:t></w:r>'
        '</w:p></w:tc>'
    )


def table() -> str:
    widths = [1800, 1800, 2400, 3600]
    rows = [
        ["Ứng dụng", "Metric", "Model", "Kết quả"],
        ["Diabetes", "F1", "Improved DNN", "F1 = 0.771; Recall = 0.926"],
        ["House Price", "RMSE", "Improved DNN", "RMSE = 1.417 tỷ VND; R2 = 0.580"],
    ]
    body = [
        '<w:tbl><w:tblPr><w:tblW w:w="9600" w:type="dxa"/><w:jc w:val="center"/>'
        '<w:tblBorders><w:top w:val="single" w:sz="8" w:color="000000"/>'
        '<w:left w:val="single" w:sz="8" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="8" w:color="000000"/>'
        '<w:right w:val="single" w:sz="8" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="8" w:color="000000"/>'
        '<w:insideV w:val="single" w:sz="8" w:color="000000"/></w:tblBorders>'
        '<w:tblLayout w:type="fixed"/></w:tblPr>',
        "".join(f'<w:gridCol w:w="{w}"/>' for w in widths).join(["<w:tblGrid>", "</w:tblGrid>"]),
    ]
    for r, row in enumerate(rows):
        body.append("<w:tr>")
        for value, width in zip(row, widths):
            body.append(cell(value, width, bold=r == 0))
        body.append("</w:tr>")
    body.append("</w:tbl>")
    return "".join(body)


def make(path: Path) -> None:
    content_types = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''
    doc = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{NS_W}"><w:body>{p("Bảng test")}{table()}
<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1008" w:bottom="1008" w:left="1008" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>
</w:body></w:document>'''
    with ZipFile(path, "w", ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", doc)


make(Path("artifacts/docx_work/table_smoke.docx"))
