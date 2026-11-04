"""Web-only migration revisions; original scientific/model bytes are untouched."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
P3=ROOT/'docs/reorganization/phase3'
changes=[]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def revise(path,text):
    before=sha(path)
    original=ROOT/path.parts[len(ROOT.parts)]/'provenance/phase3_originals'/path.relative_to(ROOT).relative_to(path.parts[len(ROOT.parts)])
    original.parent.mkdir(parents=True,exist_ok=True)
    if not original.exists():shutil.copyfile(path,original)
    tmp=path.with_name(path.name+'.phase3-tmp');tmp.write_text(text,encoding='utf-8');tmp.replace(path)
    changes.append({'path':path.relative_to(ROOT).as_posix(),'before_sha256':before,'after_sha256':sha(path),'original':original.relative_to(ROOT).as_posix()})
for project in ['tieuluan2','tieuluan3']:
    p=ROOT/project/'web/frontend/src/v3/App.tsx'
    revise(p,p.read_text(encoding='utf-8').replace('import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000"','import.meta.env.VITE_API_BASE_URL || window.location.origin'))
p=ROOT/'tieuluan1/web/frontend/src/api/predictionApi.ts'
revise(p,p.read_text(encoding='utf-8').replace('if (!configured) return "http://127.0.0.1:5000";','if (!configured) return window.location.origin;'))
for project,filename in [('agent01','Discovering_AI_Agent.ipynb'),('agent02','AG02_Code_and_Results.ipynb')]:
    p=ROOT/project/'web'/filename
    revise(p,(ROOT/project/'notebooks'/filename).read_text(encoding='utf-8'))
    note=ROOT/project/'web/MIGRATION.md'
    note.write_text('''# Web sau migration

Demo giữ dữ liệu/trace/figure gốc. Notebook download là revision đang dùng trong notebooks/, có bootstrap tên bài mới; cần mở trong repository với kernel WSL đúng hướng dẫn. Bản notebook web trước migration vẫn giữ trong provenance/phase3_originals/web/.

Chạy từ root: `./scripts/run_web.ps1 -Project '''+project+'''`. Hoặc static server chỉ trỏ vào web/: không public thư mục raw/checkpoint/provenance. Không có train/TEST mới trên web.
''',encoding='utf-8')
(P3/'web_revisions.json').write_text(json.dumps({'changes':changes,'models_retrained':False,'scientific_TEST_forward':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Web revisions:',len(changes))
