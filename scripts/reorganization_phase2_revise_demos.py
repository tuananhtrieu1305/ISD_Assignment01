"""Revise notebook demo entry points while keeping frozen experiment guards intact."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
P2=ROOT/'docs/reorganization/phase2'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,document):
    temporary=path.with_name(path.name+'.migration-tmp')
    temporary.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)

rows=[]
for project in ['tieuluan2','tieuluan3']:
    config=json.loads((ROOT/project/'project.json').read_text())
    for entry in config['notebooks']:
        path=ROOT/project/entry['path']
        if not any(part in path.parts for part in ['ch03_cnn','ch04_rnn','ch04_rnn_lstm']): continue
        before=sha(path)
        doc=json.loads(path.read_text())
        for cell in doc['cells']:
            if cell['cell_type']!='code': continue
            text=''.join(cell.get('source',[]))
            for old in ['from scripts.demo_phase27 import infer, sample_request','from scripts.demo_phase28 import sample_request, infer','from scripts.demo_phase29 import sample_request, infer']:
                text=text.replace(old,'from assignment_runtime.paper_demo import sample_request, infer')
            cell['source']=text.splitlines(keepends=True)
        doc['metadata']['migration_demo_revision']='r3: pinned serving registry seed42, NumPy CPU; historical Git HEAD guard unchanged'
        save(path,doc)
        rows.append({'project':project,'path':entry['path'],'previous_revision_sha256':before,'sha256':sha(path)})
save(P2/'demo_notebook_revision_r3.json',{'reason':'Frozen training-time Git HEAD differs from current repository HEAD; use existing pinned serving registry without changing original source/gate/seal or model weights','adapter':'_shared/assignment_runtime/paper_demo.py','notebooks':rows,'training_steps':0,'scientific_TEST_forward':0})
print('Revised',len(rows),'demo notebooks')
