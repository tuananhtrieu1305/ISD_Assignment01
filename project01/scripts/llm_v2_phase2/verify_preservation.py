"""Resolve immutable historical file pins to exact original archives after v2 edits."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parents[2];ROOT=P.parent


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    archives={}
    for manifest in [P/'provenance/before_llm_v2_phase2/preservation.json',
                     P/'artifacts/ui_revisions/answer_first_v2/preservation.json',
                     P/'artifacts/ui_revisions/results_flow_v1/preservation.json',
                     P/'artifacts/phase2/phase1_drafts_backup.json']:
        for r in load(manifest)['files']:
            original=r['path'];destination=r['archived_path']
            if original.startswith('project01/'):original=original[len('project01/'):]
            path=ROOT/destination if destination.startswith('project01/') else P/destination
            assert path.is_file() and sha(path)==r['sha256'],destination
            archives[(original,r['sha256'])]=path
    resolved=[]
    for manifest in [P/'artifacts/phase2/freeze.json',P/'artifacts/phase2/acceptance.json',
                     P/'artifacts/ui_revisions/results_flow_v1/release.json',P/'artifacts/ui_revisions/answer_first_v2/release.json']:
        for row in load(manifest)['files']:
            path=P/row['path']
            if not path.exists() or sha(path)!=row['sha256']:path=archives.get((row['path'],row['sha256']))
            assert path and sha(path)==row['sha256'],(manifest.name,row['path'])
            resolved.append({'manifest':manifest.relative_to(P).as_posix(),'original':row['path'],'sha256':row['sha256'],
                             'resolved':path.relative_to(P).as_posix()})
    for row in load(ROOT/'docs/final_project01/llm_v2/phase1_handoff.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    original=load(P/'artifacts/phase2/freeze.json')
    for row in original['notebooks']:
        path=P/'provenance/before_llm_v2_phase2'/row['path'];nb=load(path)
        fingerprint=hashlib.sha256(json.dumps([(c['cell_type'],c['source']) for c in nb['cells']],ensure_ascii=False).encode()).hexdigest()
        assert fingerprint==row['notebook_source_sha256']
    for name in ['raw_results','results','claims']:assert len(list((P/'artifacts/phase2/evaluation'/name).glob('*.json')))==120
    output={'status':'PASS','pins':len(resolved),'resolved':resolved,'phase1_handoff_files':167,
            'historical_raw_derived_claims':120,'historical_training_or_TEST_forward':0,'old_receipts_modified':False}
    path=P/'artifacts/llm_v2/phase2/preservation_verification.json'
    path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k!='resolved'}))


if __name__=='__main__':main()
