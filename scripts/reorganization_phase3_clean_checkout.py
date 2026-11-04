"""Verify declared serving payload from a source-only checkout, without raw/runtime views."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
P3=ROOT/'docs/reorganization/phase3'
temp=Path(tempfile.mkdtemp(prefix='assign-reorg-phase3-',dir='/tmp'))
rows=[]
for project in ['tieuluan1','tieuluan2','tieuluan3']:
    source=ROOT/project/'web/deploy/release.json'
    release=json.loads(source.read_text())
    allow=[source.relative_to(ROOT).as_posix(),release['archive']['path'],'scripts/render_project.py','tieuluan3/scripts/render_v3.py',*[r['path'] for r in release['source_python']]]
    for name in set(allow):
        target=temp/name;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==(ROOT/name).read_bytes()
        else:shutil.copyfile(ROOT/name,target)
    command=[sys.executable,'-B',str(temp/'scripts/render_project.py'),'check','--project',project]
    result=subprocess.run(command,cwd=temp,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'},capture_output=True,text=True,timeout=300)
    row={'project':project,'status':'PASS' if result.returncode==0 else 'FAIL','source_file_allowlist':len(set(allow)),'stdout':result.stdout[-3000:],'stderr':result.stderr[-5000:],'raw_copied':False,'runtime_views_copied':False,'GPU_environment_installed':False,'pip_install_executed':False}
    rows.append(row)
    (P3/'clean_checkout.json').write_text(json.dumps({'status':'PASS' if all(r['status']=='PASS' for r in rows) and len(rows)==3 else 'IN_PROGRESS','projects':rows,'temporary_checkout':str(temp),'scope':'Source-only Linux filesystem tree + declared serving archives; validation in existing pinned CPU interpreter, no dependency reinstall'},indent=2)+'\n')
    print(project,row['status'],flush=True)
    if result.returncode:raise RuntimeError(result.stderr[-3000:])
assert temp.parent==Path('/tmp') and temp.name.startswith('assign-reorg-phase3-')
shutil.rmtree(temp)
