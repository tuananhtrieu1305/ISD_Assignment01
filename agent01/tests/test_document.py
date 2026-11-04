"""Final artifact contracts, separate from the V3 report and model tests."""

import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parents[1]
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def test_theory_contains_exactly_six_planned_pages():
    content = json.loads((BASE / "report_content.json").read_text())
    assert len(content["pages"]) == 6
    assert all(page["heading"].startswith(str(index)) for index, page in enumerate(content["pages"], 1))


def test_all_notebook_cells_really_executed_without_errors():
    notebook = json.loads((BASE / "notebooks/Discovering_AI_Agent.ipynb").read_text())
    code = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert len(code) == 9
    assert [cell["execution_count"] for cell in code] == list(range(1, 10))
    assert all(cell["outputs"] for cell in code)
    assert all(output["output_type"] != "error" for cell in code for output in cell["outputs"])
    assert all("from discovering_ai_agent" not in "".join(cell["source"]) for cell in code)


def test_every_screenshot_is_grayscale_and_notebook_text_black():
    manifest = json.loads((BASE / "evidence/screenshot_manifest.json").read_text())
    assert len(manifest) == 9
    for record in manifest:
        assert record["text_color"] == "#000000"
        pixels = np.array(Image.open(BASE / record["path"]).convert("RGB"))
        assert np.array_equal(pixels[:, :, 0], pixels[:, :, 1])
        assert np.array_equal(pixels[:, :, 1], pixels[:, :, 2])


def test_docx_has_black_text_and_nine_real_screenshots():
    path = BASE / "output/DISCOVERING_AI_Agent.docx"
    with zipfile.ZipFile(path) as archive:
        images = [name for name in archive.namelist() if name.startswith("word/media/")]
        assert len(images) == 9
        for name in ["word/document.xml", "word/styles.xml", "word/footer1.xml"]:
            root = ET.fromstring(archive.read(name))
            colors = root.findall(".//" + W + "color")
            assert colors
            assert all(color.get(W + "val") == "000000" for color in colors)
            assert all(not any("theme" in key.lower() for key in color.attrib) for color in colors)
        text = " ".join(ET.fromstring(archive.read("word/document.xml")).itertext())
        assert "87,6%" in text
        assert "24" in text
        assert "TÀI LIỆU THAM KHẢO" in text
        assert "Chương 6" not in text


def test_actual_render_keeps_practice_after_six_theory_pages():
    from pypdf import PdfReader
    pdf = PdfReader(BASE / "qa/final/DISCOVERING_AI_Agent.pdf")
    content = json.loads((BASE / "report_content.json").read_text())
    assert len(pdf.pages) == 14
    for index in range(6):
        text = pdf.pages[index].extract_text()
        assert content["pages"][index]["heading"] in text
        assert "THỰC HÀNH" not in text
    assert "THỰC HÀNH" in pdf.pages[6].extract_text()


def test_final_render_has_no_colored_pixels_or_blank_pages():
    files = sorted((BASE / "qa/final").glob("page-*.png"))
    assert len(files) == 14
    for path in files:
        pixels = np.asarray(Image.open(path).convert("RGB"))
        assert np.array_equal(pixels[:, :, 0], pixels[:, :, 1]), str(path)
        assert np.array_equal(pixels[:, :, 1], pixels[:, :, 2]), str(path)
        assert (pixels[:, :, 0] < 128).sum() > 2000, str(path)
