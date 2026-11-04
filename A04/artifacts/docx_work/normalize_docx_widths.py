from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def normalize_float_attributes(src: Path, dst: Path) -> None:
    float_attribute = re.compile(rb'([A-Za-z0-9_:\-.]+=")(\d+\.\d+)(")')

    def as_integer(match: re.Match[bytes]) -> bytes:
        prefix, value, suffix = match.groups()
        if prefix.lower() == b'version="':
            return match.group(0)
        rounded = str(round(float(value.decode("ascii")))).encode("ascii")
        return prefix + rounded + suffix

    with ZipFile(src, "r") as zin, ZipFile(dst, "w", ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename.endswith(".xml"):
                data = float_attribute.sub(as_integer, data)
                if info.filename.startswith("word/"):
                    data = strip_change_nodes(data)
            zout.writestr(info, data)


def strip_change_nodes(data: bytes) -> bytes:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return data

    def walk(parent: ET.Element) -> None:
        for child in list(parent):
            local_name = child.tag.rsplit("}", 1)[-1]
            if local_name.endswith("Change"):
                parent.remove(child)
            else:
                walk(child)

    walk(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    normalize_float_attributes(Path(sys.argv[1]), Path(sys.argv[2]))
