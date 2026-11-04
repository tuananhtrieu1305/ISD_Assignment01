"""Assemble project-only workspace; no reference/provenance or secret is supplied."""
from pathlib import Path
import hashlib,json,shutil,sqlite3,subprocess,sys,time
P=Path(__file__).resolve().parents[2];ROOT=P.parent
target=ROOT/'.local/llm-v2-clean-start'/('run-'+str(time.time_ns()))/'project01';target.mkdir(parents=True)
files=[]
files += [p for p in (P/'web/backend/project01_llm_v2').glob('*.py')]
files += [P/'web/backend/app.py']
files += [p for p in (P/'web/frontend').rglob('*') if p.is_file() and not p.name.startswith('.env') and not any(s in p.parts for s in ['node_modules','dist','.runtime'])]
files += list((P/'notebooks').glob('*.ipynb'))
for relative in ['docs/llm_v2/provider_config.example.json','docs/llm_v2/runtime_config.json','datasets/llm_v2/chunks.jsonl',
                 'datasets/demo_profiles.json','datasets/profile_schema.json','artifacts/llm_v2/kg/seed_r2.json']:
    files.append(P/relative)
for name in ['model.npz','model_config.json','preprocessing.json','profile_schema.json','manifest.json']:files.append(P/'artifacts/package/v1'/name)
for path in (P/'artifacts/llm_v2/index').rglob('*'):
    if path.is_file() and path.suffix in {'.json'} and path.name not in {'progress.json'}:files.append(path)
for path in (P/'artifacts/llm_v2/phase2/development').glob('v2-dev-*.json'):files.append(path)
records=[]
for source in files:
    dest=target/source.relative_to(P);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    records.append({'path':source.relative_to(P).as_posix(),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
dbdest=target/'artifacts/llm_v2/runtime/calls.sqlite3';dbdest.parent.mkdir(parents=True,exist_ok=True)
with sqlite3.connect(P/'artifacts/llm_v2/runtime/calls.sqlite3') as original,sqlite3.connect(dbdest) as copied:original.backup(copied)
child=target/'scripts/clean_child.py';child.parent.mkdir(parents=True)
shutil.copyfile(Path(__file__).with_name('clean_child.py'),child)
assert not (target/'.env').exists() and not (target/'provenance').exists()
result=subprocess.run([sys.executable,'-I','-B',str(child)],cwd=target,capture_output=True,text=True)
if result.returncode:
    print(result.stdout);print(result.stderr);raise RuntimeError('Clean workspace failed')
proof=json.loads(result.stdout.strip().splitlines()[-1])
output={'status':'PASS','workspace':target.relative_to(ROOT).as_posix(),'files':records,'reference_folder_present':False,
        'provenance_present':False,'secret_file_present':False,'child':proof,'cloud_deployed':False}
receipt=P/'artifacts/llm_v2/phase2'/('clean_start_'+target.parent.name+'.json')
receipt.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
(P/'artifacts/llm_v2/phase2/clean_start_active.json').write_text(json.dumps({'receipt':receipt.relative_to(P).as_posix()})+'\n')
print(json.dumps({k:v for k,v in output.items() if k!='files'}))
