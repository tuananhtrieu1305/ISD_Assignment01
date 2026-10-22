"""Read-only PDF pagination/geometry diagnostics for Phase35 iterations."""

import argparse
import json
import re
import unicodedata
import fitz
from scripts.phase35_runtime import ROOT, digest, write_once_json


def normalize(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", text)).replace("\u200b", "")


def inspect(pdf, build):
    metadata = json.loads(build.read_text(encoding="utf-8"))
    doc = fitz.open(pdf)
    rows = []
    for index, page in enumerate(doc):
        lines = []
        outside = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                text = "".join(s["text"] for s in line["spans"])
                lines.append(text)
                box = line["bbox"]
                if box[0] < 35 or box[2] > page.rect.width - 35 or box[3] > page.rect.height - 30:
                    outside.append({"bbox": box, "text": text})
        links = []
        for link in page.get_links():
            links.append(
                {k: list(v) if isinstance(v, (fitz.Rect, fitz.Point)) else v for k, v in link.items()}
            )
        rows.append(
            {
                "page": index + 1,
                "text": "\n".join(lines),
                "outside_safe": outside,
                "images": len(page.get_images()),
                "links": links,
            }
        )
    # PDF export resolves our index links; their targets are the authoritative page map.
    target_pages = {}
    indices = [x for x in metadata["links"] if x.get("anchor")]
    # Find by visible text outside front index first; caption/title starts are unique.
    for anchor, data in metadata["bookmarks"].items():
        key = data["text"]
        needle = normalize(key)
        if len(needle) > 150:
            needle = needle[:150]
        hits = [row["page"] for row in rows if needle in normalize(row["text"])]
        if hits:
            target_pages[anchor] = hits[-1]
    # Only the front indices contain title links followed by PAGEREF links.
    # Resolve actual annotation destinations rather than guessing cross-reference occurrences.
    front_end = next((p for _, title, p in doc.get_toc() if title == "MỞ ĐẦU"), 1)
    index_entries = [h for h in metadata["headings"] if h["toc"]] + metadata["captions"]
    for row in rows[: front_end - 1]:
        page = doc[row["page"] - 1]
        textpage = page.get_textpage()
        for link in row["links"]:
            if link["kind"] != 1 or link.get("page", -1) < 0:
                continue
            visible = normalize(page.get_textbox(fitz.Rect(link["from"]), textpage=textpage))
            if len(visible) < 5:
                continue
            candidates = [e for e in index_entries if normalize(e.get("key", "")) == visible]
            if not candidates:
                candidates = [e for e in index_entries if normalize(e["text"]).startswith(visible)]
            if len(candidates) == 1:
                target_pages[candidates[0]["anchor"]] = link["page"] + 1
    report = {
        "pdf": str(pdf.relative_to(ROOT)),
        "sha256": digest(pdf),
        "pages": len(doc),
        "outline": doc.get_toc(),
        "page_map": target_pages,
        "unmapped": [x for x in metadata["bookmarks"] if x not in target_pages],
        "pages_detail": rows,
        "internal_link_inputs": len(indices),
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stem")
    parser.add_argument("--revision", default="")
    args = parser.parse_args()
    directory = ROOT / "report/qa35" / args.stem
    if args.revision and not re.fullmatch(r"r\d+", args.revision):
        raise ValueError("Invalid inspection revision")
    suffix = "-" + args.revision if args.revision else ""
    report = inspect(
        directory / (args.stem + ".pdf"), ROOT / "report/build/phase35" / (args.stem + ".build.json")
    )
    write_once_json(directory / ("inspection" + suffix + ".json"), report)
    write_once_json(directory / ("page_map" + suffix + ".json"), report["page_map"])
    print(
        json.dumps(
            {
                "pages": report["pages"],
                "mapped": len(report["page_map"]),
                "unmapped": report["unmapped"][:8],
                "unsafe_pages": [
                    {"page": r["page"], "n": len(r["outside_safe"]), "example": r["outside_safe"][:1]}
                    for r in report["pages_detail"]
                    if r["outside_safe"]
                ][:12],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
