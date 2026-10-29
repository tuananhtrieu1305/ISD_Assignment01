"""Read-only Markdown parsing and portable presentation path guards."""

import hashlib
import re
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local_file(base, relative):
    base = Path(base).resolve()
    target = (base / relative).resolve()
    if not relative or Path(relative).is_absolute() or not target.is_relative_to(base) or not target.is_file():
        raise ValueError('Missing or out-of-scope publication asset: ' + relative)
    return target


def blocks(text):
    """Parse the manuscript subset, preserving fenced source exactly."""
    lines = text.splitlines()
    result = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith('```'):
            language = line[3:]
            code = []
            index += 1
            while index < len(lines) and not lines[index].startswith('```'):
                code.append(lines[index])
                index += 1
            if index == len(lines):
                raise ValueError('Unclosed code fence')
            result.append({'kind': 'code', 'language': language, 'text': '\n'.join(code)})
        elif re.match(r'^#{1,3} ', line):
            level = len(line) - len(line.lstrip('#'))
            result.append({'kind': 'heading', 'level': level, 'text': line[level + 1:]})
        elif line.startswith('|'):
            table = []
            while index < len(lines) and lines[index].startswith('|'):
                cells = re.split(r'(?<!\\)\|', lines[index].strip().strip('|'))
                cells = [c.strip().replace('\\|', '|') for c in cells]
                if not all(re.fullmatch(r':?-+:?', c) for c in cells):
                    table.append(cells)
                index += 1
            if len({len(row) for row in table}) != 1:
                raise ValueError('Ragged publication table')
            result.append({'kind': 'table', 'rows': table})
            continue
        elif match := re.fullmatch(r'!\[([^]]+)\]\(([^)]+)\)', line):
            result.append({'kind': 'image', 'id': match[1], 'path': match[2]})
        elif re.match(r'^\d+\. ', line):
            result.append({'kind': 'paragraph', 'text': line.strip()})
        else:
            paragraph = [line.strip()]
            index += 1
            while index < len(lines) and lines[index].strip() and not re.match(r'^(?:#{1,3} |```|\||!\[|\d+\. )', lines[index]):
                paragraph.append(lines[index].strip())
                index += 1
            result.append({'kind': 'paragraph', 'text': ' '.join(paragraph)})
            continue
        index += 1
    return result


def plain_inline(text):
    return re.sub(r'\*\*([^*]+)\*\*|`([^`]+)`|\*([^*]+)\*', lambda m: m[1] or m[2] or m[3], text)


def display_heading(text):
    """Typography-only punctuation removal; identifiers and wording remain."""
    return re.sub(r'\s+', ' ', re.sub(r'[.,:;–—]', ' ', text)).strip()
