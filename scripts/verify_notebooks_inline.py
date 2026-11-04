"""Read-only verification of current notebooks and archived pre-revision evidence."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/notebook_revision/v1'

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    failures=[];verified=0;archive_map={}
    for filename in ['backup.json','presentation_backup.json']:
        for record in load(OUT/filename)['files']:
            archive_map.setdefault(record['path'],[]).append(record['archived_path'])
            path=ROOT/record['archived_path']
            assert path.is_file() and sha(path)==record['sha256'],record['archived_path']
    def check(record,historical=False):
        nonlocal verified
        candidates=[record['path']]+(archive_map.get(record['path'],[]) if historical else [])
        for candidate in candidates:
            path=ROOT/candidate
            if not path.resolve().is_relative_to(ROOT):continue
            if path.is_file() and ('bytes' not in record or path.stat().st_size==record['bytes']) and sha(path)==record['sha256']:
                verified+=1;return
        failures.append(record['path'])
    handoffs={}
    for phase in [1,2,3]:
        handoff=load(ROOT/f'docs/reorganization/phase{phase}_handoff.json')
        assert handoff['status']=='COMPLETE'
        for record in handoff['files']:check(record,historical=True)
        handoffs[str(phase)]=len(handoff['files'])
    for build in load(ROOT/'docs/reorganization/phase3/build_verification.json')['projects']:
        for record in build['frontend_source']+build['dist']:check(record)
    for name in ['tieuluan1','tieuluan2','tieuluan3']:
        release=load(ROOT/name/'web/deploy/release.json')
        check(release['archive'])
        for record in release['source_python']:check(record)
    counts={};sources={}
    manifest=load(OUT/'manifest.json')
    execution=load(OUT/'execution.json')
    assert execution['status']=='PASS'
    ran={(r['project'],r['path'],r['framework'],r['sha256']) for r in execution['runs'] if r['status']=='PASS'}
    for project in manifest['projects']:
        name=project['project'];config=load(ROOT/name/'project.json')
        assert config['notebooks']==project['notebooks'],name
        actual={p.relative_to(ROOT/name).as_posix() for p in (ROOT/name/'notebooks').rglob('*.ipynb')}
        expected={r['path'] for r in config['notebooks']}
        assert actual==expected and 1<=len(actual)<=4,(name,actual,expected)
        counts[name]=len(actual)
        for entry in config['notebooks']:
            path=ROOT/name/entry['path'];check({'path':name+'/'+entry['path'],'sha256':entry['sha256']})
            document=load(path)
            for record in document.get('metadata',{}).get('notebook_revision',{}).get('embedded_modules',[]):
                sources[record['source']]=record['sha256']
            if name in {'A01','A02','A03','agent01'}:continue
            frameworks=entry.get('supported_frameworks',[entry['framework']])
            if name in {'tieuluan2','tieuluan3'} and not any(t in entry['path'] for t in ['ML','CNN','RNN']):frameworks=['torch']
            for framework in frameworks:assert (name,entry['path'],framework,entry['sha256']) in ran,(name,entry['path'],framework)
    for path,digest in sources.items():check({'path':path,'sha256':digest})
    for record in load(OUT/'web_downloads.json')['files']:check(record)
    for name in ['A01','A02','A03','A04','A05','A06','agent01','agent02']:
        release=load(ROOT/name/'web/release-reorg.json')
        for record in release['assets']+release['notebook_downloads']:check(record)
    for filename in ['static_check.json','web_check.json','kernel_check.json']:
        assert load(OUT/filename)['status']=='PASS',filename
    for run in load(OUT/'kernel_check.json')['runs']:
        check({'path':run['project']+'/'+run['source'],'sha256':run['sha256']})
        output=(ROOT/run['output']).resolve()
        assert output.is_relative_to(ROOT/run['project']/'artifacts/notebook_runs') and output.is_file()
        assert not any(o.get('output_type')=='error' for c in load(output)['cells'] for o in c.get('outputs',[]))
    handoff=OUT/'handoff.json'
    if handoff.exists():
        for record in load(handoff)['files']:check(record)
    report={'status':'FAIL' if failures else 'PASS','project_counts':counts,'notebook_count':sum(counts.values()),'preserved_reorg_handoff_files':handoffs,'verified_records':verified,'unique_original_python_sources':len(sources),'fresh_framework_executions':len(ran),'failures':failures,'training_steps':0,'scientific_TEST_forward':0}
    print(json.dumps(report,ensure_ascii=False))
    return bool(failures)

if __name__=='__main__':raise SystemExit(main())
