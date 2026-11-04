"""Development edits only in canonical notebook cells, followed by one-way export."""
from pathlib import Path
import json,sys
from notebooks import GROUPS,export,load,save
P=Path(__file__).resolve().parents[2]
patches=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
if (P/'artifacts/llm_v2/phase2/freeze.json').exists():raise RuntimeError('Frozen; requires declared revision')
for patch in patches:
    filename=next(f for f,names in GROUPS.items() if patch['module'] in names)
    path=P/'notebooks'/filename;nb=load(path);count=0
    for cell in nb['cells']:
        source=''.join(cell['source'])
        if source.startswith('%%llm_v2_module project01_llm_v2.'+patch['module']+'\n'):
            count+=source.count(patch['old']);source=source.replace(patch['old'],patch['new']);cell['source']=source.splitlines(keepends=True)
    assert count==patch['count'],(patch['module'],count)
    save(path,nb)
export()
