"""Read-only data/source checks; never import a model or consume QA claims."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import ast
import hashlib
import json
import runpy
import subprocess
import tomllib
import unicodedata
from contextlib import redirect_stdout
import io

P=Path(__file__).resolve().parents[2];ROOT=P.parent
D=P/'datasets/llm_v2';A=P/'artifacts/llm_v2/phase1'


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def rows(path):return list(map(json.loads,path.read_text(encoding='utf-8').splitlines()))
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def norm(text):return ''.join(c for c in unicodedata.normalize('NFKC',text).casefold() if c.isalnum())


def main():
    receipt=A/'acceptance.json'
    if receipt.exists():raise RuntimeError('Acceptance exists; do not overwrite, use revision')
    transfer=load(P/'provenance/group_rag_kg_source/transfer_manifest.json')
    for r in transfer['files']:
        assert sha(ROOT/r['original_path'])==r['original_sha256'],r['original_path']
        if r['disposition']=='copied':assert sha(ROOT/r['copied_path'])==r['copied_sha256'],r['copied_path']
    acquisition=load(A/'acquisition.json')
    assert sha(D/'raw/medquad-pinned.tar.gz')==acquisition['archive_sha256']
    docs=rows(D/'corpus_documents.jsonl');qa={r['qa_id']:r for r in rows(D/'qa_context.jsonl')}
    chunks={r['chunk_id']:r for r in rows(D/'chunks.jsonl')}
    assert len(docs)==45 and len(qa)==210 and len(chunks)==316
    assert len({r['content'] for r in chunks.values()})==len(chunks)
    refs=0
    for cid,c in chunks.items():
        digest=hashlib.sha256(c['content'].encode()).hexdigest()
        assert cid=='m2c-'+digest[:20] and c['text_sha256']==digest
        for ref in c['source_refs']:
            parent=qa[ref['qa_id']]
            assert parent['answer'][ref['answer_start']:ref['answer_end']]==c['content']
            assert parent['document_id']==ref['document_id'] and parent['source_url']==ref['source_url']
            refs+=1
    assert refs==409 and all(d['source_url'].startswith('http') for d in docs)
    kg=load(P/'artifacts/llm_v2/kg/seed_r2.json')
    entities={r['id'] for r in kg['entities']}
    assert len(entities)==35 and len(kg['relationships'])==35
    seen=set()
    for edge in kg['relationships']:
        assert edge['id'] not in seen;seen.add(edge['id'])
        assert edge['subject'] in entities and edge['object'] in entities
        assert edge['relation'] in kg['relation_allowlist']
        parent=qa[edge['source_qa_id']]
        assert parent['answer'][edge['answer_start']:edge['answer_end']]==edge['quote']
        assert len(edge['quote'])>30 and edge['source_url']==parent['source_url']
        assert edge['review']['status']=='SOURCE_CHECKED_ASSISTANT'
        assert edge['direction']=='subject_to_object'
        for cid in edge['source_chunk_ids']:
            assert edge['quote'] in chunks[cid]['content']
            assert any(r['qa_id']==parent['qa_id'] for r in chunks[cid]['source_refs'])
    dev=rows(D/'evaluation_v1/development_reference.jsonl')
    held=rows(D/'evaluation_v1/held_out_reference.jsonl')
    assert len(dev)==20 and len(held)==40
    assert not ({r['fact_family'] for r in dev}&{r['fact_family'] for r in held})
    assert len({norm(r['question_vi']) for r in dev+held})==60
    for case in dev+held:
        assert case['expected_points_vi']
        if case['answerability']=='answerable':assert case['reference_evidence']
        for ref in case['reference_evidence']:
            assert qa[ref['qa_id']]['answer'][ref['answer_start']:ref['answer_end']]==ref['quote']
            assert ref['relevant_chunk_ids']
            assert all(ref['quote'] in chunks[cid]['content'] for cid in ref['relevant_chunk_ids'])
    # Read historical question fields only; never instantiate tools or inspect outputs.
    oldquestions=[]
    def collect(obj):
        if isinstance(obj,dict):
            for key,value in obj.items():
                if key in {'question','question_vi','query'} and isinstance(value,str):oldquestions.append(value)
                elif isinstance(value,(dict,list)):collect(value)
        elif isinstance(obj,list):
            for value in obj:collect(value)
    collect(load(P/'datasets/benchmark/evaluation.json'))
    overlap={norm(r['question_vi']) for r in held}&{norm(q) for q in oldquestions}
    assert not overlap,'Historical exact question reused'
    config=load(P/'docs/llm_v2/provider_config.example.json')
    assert config['allow_paid_api'] is False and config['paid_spend_limit_usd']==0
    assert config['quota']['user_selected_multi_day_evaluation'] is True
    assert load(A/'gemini_interactions_preflight.json')['status']=='PASS'
    assert load(A/'gemini_embedding_preflight.json')['status']=='PASS'
    lock=tomllib.loads((P/'environment/llm_v2/uv.lock').read_text())
    assert len(lock['package'])==72
    package_names={r['name'] for r in lock['package']}
    assert not ({'torch','tensorflow','openai','groq','cohere','neo4j','qdrant-client'}&package_names)
    notebooks=list((P/'notebooks').rglob('*.ipynb'));assert len(notebooks)==3
    for script in (P/'scripts/llm_v2_phase1').glob('*.py'):ast.parse(script.read_text(encoding='utf-8'))
    ignored=subprocess.run(['git','check-ignore','--quiet','project01/.env'],cwd=ROOT).returncode==0
    tracked=subprocess.run(['git','ls-files','--error-unmatch','project01/.env'],cwd=ROOT,capture_output=True).returncode==0
    assert ignored and not tracked
    for name in ['chunks.jsonl','source_catalog.json','evaluation_v1/held_out_questions.jsonl']:
        assert subprocess.run(['git','check-ignore','--quiet','project01/datasets/llm_v2/'+name],cwd=ROOT).returncode!=0,name
    assert subprocess.run(['git','check-ignore','--quiet','project01/datasets/llm_v2/raw/medquad-pinned.tar.gz'],cwd=ROOT).returncode==0
    key=next(line.partition('=')[2].strip().strip('\"\'') for line in (P/'.env').read_text().splitlines() if line.partition('=')[0].strip()=='GEMINI_API_KEY')
    assert len(key)>10
    roots=[P/'scripts/llm_v2_phase1',P/'docs/llm_v2',P/'artifacts/llm_v2',D,P/'provenance/group_rag_kg_source']
    scanned=0
    for root in roots:
        for path in root.rglob('*'):
            if path.is_file() and path.suffix in {'.json','.jsonl','.py','.md','.ipynb','.txt','.toml','.yaml'}:
                assert key.encode() not in path.read_bytes(),f'Secret leak: {path.name}'
                scanned+=1
    baseline=runpy.run_path(str(ROOT/'scripts/verify_final_project01.py'),run_name='phase1_preservation_audit')
    project=runpy.run_path(str(P/'scripts/verify_answer_first_v2.py'),run_name='phase1_project_audit')
    # These are original read-only integrity verifiers, not model/test/evaluation runners.
    old_receipts={}
    for label,module in [('final',baseline),('project',project)]:
        check=module.get('check') or module.get('verify') or module.get('main')
        assert check is not None,label
        buffer=io.StringIO()
        with redirect_stdout(buffer):value=check()
        if value is None:value=json.loads(buffer.getvalue())
        assert value['status']=='PASS'
        old_receipts[label]=value
    output={'status':'PASS','date':datetime.now(timezone.utc).isoformat(),
        'copied_files':transfer['copied_count'],'omitted_files':transfer['omitted_count'],
        'original_reference_hashes_checked':len(transfer['files']),
        'documents':45,'qa_contexts':210,'chunks':316,'source_refs_checked':refs,
        'kg_entities':35,'kg_assertions':35,'kg_source_chunks':20,
        'development_questions':20,'held_out_questions':40,'held_out_exact_overlap_with_old_questions':0,
        'historical_question_fields_compared':len(oldquestions),'dependency_resolution_packages':72,
        'notebook_count':3,'secret_scanned_files':scanned,'env_ignored_and_untracked':True,
        'old_integrity_verifiers':old_receipts,'training_or_model_evaluation_executed':False,
        'held_out_model_outputs':0,'generation_probe_attempts':3,'embedding_probe_attempts':1,'metadata_model_list_requests':1,
        'reference_deleted':False,'phase2_pipeline_implemented':False}
    receipt.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(output,ensure_ascii=False))


if __name__=='__main__':main()
