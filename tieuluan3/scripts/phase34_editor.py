"""Pure Markdown helpers for Phase34. No framework, data reader or inference imports."""

import ast
import os
import re
from pathlib import Path


def safe_path(root, relative):
    root = Path(root).resolve()
    relative = Path(relative)
    path = root / relative
    if (
        relative.is_absolute()
        or not path.resolve().is_relative_to(root)
        or path.is_symlink()
        or not path.is_file()
    ):
        raise ValueError("Unsafe or missing source: " + str(relative))
    return path


def markdown_blocks(text):
    """One block per line, preserving lines and byte-independent text offsets."""
    rows, offset, fence = [], 0, None
    for line in text.splitlines(keepends=True):
        value = line.rstrip("\r\n")
        marker = re.match(r"^(`{3,}|~{3,})", value)
        kind = "text"
        if marker:
            candidate = marker[1]
            if fence is None:
                fence = candidate
            elif candidate[0] == fence[0] and len(candidate) >= len(fence):
                fence = None
            kind = "code"
        elif fence:
            kind = "code"
        elif re.match(r"^#{1,6}\s", value):
            kind = "heading"
        rows.append({"kind": kind, "text": value, "start": offset, "end": offset + len(line)})
        offset += len(line)
    if fence:
        raise ValueError("Unclosed Markdown fence")
    return rows


def section_replace(text, number, replacement):
    blocks = markdown_blocks(text)
    matches = [
        i
        for i, b in enumerate(blocks)
        if b["kind"] == "heading" and b["text"].startswith("## " + number + " ")
    ]
    if len(matches) != 1:
        raise ValueError("Expected one section " + number)
    index = matches[0]
    end = next(
        (b["start"] for b in blocks[index + 1 :] if b["kind"] == "heading" and b["text"].startswith("## ")),
        len(text),
    )
    return text[: blocks[index]["start"]] + replacement.rstrip() + "\n\n" + text[end:]


def rebase_images(text, source, destination, root):
    images = []

    def replace(match):
        name = match[2]
        if re.match(r"^[a-zA-Z]+:", name):
            raise ValueError("Remote image not permitted")
        absolute = (source.parent / name).resolve()
        try:
            relative = absolute.relative_to(root.resolve())
        except ValueError as error:
            raise ValueError("Image escapes repository") from error
        absolute = safe_path(root, relative)
        images.append(absolute)
        return "![" + match[1] + "](" + Path(os.path.relpath(absolute, destination.parent)).as_posix() + ")"

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace, text), images


def caption_tables(text, chapter):
    blocks = markdown_blocks(text)
    result, tables, i, heading = [], [], 0, "Dữ liệu"
    while i < len(blocks):
        block = blocks[i]
        if block["kind"] == "heading":
            heading = re.sub(r"^#+\s*[\d.]*\s*", "", block["text"])
        if (
            block["kind"] != "code"
            and block["text"].startswith("|")
            and i + 1 < len(blocks)
            and re.match(r"^\|\s*:?-", blocks[i + 1]["text"])
        ):
            start = i
            while i < len(blocks) and blocks[i]["kind"] != "code" and blocks[i]["text"].startswith("|"):
                i += 1
            table = "\n".join(b["text"] for b in blocks[start:i])
            label = f"Bảng {chapter}.{len(tables) + 1}."
            tables.append({"label": label, "heading": heading, "markdown": table})
            result.extend(
                [label + " " + heading + "\n\n", text[blocks[start]["start"] : blocks[i - 1]["end"]]]
            )
        else:
            result.append(text[block["start"] : block["end"]])
            i += 1
    return "".join(result), tables


def bibliography_entries(text):
    result, cursor = {}, 0
    pattern = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")
    while match := pattern.search(text, cursor):
        start, index, depth = match.start(), match.end(), 1
        while index < len(text) and depth:
            char = text[index]
            if char in "{}":
                depth += 1 if char == "{" else -1
            index += 1
        if depth:
            raise ValueError("Unclosed bibliography entry")
        key = match[2]
        if key in result:
            raise ValueError("Duplicate bibliography key: " + key)
        result[key], cursor = text[start:index], index
    return result


def convert_citations(text, bibliography, registry):
    def convert(match):
        keys = re.findall(r"@([\w:.-]+)", match[0])
        numbers = []
        for key in keys:
            if key not in bibliography:
                raise ValueError("Unknown citation " + key)
            if key not in registry:
                registry[key] = len(registry) + 1
            numbers.append(str(registry[key]))
        return "[" + ", ".join(numbers) + "]"

    result = []
    for block in markdown_blocks(text):
        line = text[block["start"] : block["end"]]
        result.append(line if block["kind"] == "code" else re.sub(r"\[@[^\]]+\]", convert, line))
    return "".join(result)


def rebase_links(text, source, destination, root):
    def replace(match):
        name = match[2]
        if re.match(r"^(?:https?://|mailto:|#)", name):
            return match[0]
        absolute = (source.parent / name).resolve()
        try:
            relative = absolute.relative_to(root.resolve())
        except ValueError as error:
            raise ValueError("Link escapes repository") from error
        absolute = safe_path(root, relative)
        return "[" + match[1] + "](" + Path(os.path.relpath(absolute, destination.parent)).as_posix() + ")"

    return re.sub(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)", replace, text)


def figure_captions(text):
    figures = []
    pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    for match in pattern.finditer(text):
        candidate = (
            match[1]
            if re.match(r"^Hình \d+\.\d+\.", match[1])
            else text[match.end() :].lstrip()[:600].lstrip("*")
        )
        label = re.match(r"^(Hình \d+\.\d+\.)\s*([^\n]+)", candidate)
        if not label:
            raise ValueError("Missing numbered figure caption " + match[2])
        figures.append({"label": label[1], "caption": label[2].rstrip("*"), "image": match[2]})
    return figures


def source_excerpt(path, class_name, method_name):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    nodes = [
        method
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
        for method in node.body
        if isinstance(method, ast.FunctionDef) and method.name == method_name
    ]
    if len(nodes) != 1:
        raise ValueError("Expected unique source excerpt")
    node = nodes[0]
    return "\n".join(source.splitlines()[node.lineno - 1 : node.end_lineno]), node.lineno, node.end_lineno
