"""Apply the declared mechanical JSX edits once; original UI is archived in r8."""
from pathlib import Path
import json
P=Path(__file__).resolve().parents[2]
path=P/'web/frontend/src/main.jsx'
source=path.read_text(encoding='utf-8')
for item in json.loads((Path(__file__).with_name('full_demo_r8_ui_patches.json')).read_text(encoding='utf-8')):
    assert source.count(item['old'])==1,item['old']
    source=source.replace(item['old'],item['new'])
path.write_text(source,encoding='utf-8')
