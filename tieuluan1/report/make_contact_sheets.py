"""Create labeled contact sheets for internal visual QA of rendered DOCX pages."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def page_number(path: Path) -> int:
    match = re.search(r"page-(\d+)\.png$", path.name)
    return int(match.group(1)) if match else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--columns", type=int, default=3)
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--thumb-width", type=int, default=480)
    args = parser.parse_args()

    pages = sorted(args.input_dir.glob("page-*.png"), key=page_number)
    if not pages:
        raise SystemExit(f"No page PNGs in {args.input_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    first = Image.open(pages[0])
    ratio = first.height / first.width
    thumb_height = round(args.thumb_width * ratio)
    label_height = 34
    sheet_width = args.columns * args.thumb_width
    sheet_height = args.rows * (thumb_height + label_height)
    per_sheet = args.columns * args.rows
    font = ImageFont.load_default(size=20)

    for sheet_index in range(math.ceil(len(pages) / per_sheet)):
        sheet = Image.new("RGB", (sheet_width, sheet_height), "#D8DEE5")
        draw = ImageDraw.Draw(sheet)
        chunk = pages[sheet_index * per_sheet : (sheet_index + 1) * per_sheet]
        for item_index, path in enumerate(chunk):
            row, column = divmod(item_index, args.columns)
            x = column * args.thumb_width
            y = row * (thumb_height + label_height)
            with Image.open(path) as page:
                thumb = page.convert("RGB").resize((args.thumb_width, thumb_height), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (x, y + label_height))
            draw.rectangle((x, y, x + args.thumb_width, y + label_height), fill="#17365D")
            draw.text((x + 10, y + 6), f"Trang {page_number(path)}", fill="white", font=font)
        output = args.output_dir / f"contact-{sheet_index + 1:02d}.png"
        sheet.save(output, optimize=True)
    print(f"Created {math.ceil(len(pages) / per_sheet)} contact sheets for {len(pages)} pages.")


if __name__ == "__main__":
    main()
