from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = f"{{{NS['w']}}}"


def text_of(el: ET.Element) -> str:
    return "".join(t.text or "" for t in el.findall(".//w:t", NS)).strip()


def has_page_break(el: ET.Element) -> bool:
    for br in el.findall(".//w:br", NS):
        if br.get(W + "type") == "page":
            return True
    return False


def main(path: str):
    with ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    body = root.find("w:body", NS)
    children = list(body)
    for index, child in enumerate(children):
        if child.tag != W + "p" or not has_page_break(child):
            continue
        prev_text = ""
        next_text = ""
        for prev in reversed(children[:index]):
            prev_text = text_of(prev)
            if prev_text:
                break
        for nxt in children[index + 1 :]:
            next_text = text_of(nxt)
            if next_text:
                break
        own_text = text_of(child)
        print(f"{index:04d} page-break own={own_text[:100]!r} prev={prev_text[:100]!r} next={next_text[:100]!r}")


if __name__ == "__main__":
    main(sys.argv[1])
