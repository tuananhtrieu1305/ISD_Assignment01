"""Protect source fidelity, manuscript coverage and portable file boundaries."""

from pathlib import Path

import pytest

from agent02_assignment.code.publication_v1 import blocks, display_heading, local_file, plain_inline

BASE = Path(__file__).resolve().parents[1]


def test_exact_source_fence():
    source = 'def learn(x):\n    if x:\n        return 1\n    return 0'
    assert blocks('```python\n' + source + '\n```')[0]['text'] == source


def test_unclosed_fence():
    with pytest.raises(ValueError, match='Unclosed'):
        blocks('```python\nx = 1')


def test_required_q3_steps_stay_separate():
    assert len(blocks('1. Target = 10,5\n2. Delta = 6,5\n3. Q mới = 4,65')) == 3


def test_table_escaped_pipe_and_alignment():
    assert blocks('|Name|Value|\n|:---|---:|\n|a\\|b|2|')[0]['rows'] == [['Name', 'Value'], ['a|b', '2']]


def test_ragged_table():
    with pytest.raises(ValueError, match='Ragged'):
        blocks('|a|b|\n|---|---|\n|x|')


@pytest.mark.parametrize('name', ['', '../checkpoint.json', '/etc/passwd', 'missing-file'])
def test_asset_boundary(name):
    with pytest.raises(ValueError):
        local_file(BASE / 'report/phase08', name)


def test_missing_inline_markup_and_heading_identity():
    assert plain_inline('**profit** and `Q.learn`') == 'profit and Q.learn'
    assert plain_inline('Naeem *A Gentle Introduction*') == 'Naeem A Gentle Introduction'
    assert display_heading('6.3. Câu 3 — Ý nghĩa') == '6 3 Câu 3 Ý nghĩa'


def test_full_manuscript_no_missing_assets_or_code():
    import json
    manuscript = BASE / 'report/phase08/manuscript.md'
    items = blocks(manuscript.read_text(encoding='utf-8'))
    excerpts = json.loads((BASE / 'report/phase08/code_excerpt_index.json').read_text())
    assert [b['text'] for b in items if b['kind'] == 'code'] == [e['text'] for e in excerpts]
    assert len([b for b in items if b['kind'] == 'image']) == 20
    # Twelve artifact-bound tables plus run matrix and rule/RL comparison.
    assert len([b for b in items if b['kind'] == 'table']) == 14
    for item in items:
        if item['kind'] == 'image':
            relative = (manuscript.parent / item['path']).resolve().relative_to(BASE).as_posix()
            assert local_file(BASE, relative).is_file()
