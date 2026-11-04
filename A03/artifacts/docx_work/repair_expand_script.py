from pathlib import Path


def main():
    path = Path("artifacts/docx_work/expand_a03_report.py")
    text = path.read_text(encoding="utf-8")
    if "def build_more_appendices" in text:
        print("expand script already repaired")
        return

    heading_start = text.index("def heading1(")
    heading_end = text.index("\ndef heading2(", heading_start)
    heading_block = text[heading_start:heading_end]
    marker = '    elements.extend(heading1("PHỤ LỤC B.'
    extra_start = heading_block.index(marker)
    appendix_block = heading_block[extra_start:]

    clean_heading1 = (
        "def heading1(text, page_break=False):\n"
        "    elements = []\n"
        "    if page_break:\n"
        "        elements.append(page_break_para())\n"
        "    elements.append(paragraph(text, style=\"Heading1\", size=None))\n"
        "    return elements\n\n"
    )
    text = text[:heading_start] + clean_heading1 + text[heading_end:]

    expand_anchor = "\n\ndef expand_docx("
    expand_pos = text.index(expand_anchor)
    prefix = text[:expand_pos]
    suffix = text[expand_pos:]
    return_pos = prefix.rfind("\n    return elements")
    if return_pos == -1:
        raise RuntimeError("Could not find build_added_sections return.")

    prefix = (
        prefix[:return_pos]
        + "\n    elements.extend(build_more_appendices())"
        + prefix[return_pos:]
    )
    appendix_func = "\n\ndef build_more_appendices():\n    elements = []\n" + appendix_block
    text = prefix + appendix_func + suffix
    path.write_text(text, encoding="utf-8")
    print("expand script repaired")


if __name__ == "__main__":
    main()
