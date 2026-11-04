"""Content-assembly contracts; never import model runners or call scientific evaluators."""

import ast
import hashlib

import pytest

from agent02_assignment.code.report_assets import (
    decimal_vi,
    extract_code,
    markdown_table,
    readable_prose,
    render_tokens,
    validate_structure,
)


def test_vietnamese_decimals_keep_sign_and_zero():
    assert decimal_vi(34.02786)== '34,02786'
    assert decimal_vi(-3.75445)== '-3,75445'
    assert decimal_vi(0,0)== '0'
    assert decimal_vi(3345548,0,group=True)== '3.345.548'


@pytest.mark.parametrize('value',[float('nan'),float('inf')])
def test_nonfinite_prose_numbers_rejected(value):
    with pytest.raises(ValueError):
        decimal_vi(value)


def test_table_shape_and_escaping():
    result=markdown_table(['A','B'],[['x|y',2],['z',3]])
    assert 'x\\|y' in result and '|---|---|' in result
    with pytest.raises(ValueError):
        markdown_table(['A'],[['x','y']])


def test_token_rendering_and_provenance():
    values={'X':'4,65','Y':'5'}
    text,used=render_tokens('Q={{X}};margin={{Y}};Q={{X}}',values)
    assert text=='Q=4,65;margin=5;Q=4,65' and used==['X','Y','X']
    with pytest.raises(ValueError):
        render_tokens('{{MISSING}}',values)
    with pytest.raises(ValueError):
        render_tokens('{{X}}',{'X':'{{NESTED}}'})


def test_prose_spacing_preserves_code_ids_and_file_paths():
    text='F01 S4 Q0 float64 B23DCCN053 D23CTPM01 Agent02 AGENT02 arXiv:2501.06322v1 Q34,02786: train5episode×20bước, α0,1; {{N.a1}} `q2` data/a001.json\n```python\nq2=3\n```'
    result=readable_prose(text)
    assert 'train 5 episode × 20 bước' in result and 'α 0,1' in result
    assert 'F01 S4 Q0 float64' in result and '{{N.a1}}' in result
    assert '`q2` data/a001.json' in result and 'q2=3' in result
    assert 'B23DCCN053 D23CTPM01 Agent02' in result
    assert 'AGENT02 arXiv:2501.06322v1' in result
    assert 'Q 34,02786' in result


def test_ast_excerpt_is_exact_and_keeps_terminal(tmp_path):
    source='class Agent:\n    def learn(self, terminal):\n        if terminal:\n            return 6\n        return 9\n'
    target=tmp_path/'sample.py'
    target.write_text(source)
    excerpt=extract_code(tmp_path,'sample.py','Agent.learn')
    assert excerpt['text'].startswith('def learn') and 'if terminal:' in excerpt['text']
    assert excerpt['source_sha256']==hashlib.sha256(source.encode()).hexdigest()
    assert excerpt['start_line']==2 and excerpt['end_line']==5
    ast.parse(excerpt['text'])
    with pytest.raises(ValueError):
        extract_code(tmp_path,'sample.py','Agent.missing')
    with pytest.raises(ValueError):
        extract_code(tmp_path,'../escape.py','Agent')


def test_exact_contiguous_excerpt_range(tmp_path):
    (tmp_path/'x.py').write_text('def eval():\n    q = 0\n    before = q\n    q = 1\n    return q\n')
    excerpt=extract_code(tmp_path,'x.py','eval',start='    before = q',end='    q = 1')
    assert excerpt['text']=='before = q\nq = 1'
    with pytest.raises(ValueError):
        extract_code(tmp_path,'x.py','eval',start='missing')


def manuscript():
    text='\n'.join(f'## {i}. Phần {i}\nNội dung.' for i in range(1,10))
    text+='\n'+'\n'.join(f'### 6.{i}. Câu {i} — Trả lời\nĐủ ý.' for i in range(1,11))
    text+='\n'+'\n'.join(f'![F{i:02d}](../../artifacts/figures/f{i:02d}.png)\nGiải thích hình F{i:02d}.' for i in range(1,21))
    return text


def test_nine_sections_ten_questions_twenty_images_and_no_placeholders():
    receipt=validate_structure(manuscript())
    assert receipt['sections']==9 and receipt['questions']==10 and receipt['figures']==20


@pytest.mark.parametrize('kind',['question','figure','placeholder','section'])
def test_missing_content_rejected(kind):
    text=manuscript()
    if kind=='question':
        text=text.replace('### 6.10. Câu 10','### Khác')
    elif kind=='figure':
        text=text.replace('![F20]','![Khác]')
    elif kind=='placeholder':
        text+='\n{{TODO}}'
    else:
        text=text.replace('## 9.','## Khác')
    with pytest.raises(ValueError):
        validate_structure(text)
