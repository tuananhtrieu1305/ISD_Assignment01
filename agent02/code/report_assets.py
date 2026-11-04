"""Pure helpers for source-faithful report assembly; no scientific runner imports."""

import ast
import hashlib
import math
import re
import textwrap
from pathlib import Path


def decimal_vi(value, digits=5, *, group=False):
    number=float(value)
    if not math.isfinite(number):
        raise ValueError('Report numbers must be finite')
    formatted=format(number,(',' if group else '')+f'.{digits}f')
    return formatted.replace(',','_').replace('.',',').replace('_','.')


def markdown_table(headers, rows):
    def cells(values):
        return '|'+ '|'.join(str(v).replace('|','\\|').replace('\n',' ') for v in values)+'|'
    if any(len(row)!=len(headers) for row in rows):
        raise ValueError('Table row width differs')
    return '\n'.join([cells(headers),cells(['---']*len(headers)),*[cells(row) for row in rows]])


def render_tokens(template, values):
    used=[]
    def replace(match):
        key=match[1]
        if key not in values:
            raise ValueError('Unknown report token:'+key)
        used.append(key)
        return str(values[key])
    result=re.sub(r'\{\{([\w.:-]+)\}\}',replace,template)
    if '{{' in result or '}}' in result:
        raise ValueError('Unresolved/nested report token')
    return result,used


def readable_prose(text):
    """Add missing prose spaces while preserving code, IDs, paths and template tokens."""
    protected=(r'(```[\s\S]*?```|`[^`\n]+`|\{\{[^}]+\}\}|'
        r'\b(?:[A-Z]\d{2}[A-Z]+\d+|(?:Agent|AGENT|AG)\d+|REF\d+|CONTROLLED\d+|[FSDBE]\d{1,2}|Q(?:0?[0-9]|10)|float64|SHA256|PCG64|\d{4}\.\d{4,5}(?:v\d+)?)\b|'
        r'https?://\S+|\b(?:sources|artifacts|evidence|report|code|data|docs)/[A-Za-z0-9_./-]+)')
    parts=re.split(protected,text)
    for i in range(0,len(parts),2):
        value=parts[i]
        value=re.sub(r'(?<=[^\W\d_])(?=\d)',' ',value)
        value=re.sub(r'(?<=\d)(?=[^\W\d_])',' ',value)
        value=value.replace('×',' × ').replace('→',' → ')
        for old,new in [('Xepisode','X là episode'),('Xcấu','X là cấu'),('Xnămcấu','X là năm cấu'),
                        ('Xnăm','X là năm'),('Yprofit','Y là profit'),('Ymeanprofit','Y là mean profit'),
                        ('Ytỷ','Y là tỷ'),('Yxác','Y là xác'),('Ychênhprofit','Y là chênh profit'),
                        ('whiskerstd','whisker là std'),('meanprofit','mean profit'),('fixedrule','fixed rule')]:
            value=value.replace(old,new)
        parts[i]=re.sub(r' {2,}',' ',value)
    return ''.join(parts)


def extract_code(base, relative, symbol, *, start=None, end=None):
    root=Path(base).resolve()
    target=(root/relative).resolve()
    if not target.is_relative_to(root):
        raise ValueError('Source path escapes assignment')
    raw=target.read_bytes()
    source=raw.decode('utf-8')
    nodes=ast.parse(source).body
    selected=None
    for name in symbol.split('.'):
        selected=next((node for node in nodes if getattr(node,'name',None)==name),None)
        if selected is None:
            raise ValueError('Source symbol missing:'+symbol)
        nodes=getattr(selected,'body',[])
    lines=source.splitlines()
    first,last=selected.lineno,selected.end_lineno
    fragment=lines[first-1:last]
    if start is not None:
        matches=[i for i,line in enumerate(fragment) if line==start]
        if len(matches)!=1:
            raise ValueError('Excerpt start must occur exactly once')
        first+=matches[0]
    if end is not None:
        matches=[i for i,line in enumerate(fragment) if line==end]
        if len(matches)!=1:
            raise ValueError('Excerpt end must occur exactly once')
        last=selected.lineno+matches[0]
    if last<first:
        raise ValueError('Excerpt range reversed')
    text=textwrap.dedent('\n'.join(lines[first-1:last]))
    return {'path':relative,'symbol':symbol,'start_line':first,'end_line':last,'text':text,
        'source_sha256':hashlib.sha256(raw).hexdigest(),'excerpt_sha256':hashlib.sha256(text.encode()).hexdigest()}


def validate_structure(text):
    sections=re.findall(r'^## ([1-9])\. ',text,re.MULTILINE)
    questions=re.findall(r'^### 6\.(\d+)\. Câu (\d+)\b',text,re.MULTILINE)
    figures=re.findall(r'!\[F(\d{2})\]',text)
    if sections!=[str(i) for i in range(1,10)]:
        raise ValueError('Require exactly nine ordered report sections')
    if questions!=[(str(i),str(i)) for i in range(1,11)]:
        raise ValueError('Require ten ordered question answers')
    if sorted(figures)!=[f'{i:02d}' for i in range(1,21)]:
        raise ValueError('Require twenty unique explained figures')
    if '{{' in text or '}}' in text or re.search(r'\b(TODO|TBD|PLACEHOLDER)\b',text):
        raise ValueError('No unresolved content placeholders')
    return {'sections':9,'questions':10,'figures':20}
