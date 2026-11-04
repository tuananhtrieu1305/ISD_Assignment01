"""Template-preserving OOXML publication builder. No scientific computation."""

import argparse
from copy import deepcopy
import hashlib
import io
import json
import math
from pathlib import Path
import re
import zipfile

from lxml import etree as E
from markdown_it import MarkdownIt
from PIL import Image

from scripts.phase35_runtime import ROOT, digest, write_once_json

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
NS = {"w": W[1:-1], "r": R[1:-1], "m": M[1:-1]}
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
EDITABLE = {
    "docProps/core.xml",
    "docProps/app.xml",
    "word/document.xml",
    "word/_rels/document.xml.rels",
    "word/styles.xml",
    "word/settings.xml",
    "word/footer1.xml",
    "[Content_Types].xml",
}
TEMPLATE = ROOT / "releases/v2/references/A06_Assignment_Report.docx"


def el(tag, attrs=None, text=None):
    node = E.Element(W + tag)
    for key, value in (attrs or {}).items():
        node.set(W + key, str(value))
    if text is not None:
        node.text = text
        if tag == "t":
            node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return node


def run(text, *, bold=False, italic=False, code=False, size=None, color=None, font=None):
    node = el("r")
    props = el("rPr")
    if font:
        props.append(el("rFonts", {"ascii": font, "hAnsi": font, "eastAsia": font}))
    if bold:
        props.append(el("b"))
    if italic:
        props.append(el("i"))
    if code:
        props.append(el("rFonts", {"ascii": "Consolas", "hAnsi": "Consolas", "eastAsia": "Consolas"}))
        props.append(el("sz", {"val": size or 21}))
    elif size:
        props.append(el("sz", {"val": size}))
    if color:
        props.append(el("color", {"val": color}))
    if len(props):
        node.append(props)
    node.append(el("t", text=text))
    return node


def paragraph(text="", style=None):
    p = el("p")
    props = el("pPr")
    if style:
        props.append(el("pStyle", {"val": style}))
    p.append(props)
    if text:
        p.append(run(text))
    return p


def field(instruction, cached, **formatting):
    f = el("fldSimple", {"instr": instruction})
    f.append(run(str(cached), **formatting))
    return f


def bookmark_name(text):
    slug = re.sub(r"[^A-Za-z0-9_]", "_", text)
    return "v3_" + slug[:25] + "_" + hashlib.sha256(text.encode()).hexdigest()[:8]


def normalize_bibliography(text):
    replacements = {
        r"K\"uttler": "Küttler",
        r"Rockt\"aschel": "Rocktäschel",
        r"L\'eon": "Léon",
        r"J\"urgen": "Jürgen",
        r"\Lukasz": "Łukasz",
        r"Vrande\vci\'c": "Vrandečić",
        r"Kr\"otzsch": "Krötzsch",
        r"B\"uttcher": "Büttcher",
    }
    for old, new in replacements.items():
        pattern = re.escape(old).replace(r"\\", r"\\+")
        text = re.sub(pattern, lambda _: new, text)
    return text


