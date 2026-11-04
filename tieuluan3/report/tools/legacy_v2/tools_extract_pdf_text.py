from __future__ import annotations

import re
import sys
import zlib
from pathlib import Path


def unescape_pdf_string(value: bytes) -> str:
    out = bytearray()
    i = 0
    while i < len(value):
        c = value[i]
        if c == 0x5C and i + 1 < len(value):
            nxt = value[i + 1]
            if nxt in b"nrtbf":
                out.append({ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12}[nxt])
                i += 2
                continue
            if nxt in b"()\\":
                out.append(nxt)
                i += 2
                continue
            if 48 <= nxt <= 55:
                j = i + 1
                octal = bytearray()
                while j < len(value) and len(octal) < 3 and 48 <= value[j] <= 55:
                    octal.append(value[j])
                    j += 1
                out.append(int(octal.decode("ascii"), 8) & 0xFF)
                i = j
                continue
            out.append(nxt)
            i += 2
            continue
        out.append(c)
        i += 1
    for enc in ("utf-16-be", "utf-8", "cp1258", "latin-1"):
        try:
            text = bytes(out).decode(enc)
            if text.count("\x00") < 2:
                return text
        except UnicodeDecodeError:
            pass
    return bytes(out).decode("latin-1", errors="ignore")


def extract_literals(stream: bytes) -> list[str]:
    chunks: list[str] = []
    i = 0
    while i < len(stream):
        if stream[i] == 0x28:
            depth = 1
            j = i + 1
            escaped = False
            buf = bytearray()
            while j < len(stream) and depth:
                c = stream[j]
                if escaped:
                    buf.append(0x5C)
                    buf.append(c)
                    escaped = False
                elif c == 0x5C:
                    escaped = True
                elif c == 0x28:
                    depth += 1
                    buf.append(c)
                elif c == 0x29:
                    depth -= 1
                    if depth:
                        buf.append(c)
                else:
                    buf.append(c)
                j += 1
            text = unescape_pdf_string(bytes(buf)).strip()
            if text:
                chunks.append(text)
            i = j
            continue
        if stream[i] == 0x3C and i + 1 < len(stream) and stream[i + 1] != 0x3C:
            j = stream.find(b">", i + 1)
            if j != -1:
                raw = re.sub(rb"\s+", b"", stream[i + 1 : j])
                if len(raw) >= 4 and len(raw) % 2 == 0:
                    try:
                        data = bytes.fromhex(raw.decode("ascii"))
                        text = data.decode("utf-16-be", errors="ignore").strip()
                        if text and any(ch.isprintable() and not ch.isspace() for ch in text):
                            chunks.append(text)
                    except Exception:
                        pass
                i = j + 1
                continue
        i += 1
    return chunks


def main() -> None:
    pdf = Path(sys.argv[1])
    data = pdf.read_bytes()
    pieces: list[str] = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        stream = match.group(1)
        prefix = data[max(0, match.start() - 500) : match.start()]
        if b"FlateDecode" in prefix:
            try:
                stream = zlib.decompress(stream)
            except zlib.error:
                continue
        if len(stream) > 2_000_000 or (b" Tj" not in stream and b" TJ" not in stream and b"BT" not in stream):
            continue
        texts = extract_literals(stream)
        if texts:
            pieces.append("\n".join(texts))
    print("\n\n--- stream ---\n\n".join(pieces))


if __name__ == "__main__":
    main()
