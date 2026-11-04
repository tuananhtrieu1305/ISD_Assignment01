"""Derive deterministic TOC/figure/table page numbers from artifact-tool layout."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u00a0", " ").replace("\t", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s*([:;,.])\s*", r"\1", text)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-log", required=True, type=Path)
    parser.add_argument("--layout", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    build_log = json.loads(args.build_log.read_text(encoding="utf-8"))
    layout = json.loads(args.layout.read_text(encoding="utf-8"))
    fragments = layout["fragments"]
    normalized_fragments = [
        (normalize(item["text"]), int(item["pageIndex"]) + 1, item)
        for item in fragments
    ]

    page_map: dict[str, int] = {}
    missing: list[dict[str, str]] = []
    for target in build_log["navigation_targets"]:
        wanted = normalize(target["display"])
        exact = [page for text, page, _ in normalized_fragments if text == wanted]
        if exact:
            page_map[target["bookmark"]] = max(exact)
            continue
        prefix = [
            page
            for text, page, _ in normalized_fragments
            if text.startswith(wanted) and len(text) <= len(wanted) + 8
        ]
        if prefix:
            page_map[target["bookmark"]] = max(prefix)
        else:
            missing.append({"bookmark": target["bookmark"], "display": target["display"]})

    payload = {
        "schema_version": 1,
        "source_docx": layout["inputPath"],
        "page_count": layout["pageCount"],
        "resolved_count": len(page_map),
        "target_count": len(build_log["navigation_targets"]),
        "missing": missing,
        "pages": page_map,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Resolved {len(page_map)}/{len(build_log['navigation_targets'])} navigation targets "
        f"across {layout['pageCount']} pages."
    )
    if missing:
        for item in missing:
            print(f"MISSING: {item['bookmark']} -> {item['display']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