def resolve_asset(value, source, root=ROOT):
    path = (Path(source).parent / value).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("Asset escapes workspace")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def column_widths(rows, budget=9638):
    n = len(rows[0])
    if not 1 <= n <= 12 or any(len(row) != n for row in rows):
        raise ValueError("Unsupported or ragged table")
    floor = min(800, budget // n)
    weights = [math.sqrt(max(8, min(100, max(len(row[i]) for row in rows)))) for i in range(n)]
    remaining = budget - n * floor
    widths = [floor + int(remaining * x / sum(weights)) for x in weights]
    widths[-1] += budget - sum(widths)
    return widths


def parse_markdown(text):
    # Narrow presentation normalization of the two literal Ch5 math fragments.
    # Keep frozen manuscript bytes intact; do not pretend to parse arbitrary TeX.
    text = text.replace(
        "\\[\n\\operatorname{RRF}(d)=\\sum_j\\frac{w_j}{60+r_j(d)}.\n\\]",
        "`RRF(d) = Σ_j w_j / (60 + r_j(d))`.",
    ).replace(r"k\in\{1,3,5,10\}", "k ∈ {1,3,5,10}")
    return MarkdownIt("commonmark").enable("table").parse(text)


def xml_bytes(node):
    return E.tostring(node, encoding="UTF-8", xml_declaration=True, standalone=True)


def publication_properties(core_data, app_data, pages):
    core = E.fromstring(core_data)
    dc = "http://purl.org/dc/elements/1.1/"
    cp = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
    terms = "http://purl.org/dc/terms/"
    values = {
        "{" + dc + "}title": "Tiểu luận môn học Trí tuệ nhân tạo — sáu chương",
        "{" + dc + "}subject": "AI, ML, CNN, RNN–LSTM, Knowledge Graph–RAG và hệ đa tác tử",
        "{" + dc + "}creator": "Triệu Tuấn Anh",
        "{"
        + dc
        + "}description": "Tiểu luận V3 từ bản thảo và kết quả đã khóa Phase34; không huấn luyện hoặc đánh giá TEST lại trong bước dựng Word.",
        "{" + cp + "}keywords": "AI, scratch, Keras, PyTorch, CNN, RNN, LSTM, KG, RAG, multi-agent",
        "{" + cp + "}lastModifiedBy": "Phase35 OOXML builder",
        "{" + cp + "}revision": "3",
        "{" + terms + "}created": "2026-10-22T00:00:00Z",
        "{" + terms + "}modified": "2026-10-22T00:00:00Z",
    }
    for tag, value in values.items():
        node = core.find(tag)
        if node is None:
            node = E.SubElement(core, tag)
        node.text = value
    app = E.fromstring(app_data)
    ap = "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}"
    # Drop unavailable legacy statistics, rather than publishing made-up Word counts.
    for name in [
        "Words",
        "Characters",
        "CharactersWithSpaces",
        "Lines",
        "Paragraphs",
        "TotalTime",
        "HeadingPairs",
        "TitlesOfParts",
    ]:
        node = app.find(ap + name)
        if node is not None:
            app.remove(node)
    for name, value in {
        "Pages": str(pages),
        "Application": "Phase35 OOXML builder",
        "AppVersion": "3.0000",
        "Template": "A06_Assignment_Report.docx (style reference)",
    }.items():
        node = app.find(ap + name)
        if node is None:
            node = E.SubElement(app, ap + name)
        node.text = value
    return xml_bytes(core), xml_bytes(app)


def breakable(text):
    """Add zero-width opportunities only inside long identifiers/URLs, not data loss."""
    return re.sub(
        r"\S{30,}",
        lambda m: re.sub(r"([/_.:;=,\-])", lambda x: x[0] + "\u200b", m[0])
        if any(c in m[0] for c in "/_.:;=,-")
        else "\u200b".join(m[0][i : i + 24] for i in range(0, len(m[0]), 24)),
        text,
    )


class Builder:
    def __init__(self, template=TEMPLATE, page_map=None, page_count=1):
        with zipfile.ZipFile(template) as package:
            self.original = {name: package.read(name) for name in package.namelist()}
        self.parts = dict(self.original)
        self.document = E.fromstring(self.parts["word/document.xml"])
        self.body = self.document.find("w:body", NS)
        self.section = deepcopy(self.body.find("w:sectPr", NS))
        self.cover = [deepcopy(p) for p in list(self.body)[:15]]
        self.relationships = E.fromstring(self.parts["word/_rels/document.xml.rels"])
        self.types = E.fromstring(self.parts["[Content_Types].xml"])
        self.headings, self.captions, self.links, self.images, self.math = [], [], [], [], []
        self.bookmarks = {}
        self.page_map = page_map or {}
        if not isinstance(page_count, int) or not 1 <= page_count <= 1000:
            raise ValueError("Invalid page count")
        self.page_count = page_count
        self.source = ROOT / "report/phase34/manuscript.md"
        self.dataset_targets = {}
        self.table_count = 0
        self.inline_md = MarkdownIt("commonmark")
        figures = json.loads(
            (ROOT / "artifacts/manifests/phase34/figure_ledger.json").read_text(encoding="utf-8")
        )
        self.figure_captions = {
            resolve_asset(row["image"], ROOT / "report/phase34/manuscript.md"): row["label"]
            + " "
            + row["caption"]
            for row in figures
        }

    def mark(self, p, key, text):
        name = bookmark_name(key)
        if name in self.bookmarks:
            raise ValueError("Duplicate bookmark " + key)
        number = str(len(self.bookmarks) + 2000)
        self.bookmarks[name] = {"key": key, "text": text}
        p.insert(1, el("bookmarkStart", {"id": number, "name": name}))
        p.append(el("bookmarkEnd", {"id": number}))
        return name

    def relationship(self, kind, target, external=False):
        rid = "rIdV3_" + str(len(self.relationships) + 1)
        attrs = {"Id": rid, "Type": NS["r"] + "/" + kind, "Target": target}
        if external:
            attrs["TargetMode"] = "External"
        E.SubElement(self.relationships, "{" + PKG + "}Relationship", attrs)
        return rid

    def hyperlink(self, parent, text, *, anchor=None, url=None, **formatting):
        h = el("hyperlink")
        if anchor:
            h.set(W + "anchor", anchor)
        else:
            h.set(R + "id", self.relationship("hyperlink", url, True))
        h.append(run(breakable(text), color="1F4E79", **formatting))
        parent.append(h)
        self.links.append({"text": text, "anchor": anchor, "url": url})

    def inline(self, parent, text, *, size=None, bibliography=False):
        if bibliography:
            text = normalize_bibliography(text)
        children = self.inline_md.parseInline(text)[0].children or []
        bold = italic = False
        container = parent
        for token in children:
            if token.type == "strong_open":
                bold = True
            elif token.type == "strong_close":
                bold = False
            elif token.type == "em_open":
                italic = True
            elif token.type == "em_close":
                italic = False
            elif token.type == "link_open":
                href = token.attrGet("href")
                h = el("hyperlink")
                if href.startswith(("https://", "http://")):
                    h.set(R + "id", self.relationship("hyperlink", href, True))
                    self.links.append({"url": href})
                elif href.startswith("#"):
                    h.set(W + "anchor", bookmark_name(href[1:]))
                    self.links.append({"anchor": bookmark_name(href[1:])})
                else:
                    path = resolve_asset(href.split("#")[0], self.source)
                    if path.stem in self.dataset_targets:
                        anchor = self.dataset_targets[path.stem]
                    elif "contract" in str(path) or "model" in str(path):
                        anchor = bookmark_name("PHỤ LỤC B")
                    else:
                        anchor = bookmark_name("PHỤ LỤC C")
                    h.set(W + "anchor", anchor)
                    self.links.append({"source_locator": str(path.relative_to(ROOT)), "anchor": anchor})
                parent.append(h)
                container = h
            elif token.type == "link_close":
                container = parent
            elif token.type in ("softbreak", "hardbreak"):
                container.append(run(" "))
            elif token.type == "code_inline":
                if ("∘" in token.content or token.content.startswith(("z = ", "F = ", "RRF(d) = "))) and len(
                    token.content
                ) < 180:
                    if len(token.content) > 60:
                        groups = token.content.split(" ∘ ")
                        lines = [""]
                        for group in groups:
                            addition = (" ∘ " if lines[-1] else "") + group
                            if len(lines[-1] + addition) > 55 and lines[-1]:
                                lines.append("∘ " + group)
                            else:
                                lines[-1] += addition
                        for number, line in enumerate(lines):
                            if number:
                                br = el("r")
                                br.append(el("br"))
                                container.append(br)
                            container.append(self.math_inline(line))
                        if parent.tag == W + "p":
                            pp = parent.find("w:pPr", NS)
                            for jc in pp.findall("w:jc", NS):
                                pp.remove(jc)
                            pp.append(el("jc", {"val": "left"}))
                    else:
                        container.append(self.math_inline(token.content))
                else:
                    container.append(
                        run(breakable(token.content), bold=bold, italic=italic, code=True, size=size)
                    )
            elif token.type == "text":
                for fragment in re.split(r"(\[\d{1,2}\])", token.content):
                    match = re.fullmatch(r"\[(\d{1,2})\]", fragment)
                    if (
                        match
                        and 1 <= int(match[1]) <= 43
                        and not bibliography
                        and size is None
                        and "appendix_" not in self.source.name
                    ):
                        self.hyperlink(
                            container,
                            fragment,
                            anchor=bookmark_name("reference_" + match[1]),
                            size=size,
                            bold=bold,
                            italic=italic,
                        )
                    elif fragment:
                        container.append(run(breakable(fragment), bold=bold, italic=italic, size=size))
            elif token.type == "image":
                raise ValueError("Inline image must be standalone block")
            else:
                raise ValueError("Unsupported inline Markdown token " + token.type)

    def math_inline(self, expression):
        self.math.append(expression)
        math_node = E.Element(M + "oMath")
        r = E.SubElement(math_node, M + "r")
        E.SubElement(r, M + "t").text = expression
        return math_node

    def math_paragraph(self, expression):
        p = paragraph()
        mp = E.SubElement(p, M + "oMathPara")
        mp.append(self.math_inline(expression))
        return p

    def caption(self, text, kind):
        match = re.match(r"(Bảng|Hình) ([A-D\d]+)\.(\d+)\.\s*(.*)", text, re.S)
        if not match:
            raise ValueError("Unnumbered caption " + text)
        label, chapter, number, title = match.groups()
        p = paragraph(style="Caption")
        key = f"{label} {chapter}.{number}"
        p.append(run(f"{label} {chapter}."))
        p.append(field(f"SEQ V3{kind.title()} \\r {number}", number))
        anchor = self.mark(p, key, text)
        self.inline(p, ". " + title)
        p.find("w:pPr", NS).append(el("keepNext", {"val": "1" if kind == "table" else "0"}))
        self.captions.append({"key": key, "text": text, "anchor": anchor, "kind": kind})
        return p

    def table(self, rows):
        widths = column_widths(rows)
        size = 19 if len(widths) >= 7 else 21
        t = el("tbl")
        props = el("tblPr")
        props.append(el("tblW", {"w": 9638, "type": "dxa"}))
        props.append(el("tblLayout", {"type": "fixed"}))
        borders = el("tblBorders")
        for side in ["top", "left", "bottom", "right", "insideH", "insideV"]:
            borders.append(el(side, {"val": "single", "sz": 4, "color": "B9C9D6"}))
        props.append(borders)
        margins = el("tblCellMar")
        for side in ["top", "bottom", "left", "right"]:
            margins.append(el(side, {"w": 65 if side in ["top", "bottom"] else 85, "type": "dxa"}))
        props.append(margins)
        t.append(props)
        grid = el("tblGrid")
        for width in widths:
            grid.append(el("gridCol", {"w": width}))
        t.append(grid)
        for index, row in enumerate(rows):
            tr = el("tr")
            rp = el("trPr")
            # Keep ordinary rows intact: a label must not spill onto a page without its numbers.
            # Conservatively allow exceptionally tall appendix rows to flow (never fixed height).
            estimated_points = max(
                math.ceil(max(1, len(value)) * 1.4 / max(8, int((width / 20 - 10) / (size / 2 * 0.62))))
                * (size / 2 * 1.3)
                + 8
                for width, value in zip(widths, row, strict=True)
            )
            if estimated_points <= 400:
                rp.append(el("cantSplit"))
            if index == 0:
                rp.append(el("tblHeader"))
            tr.append(rp)
            for width, value in zip(widths, row, strict=True):
                tc = el("tc")
                cp = el("tcPr")
                cp.append(el("tcW", {"w": width, "type": "dxa"}))
                cp.append(el("vAlign", {"val": "center" if index == 0 else "top"}))
                if index == 0 or index % 2 == 0:
                    cp.append(el("shd", {"fill": "DEEAF6" if index == 0 else "F6F8FA", "val": "clear"}))
                tc.append(cp)
                p = paragraph(style="V3Table")
                pp = p.find("w:pPr", NS)
                pp.append(el("spacing", {"before": 0, "after": 30, "line": 250, "lineRule": "auto"}))
                self.inline(p, value, size=size)
                if index == 0:
                    for r in p.findall(".//w:r", NS):
                        rpr = r.find("w:rPr", NS)
                        if rpr is None:
                            rpr = el("rPr")
                            r.insert(0, rpr)
                        rpr.append(el("b"))
                        rpr.append(el("color", {"val": "1F4E79"}))
                tc.append(p)
                tr.append(tc)
            t.append(tr)
        self.table_count += 1
        return t

    def image(self, token):
        path = resolve_asset(token.attrGet("src"), self.source)
        data = path.read_bytes()
        if path.suffix.lower() == ".svg":
            receipt = json.loads(
                (ROOT / "artifacts/manifests/phase35/timeline_browser_render.json").read_text()
            )
            fallback = ROOT / receipt["output"]
            if (
                receipt["source"] != str(path.relative_to(ROOT))
                or receipt["source_sha256"] != digest(path)
                or digest(fallback) != receipt["output_sha256"]
            ):
                raise ValueError("SVG/browser fallback provenance mismatch")
            data = fallback.read_bytes()
        with Image.open(io.BytesIO(data)) as img:
            width, height = img.size
            if img.format not in {"PNG", "JPEG"}:
                raise ValueError("Unexpected image format")
            suffix = "png" if img.format == "PNG" else "jpeg"
        index = len(self.images) + 1
        name = f"v3_figure_{index:03d}.{suffix}"
        self.parts["word/media/" + name] = data
        rid = self.relationship("image", "media/" + name)
        if not any(x.get("Extension") == suffix for x in self.types):
            E.SubElement(self.types, "{" + CT + "}Default", Extension=suffix, ContentType="image/" + suffix)
        scale = min(6.69 / width, 5.8 / height)
        cx, cy = round(width * scale * 914400), round(height * scale * 914400)
        wp = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
        a = "http://schemas.openxmlformats.org/drawingml/2006/main"
        pic = "http://schemas.openxmlformats.org/drawingml/2006/picture"
        p = paragraph(style="V3Figure")
        drawing = E.SubElement(E.SubElement(p, W + "r"), W + "drawing")
        inline = E.SubElement(drawing, "{" + wp + "}inline", distT="0", distB="0", distL="0", distR="0")
        E.SubElement(inline, "{" + wp + "}extent", cx=str(cx), cy=str(cy))
        E.SubElement(
            inline, "{" + wp + "}docPr", id=str(1000 + index), name=name, descr=token.content or path.stem
        )
        graphic = E.SubElement(inline, "{" + a + "}graphic")
        gd = E.SubElement(graphic, "{" + a + "}graphicData", uri=pic)
        ppic = E.SubElement(gd, "{" + pic + "}pic")
        nv = E.SubElement(ppic, "{" + pic + "}nvPicPr")
        E.SubElement(nv, "{" + pic + "}cNvPr", id="0", name=name)
        E.SubElement(nv, "{" + pic + "}cNvPicPr")
        bf = E.SubElement(ppic, "{" + pic + "}blipFill")
        E.SubElement(bf, "{" + a + "}blip", {R + "embed": rid})
        E.SubElement(E.SubElement(bf, "{" + a + "}stretch"), "{" + a + "}fillRect")
        sp = E.SubElement(ppic, "{" + pic + "}spPr")
        xf = E.SubElement(sp, "{" + a + "}xfrm")
        E.SubElement(xf, "{" + a + "}off", x="0", y="0")
        E.SubElement(xf, "{" + a + "}ext", cx=str(cx), cy=str(cy))
        E.SubElement(E.SubElement(sp, "{" + a + "}prstGeom", prst="rect"), "{" + a + "}avLst")
        self.images.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": digest(path),
                "media": name,
                "width_px": width,
                "height_px": height,
                "width_inches": cx / 914400,
                "height_inches": cy / 914400,
            }
        )
        return p

    def heading(self, text, level, appendix=False):
        key = text
        if text.startswith("PHỤ LỤC "):
            key = text[:9]
        if bookmark_name(key) in self.bookmarks and level > 2:
            key = f"{self.source.name}_{len(self.headings)}_{text}"
        style = f"Heading{min(level, 3)}"
        if appendix and level > 1:
            style = "V3AppendixHeading" if level == 2 else "V3Subheading"
        p = paragraph(text, style)
        anchor = self.mark(p, key, text)
        if level == 1:
            p.find("w:pPr", NS).append(el("pageBreakBefore"))
        self.headings.append(
            {
                "text": text,
                "level": level,
                "anchor": anchor,
                "toc": level <= 2 and not (appendix and level > 1),
            }
        )
        return p

    def blocks(self, path, *, front=False):
        self.source = Path(path)
        text = self.source.read_text(encoding="utf-8")
        tokens = parse_markdown(text)
        appendix = (
            self.source.name.split("_")[-1].startswith(("a.", "b.", "c.", "d."))
            or "appendix_" in self.source.name
        )
        bibliography = self.source.name == "08_references.md"
        index = 0
        list_depth, list_numbers = 0, []
        while index < len(tokens):
            token = tokens[index]
            if token.type == "heading_open":
                content = tokens[index + 1].content
                level = int(token.tag[1])
                if not (front and level == 1):
                    p = self.heading(content, level, appendix)
                    self.body.append(p)
                index += 3
            elif token.type == "paragraph_open":
                inline = tokens[index + 1]
                caption_content = (
                    inline.content.replace("**", "")
                    if inline.content.startswith(("**Hình ", "**Bảng "))
                    else inline.content
                )
                children = inline.children or []
                if len(children) == 1 and children[0].type == "image":
                    self.body.append(self.image(children[0]))
                    image_path = resolve_asset(children[0].attrGet("src"), self.source)
                    next_text = (
                        tokens[index + 4].content
                        if index + 4 < len(tokens) and tokens[index + 3].type == "paragraph_open"
                        else ""
                    )
                    next_text = next_text.replace("**", "")
                    if not re.match(r"^Hình [A-D\d]+\.\d+\.\s", next_text):
                        self.body.append(
                            self.caption(self.figure_captions[image_path].replace("**", ""), "figure")
                        )
                elif re.match(r"^(Bảng|Hình) [A-D\d]+\.\d+\.\s", caption_content):
                    key = re.match(r"^((?:Bảng|Hình) [A-D\d]+\.\d+)\.", caption_content)[1]
                    if caption_content.startswith("Hình") and bookmark_name(key) in self.bookmarks:
                        previous = next(x["text"] for x in self.captions if x["key"] == key)
                        if previous != caption_content:
                            raise ValueError("Figure ledger/source caption mismatch: " + key)
                    else:
                        self.body.append(
                            self.caption(
                                caption_content, "table" if caption_content.startswith("Bảng") else "figure"
                            )
                        )
                else:
                    p = paragraph(style="V3List" if list_depth else None)
                    if list_depth:
                        label = f"{list_numbers[-1]}. " if list_numbers[-1] else "• "
                        p.append(run(label))
                        if list_numbers[-1]:
                            list_numbers[-1] += 1
                    if bibliography:
                        match = re.match(r"\[(\d+)\]", inline.content)
                        if match:
                            self.mark(p, "reference_" + match[1], inline.content)
                    self.inline(p, inline.content, bibliography=bibliography)
                    self.body.append(p)
                index += 3
            elif token.type == "table_open":
                rows, row = [], []
                index += 1
                while tokens[index].type != "table_close":
                    tt = tokens[index]
                    if tt.type == "tr_open":
                        row = []
                    elif tt.type == "inline":
                        row.append(tt.content)
                    elif tt.type == "tr_close":
                        rows.append(row)
                    index += 1
                self.body.append(self.table(rows))
                self.body.append(paragraph("", "V3Spacer"))
                index += 1
            elif token.type in ("fence", "code_block"):
                for line in token.content.rstrip("\n").split("\n"):
                    p = paragraph(style="V3Code")
                    p.append(run(line, code=True, size=20))
                    self.body.append(p)
                index += 1
            elif token.type in ("bullet_list_open", "ordered_list_open"):
                list_depth += 1
                list_numbers.append(
                    int(token.attrGet("start") or 1) if token.type == "ordered_list_open" else 0
                )
                index += 1
            elif token.type in ("bullet_list_close", "ordered_list_close"):
                list_depth -= 1
                list_numbers.pop()
                index += 1
            elif token.type in (
                "list_item_open",
                "list_item_close",
                "blockquote_open",
                "blockquote_close",
                "hr",
            ):
                index += 1
            else:
                raise ValueError(f"Unsupported block token {token.type} in {path}")

    def styles(self):
        styles = E.fromstring(self.original["word/styles.xml"])
        definitions = [
            (
                "V3Table",
                "Normal",
                21,
                {
                    "jc": {"val": "left"},
                    "ind": {"firstLine": 0},
                    "spacing": {"after": 30, "line": 250, "lineRule": "auto"},
                },
            ),
            (
                "V3Code",
                "CodeBlock",
                20,
                {
                    "ind": {"left": 180, "firstLine": 0},
                    "spacing": {"after": 0, "line": 240, "lineRule": "auto"},
                },
            ),
            (
                "V3Figure",
                "Normal",
                26,
                {
                    "jc": {"val": "center"},
                    "ind": {"firstLine": 0},
                    "keepNext": {},
                    "spacing": {"before": 80, "after": 40},
                },
            ),
            (
                "V3Spacer",
                "Normal",
                4,
                {
                    "ind": {"firstLine": 0},
                    "spacing": {"before": 0, "after": 0, "line": 80, "lineRule": "exact"},
                },
            ),
            ("V3List", "Normal", 26, {"ind": {"left": 250, "hanging": 250}, "spacing": {"after": 70}}),
            (
                "V3Index",
                "Normal",
                24,
                {
                    "ind": {"firstLine": 0},
                    "spacing": {"after": 50, "line": 260, "lineRule": "auto"},
                    "jc": {"val": "left"},
                },
            ),
            ("V3AppendixHeading", "Heading2", 27, {}),
            ("V3Subheading", "Heading3", 26, {}),
        ]
        for name, base, size, properties in definitions:
            s = el("style", {"type": "paragraph", "styleId": name, "customStyle": "1"})
            s.append(el("name", {"val": name}))
            s.append(el("basedOn", {"val": base}))
            ppr = el("pPr")
            for key, attrs in properties.items():
                ppr.append(el(key, attrs))
            if name == "V3Index":
                tabs = el("tabs")
                tabs.append(el("tab", {"val": "right", "leader": "dot", "pos": 9638}))
                ppr.append(tabs)
            s.append(ppr)
            rpr = el("rPr")
            rpr.append(el("sz", {"val": size}))
            s.append(rpr)
            styles.append(s)
        self.parts["word/styles.xml"] = xml_bytes(styles)

    def index_pages(self, title, entries, *, figures=False):
        nodes = [paragraph(title, "FrontMatterTitle")]
        nodes[0].find("w:pPr", NS).append(el("pageBreakBefore"))
        for row in entries:
            text = row["text"]
            if figures and not re.match(r"^Bảng [AB]\.\d+\.", text):
                # Keep body captions complete; the list is an explicit short-title view.
                text = re.split(r"\.\s+", text, maxsplit=2)
                text = ". ".join(text[:2]) + ("." if len(text) > 2 else "")
            p = paragraph(style="V3Index")
            if row.get("level") == 2:
                p.find("w:pPr", NS).append(el("ind", {"left": 260, "firstLine": 0}))
            if figures:
                p.append(field("REF " + row["anchor"] + " \\h", row["key"], color="1F4E79"))
                self.hyperlink(p, text[len(row["key"]) :], anchor=row["anchor"])
                self.links.append({"anchor": row["anchor"], "kind": "REF"})
            else:
                self.hyperlink(p, text, anchor=row["anchor"])
            rr = el("r")
            rr.append(el("tab"))
            p.append(rr)
            p.append(field("PAGEREF " + row["anchor"] + " \\h", self.page_map.get(row["anchor"], "—")))
            nodes.append(p)
        return nodes

    def build(self, manifest, output):
        for child in list(self.body):
            self.body.remove(child)
        for index, p in enumerate(self.cover):
            if index in (5, 6):
                for node in list(p):
                    if node.tag != W + "pPr":
                        p.remove(node)
                if index == 5:
                    p.append(run("TIỂU LUẬN MÔN HỌC", bold=True, size=44))
                else:
                    p.append(run("TRÍ TUỆ NHÂN TẠO", bold=True, size=32))
                cover_properties = p.find("w:pPr", NS)
                if cover_properties is None:
                    cover_properties = el("pPr")
                    p.insert(0, cover_properties)
                for child in list(cover_properties):
                    if child.tag in (W + "jc", W + "ind"):
                        cover_properties.remove(child)
                cover_properties.append(el("jc", {"val": "center"}))
                cover_properties.append(el("ind", {"firstLine": 0}))
            self.body.append(p)
        # Data-card links resolve to the exact reproduced appendix section.
        appendix = ROOT / "report/phase34/sections/09_appendix_a.md"
        for heading, dataset in re.findall(
            r"^## (A\.\d+\. (ch\d_\w+))$", appendix.read_text(encoding="utf-8"), re.M
        ):
            self.dataset_targets[dataset] = bookmark_name(heading)
        for relative in manifest["publication_order"]:
            if Path(relative).name in ("contents.md", "figures_and_tables.md"):
                continue
            self.blocks(ROOT / relative, front=Path(relative).name == "front_matter.md")
        # Front matter gets a real page break, after the retained 15-paragraph cover.
        if len(self.body) > 15:
            self.body[15].find("w:pPr", NS).append(el("pageBreakBefore"))
        insertion = next(i for i, p in enumerate(self.body) if "".join(p.itertext()) == "MỞ ĐẦU")
        indices = self.index_pages("MỤC LỤC", [x for x in self.headings if x["toc"]])
        indices += self.index_pages(
            "DANH MỤC HÌNH", [x for x in self.captions if x["kind"] == "figure"], figures=True
        )
        if self.page_map:
            required = [x for x in self.headings if x["toc"]] + self.captions
            missing = [x["anchor"] for x in required if x["anchor"] not in self.page_map]
            if missing:
                raise ValueError("Incomplete pagination cache: " + str(missing))
        indices += self.index_pages(
            "DANH MỤC BẢNG", [x for x in self.captions if x["kind"] == "table"], figures=True
        )
        for offset, node in enumerate(indices):
            self.body.insert(insertion + offset, node)
        self.body.append(self.section)
        self.styles()
        footer = E.fromstring(self.original["word/footer1.xml"])
        p = footer.find("w:p", NS)
        p.append(run(" ", font="Times New Roman", size=24))
        p.append(field("PAGE", "1", font="Times New Roman", size=24))
        p.append(run(" / ", font="Times New Roman", size=24))
        p.append(field("NUMPAGES", str(self.page_count), font="Times New Roman", size=24))
        self.parts["word/footer1.xml"] = xml_bytes(footer)
        settings = E.fromstring(self.original["word/settings.xml"])
        update = settings.find("w:updateFields", NS)
        if update is None:
            update = el("updateFields")
            settings.append(update)
        update.set(W + "val", "true")
        self.parts["word/settings.xml"] = xml_bytes(settings)
        self.parts["word/document.xml"] = xml_bytes(self.document)
        self.parts["word/_rels/document.xml.rels"] = xml_bytes(self.relationships)
        self.parts["[Content_Types].xml"] = xml_bytes(self.types)
        self.parts["docProps/core.xml"], self.parts["docProps/app.xml"] = publication_properties(
            self.original["docProps/core.xml"], self.original["docProps/app.xml"], self.page_count
        )
        unresolved = [x for x in self.links if x.get("anchor") and x["anchor"] not in self.bookmarks]
        if unresolved:
            raise ValueError("Unresolved links " + str(unresolved[:3]))
        if self.table_count != 143 + 1 or len(self.images) != 37:
            raise ValueError(f"Unexpected tables/images {self.table_count}/{len(self.images)}")
        output = Path(output)
        if output.exists():
            raise FileExistsError(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as package:
            for name, data in self.parts.items():
                package.writestr(name, data)
        evidence = {
            "template_sha256": digest(TEMPLATE),
            "output": str(output.relative_to(ROOT)),
            "sha256": digest(output),
            "tables": self.table_count,
            "captions": self.captions,
            "headings": self.headings,
            "images": self.images,
            "math": self.math,
            "bookmarks": self.bookmarks,
            "links": self.links,
            "page_map": self.page_map,
            "editable_parts": sorted(EDITABLE),
            "unchanged_parts": [name for name, data in self.original.items() if self.parts[name] == data],
            "changed_parts": [name for name, data in self.original.items() if self.parts[name] != data],
            "source_manifest_sha256": digest(ROOT / "artifacts/manifests/phase34/manuscript_manifest.json"),
            "bibliography_presentation_normalization": [
                "Küttler",
                "Rocktäschel",
                "Léon",
                "Jürgen",
                "Łukasz",
                "Vrandečić",
                "Krötzsch",
                "Büttcher",
            ],
        }
        if set(evidence["changed_parts"]) - EDITABLE:
            raise RuntimeError("Unexpected package mutation")
        write_once_json(output.with_suffix(".build.json"), evidence)
        return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--page-map")
    parser.add_argument("--page-count", type=int, default=1)
    args = parser.parse_args()
    pages = json.loads((ROOT / args.page_map).read_text()) if args.page_map else None
    manifest = json.loads((ROOT / "artifacts/manifests/phase34/manuscript_manifest.json").read_text())
    evidence = Builder(page_map=pages, page_count=args.page_count).build(manifest, ROOT / args.output)
    print(
        json.dumps(
            {key: evidence[key] for key in ["output", "sha256", "tables", "changed_parts"]},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
