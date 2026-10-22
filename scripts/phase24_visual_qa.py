"""Local contact sheets of generated scientific plots, never alter source images."""

import math

from PIL import Image, ImageDraw

from src.common.contracts import ROOT


def main():
    paths = sorted((ROOT / "artifacts/figures/phase24").glob("*.png"))
    output = ROOT / "report/qa_phase24"
    output.mkdir(parents=True, exist_ok=True)
    for page in range(math.ceil(len(paths) / 6)):
        chosen = paths[page * 6 : (page + 1) * 6]
        canvas = Image.new("RGB", (1800, 1600), "#eeeeee")
        draw = ImageDraw.Draw(canvas)
        for i, path in enumerate(chosen):
            with Image.open(path) as raw:
                preview = raw.convert("RGB")
                preview.thumbnail((860, 450))
            x, y = (i % 2) * 900 + 20, (i // 2) * 530 + 30
            draw.text((x, y - 20), path.stem, fill="black")
            canvas.paste(preview, (x, y))
        target = output / f"contact_{page + 1}.png"
        canvas.save(target)
        print(str(target), flush=True)


if __name__ == "__main__":
    main()
