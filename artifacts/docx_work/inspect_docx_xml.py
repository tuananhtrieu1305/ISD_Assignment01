from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = f"{{{NS['w']}}}"


def text_of(el: ET.Element) -> str:
    return "".join(t.text or "" for t in el.findall(".//w:t", NS))


def style_of(p: ET.Element) -> str:
    node = p.find("w:pPr/w:pStyle", NS)
    return node.get(W + "val") if node is not None else ""


def dump_doc(path: str) -> None:
    with ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
        body = root.find("w:body", NS)
        if body is None:
            return
        print("Body children:", len(list(body)))
        for idx, child in enumerate(body):
            if child.tag == W + "p":
                text = text_of(child).strip()
                if text:
                    print(f"{idx:04d} P [{style_of(child)}] {text[:220]}")
            elif child.tag == W + "tbl":
                first = text_of(child).strip().replace("\n", " ")
                rows = child.findall("w:tr", NS)
                print(f"{idx:04d} T rows={len(rows)} text={first[:220]}")

        print("\nStyles:")
        styles = ET.fromstring(zf.read("word/styles.xml"))
        for st in styles.findall("w:style", NS):
            style_id = st.get(W + "styleId")
            style_type = st.get(W + "type")
            name = st.find("w:name", NS)
            name_val = name.get(W + "val") if name is not None else ""
            if style_type == "paragraph" and style_id in {"Normal", "Heading1", "Heading2", "Caption", "TOCText", "TOC1", "TOC2", "ListParagraph"}:
                print(style_type, style_id, name_val, ET.tostring(st, encoding="unicode")[:500])


if __name__ == "__main__":
    dump_doc("artifacts/docx_work/A03_renderable.docx")
