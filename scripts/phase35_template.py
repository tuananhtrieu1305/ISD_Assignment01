"""Read-only package, style and story inventory for the retained A06 template."""

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from scripts.phase35_runtime import BASE, ROOT, digest, write_once_json

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}
W = "{" + NS["w"] + "}"


def parse_story(data, part):
    root = ET.fromstring(data)
    paragraphs, fonts = [], Counter()
    for index, p in enumerate(root.findall(".//w:p", NS)):
        style = p.find("w:pPr/w:pStyle", NS)
        paragraphs.append(
            {
                "locator": f"{part}::paragraph[{index + 1}]",
                "style": style.get(W + "val") if style is not None else "Normal",
                "text": "".join(p.itertext())
                if p.find(".//w:t", NS) is None
                else "".join(t.text or "" for t in p.findall(".//w:t", NS)),
                "properties": ET.tostring(p.find("w:pPr", NS), encoding="unicode")
                if p.find("w:pPr", NS) is not None
                else "",
                "direct_run_properties": [
                    ET.tostring(r, encoding="unicode") for r in p.findall("w:r/w:rPr", NS)
                ],
            }
        )
        for font in p.findall("w:r/w:rPr/w:rFonts", NS):
            for name in set(font.get(W + key) for key in ["ascii", "hAnsi", "eastAsia", "cs"]):
                if name:
                    fonts[name] += 1
    fields = [x.get(W + "instr", "").strip() for x in root.findall(".//w:fldSimple", NS)]
    fields += [x.text.strip() for x in root.findall(".//w:instrText", NS) if x.text]
    tables = root.findall(".//w:tbl", NS)
    return {
        "paragraphs": paragraphs,
        "direct_fonts": dict(fonts),
        "tables": len(tables),
        "table_patterns": [
            {
                "locator": f"{part}::table[{i + 1}]",
                "properties": ET.tostring(t.find("w:tblPr", NS), encoding="unicode")
                if t.find("w:tblPr", NS) is not None
                else "",
                "grid": ET.tostring(t.find("w:tblGrid", NS), encoding="unicode")
                if t.find("w:tblGrid", NS) is not None
                else "",
                "rows": len(t.findall("w:tr", NS)),
                "columns": max((len(r.findall("w:tc", NS)) for r in t.findall("w:tr", NS)), default=0),
            }
            for i, t in enumerate(tables)
        ],
        "fields": fields,
        "math": len(root.findall(".//m:oMath", NS)),
        "content_controls": len(root.findall(".//w:sdt", NS)),
        "drawings": len(root.findall(".//w:drawing", NS)),
        "text_boxes": len(root.findall(".//w:txbxContent", NS)),
        "bookmarks": [x.get(W + "name") for x in root.findall(".//w:bookmarkStart", NS)],
    }


def inspect_template(path):
    path = Path(path)
    stories, parts = {}, []
    editable = {
        "word/document.xml",
        "word/_rels/document.xml.rels",
        "word/settings.xml",
        "[Content_Types].xml",
        "docProps/core.xml",
        "docProps/app.xml",
    }
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if (
            len({p.filename for p in members}) != len(members)
            or sum(p.file_size for p in members) > 100 * 1024 * 1024
        ):
            raise ValueError("Duplicate or oversized package")
        for part in members:
            name = part.filename
            if name.startswith("/") or ".." in Path(name).parts or "\\" in name:
                raise ValueError("Unsafe package member")
            data = archive.read(name)
            parts.append(
                {
                    "path": name,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "preserve_only": name not in editable,
                }
            )
            if (
                name.startswith("word/")
                and name.endswith(".xml")
                and any(
                    k in name
                    for k in ["document.xml", "header", "footer", "footnotes", "endnotes", "comments"]
                )
            ):
                stories[name] = parse_story(data, name)
        document = ET.fromstring(archive.read("word/document.xml"))
        style_root = ET.fromstring(archive.read("word/styles.xml"))
        styles = []
        for style in style_root.findall("w:style", NS):
            name = style.find("w:name", NS)
            styles.append(
                {
                    "id": style.get(W + "styleId"),
                    "name": name.get(W + "val") if name is not None else "",
                    "type": style.get(W + "type"),
                    "xml": ET.tostring(style, encoding="unicode"),
                }
            )
        sections = [ET.tostring(x, encoding="unicode") for x in document.findall(".//w:sectPr", NS)]
    return {
        "source": {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)},
        "sections": sections,
        "styles": styles,
        "stories": stories,
        "package_parts": parts,
        "scope": "Read-only package evidence; rendered reference review remains a separate gate",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="releases/v2/references/A06_Assignment_Report.docx")
    args = parser.parse_args()
    inventory = inspect_template(ROOT / args.source)
    write_once_json(BASE.parent / "template_inventory.json", inventory)
    print(
        {
            "parts": len(inventory["package_parts"]),
            "stories": list(inventory["stories"]),
            "sections": len(inventory["sections"]),
        }
    )
    print("Direct fonts:", inventory["stories"]["word/document.xml"]["direct_fonts"])
    print("Styles:", [(s["id"], s["name"]) for s in inventory["styles"]])
    print(
        "Opening paragraphs:",
        [(p["style"], p["text"]) for p in inventory["stories"]["word/document.xml"]["paragraphs"][:16]],
    )


if __name__ == "__main__":
    main()
