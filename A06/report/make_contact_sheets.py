"""Create internal QA contact sheets from artifact-tool page renders."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "docx_render_a06_final"
OUTPUT = SOURCE / "contact_sheets"
OUTPUT.mkdir(parents=True, exist_ok=True)

pages = sorted(SOURCE.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
thumb_w, thumb_h = 430, 608
label_h, gap = 28, 18
cols, rows = 4, 4
sheet_w = cols * (thumb_w + gap) + gap
sheet_h = rows * (thumb_h + label_h + gap) + gap
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)

for sheet_index in range((len(pages) + cols * rows - 1) // (cols * rows)):
    canvas = Image.new("RGB", (sheet_w, sheet_h), "#E8EDF2")
    draw = ImageDraw.Draw(canvas)
    chunk = pages[sheet_index * cols * rows:(sheet_index + 1) * cols * rows]
    for idx, path in enumerate(chunk):
        row, col = divmod(idx, cols)
        x = gap + col * (thumb_w + gap)
        y = gap + row * (thumb_h + label_h + gap)
        with Image.open(path) as image:
            image = image.convert("RGB")
            image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            canvas.paste(image, (x + (thumb_w - image.width) // 2, y))
        page_no = int(path.stem.split("-")[-1])
        draw.text((x + 6, y + thumb_h + 4), f"page-{page_no}", fill="#17365D", font=font)
    canvas.save(OUTPUT / f"contact_sheet_{sheet_index + 1:02d}.png", quality=95)

print(f"Created {len(list(OUTPUT.glob('contact_sheet_*.png')))} contact sheets for {len(pages)} pages")
