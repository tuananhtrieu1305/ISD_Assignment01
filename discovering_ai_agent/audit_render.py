"""Read actual rendered pages and report pagination; no layout claims from XML alone."""

import argparse
import json
import unicodedata
from pathlib import Path

from pypdf import PdfReader

BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    args = parser.parse_args()
    directory = Path(args.directory)
    reader = PdfReader(directory / "DISCOVERING_AI_Agent.pdf")
    pages = [unicodedata.normalize("NFC", page.extract_text()) for page in reader.pages]
    data = json.loads((BASE / "report_content.json").read_text())
    starts = []
    for theory in data["pages"]:
        positions = [index + 1 for index, text in enumerate(pages) if theory["heading"] in text]
        starts.append({"heading": theory["heading"], "pages": positions})
    result = {"page_count": len(pages), "theory_headings": starts,
              "practice_pages": [index + 1 for index, text in enumerate(pages) if "PHẦN THỰC HÀNH" in text],
              "pages": [{"page": index + 1, "text_characters": len(text), "beginning": text[:150],
                         "ending": text[-150:]} for index, text in enumerate(pages)]}
    (directory / "pagination.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
