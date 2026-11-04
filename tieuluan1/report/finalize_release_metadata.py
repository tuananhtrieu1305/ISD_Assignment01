#!/usr/bin/env python3
"""Remove internal build metadata while preserving the academic author identity."""

from __future__ import annotations

import argparse
import os
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)
ET.register_namespace("dcterms", "http://purl.org/dc/terms/")
ET.register_namespace("dcmitype", "http://purl.org/dc/dcmitype/")
ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")


def patch_core(xml_bytes: bytes, author: str) -> bytes:
    root = ET.fromstring(xml_bytes)
    creator = root.find("dc:creator", NS)
    if creator is None:
        creator = ET.SubElement(root, f"{{{NS['dc']}}}creator")
    creator.text = author
    modified_by = root.find("cp:lastModifiedBy", NS)
    if modified_by is None:
        modified_by = ET.SubElement(root, f"{{{NS['cp']}}}lastModifiedBy")
    modified_by.text = author
    description = root.find("dc:description", NS)
    if description is not None:
        description.text = None
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def finalize(path: Path, author: str) -> None:
    with zipfile.ZipFile(path, "r") as source:
        entries = [(info, source.read(info.filename)) for info in source.infolist()]
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.stem}_", suffix=".docx", dir=path.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with zipfile.ZipFile(temp_path, "w") as target:
            for info, data in entries:
                if info.filename == "docProps/core.xml":
                    data = patch_core(data, author)
                # Preserve the original compression mode and package metadata.
                target.writestr(info, data)
        with zipfile.ZipFile(temp_path) as check:
            if check.testzip() is not None:
                raise RuntimeError("Release package failed ZIP integrity validation")
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docx", type=Path)
    parser.add_argument("--author", required=True)
    args = parser.parse_args()
    finalize(args.docx.resolve(), args.author)
    print(f"Finalized release metadata: {args.docx}")


if __name__ == "__main__":
    main()
