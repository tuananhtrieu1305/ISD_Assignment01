from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = f"{{{NS['w']}}}"


def text_of(el: ET.Element) -> str:
    return "".join(t.text or "" for t in el.findall(".//w:t", NS))


def style_of(p: ET.Element) -> str:
    node = p.find("w:pPr/w:pStyle", NS)
    return node.get(W + "val") if node is not None else ""


def analyze(path: str) -> None:
    docx_path = Path(path)
    print(f"\n=== {docx_path} ===")
    with ZipFile(docx_path) as zf:
        names = zf.namelist()
        if "docProps/app.xml" in names:
            app = ET.fromstring(zf.read("docProps/app.xml"))
            app_ns = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            for tag in ["Pages", "Words", "Paragraphs", "Lines"]:
                node = app.find(f"{{{app_ns}}}{tag}")
                print(tag, node.text if node is not None else None)

        xml = zf.read("word/document.xml")
        root = ET.fromstring(xml)
        body = root.find("w:body", NS)
        if body is None:
            return

        paras: list[tuple[str, str]] = []
        table_count = 0
        drawings = 0
        hyperlinks = 0
        for child in body:
            if child.tag == W + "p":
                text = text_of(child).strip()
                if child.findall(".//w:drawing", NS) or child.findall(".//w:pict", NS):
                    drawings += 1
                hyperlinks += len(child.findall(".//w:hyperlink", NS))
                if text:
                    paras.append((style_of(child), re.sub(r"\s+", " ", text)))
            elif child.tag == W + "tbl":
                table_count += 1

        print("document.xml bytes", len(xml), "100.0 count", xml.count(b"100.0"))
        print("paragraphs with text", len(paras), "tables", table_count, "drawings", drawings, "hyperlinks", hyperlinks)
        print("media files", len([name for name in names if name.startswith("word/media/")]))

        print("Headings / lists / links:")
        for style, text in paras:
            if style or re.match(
                r"^(Mục lục|Danh sách|CHƯƠNG|KẾT LUẬN|PHỤ LỤC|[0-9]+\.[0-9]+\.|GitHub|Notebook)",
                text,
                re.I,
            ):
                print(f"  [{style}] {text[:220]}")

        print("First 60 paragraphs:")
        for style, text in paras[:60]:
            print(f"  [{style}] {text[:180]}")


if __name__ == "__main__":
    paths = sys.argv[1:] or ["artifacts/docx_work/A03_CT_anhtt.053_expanded.docx"]
    for item in paths:
        analyze(item)
