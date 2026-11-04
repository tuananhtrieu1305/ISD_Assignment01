"""Seal prepared inputs and update the mutable v2 dispatcher checkpoint only."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json

P=Path(__file__).resolve().parents[2];ROOT=P.parent
DOC=ROOT/'docs/final_project01/llm_v2'


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    handoff=DOC/'phase1_handoff.json'
    if handoff.exists():raise RuntimeError('Handoff exists; use revision')
    audit=load(P/'artifacts/llm_v2/phase1/acceptance.json')
    assert audit['status']=='PASS'
    files=[]
    directories=['datasets/llm_v2','artifacts/llm_v2','docs/llm_v2','scripts/llm_v2_phase1',
                 'environment/llm_v2','provenance/group_rag_kg_source','provenance/before_llm_v2_phase1']
    paths={p for name in directories for p in (P/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    paths|={P/'.gitignore',DOC/'phase1_report.md'}
    for path in sorted(paths):
        assert path.name!='.env'
        files.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size})
    dump(handoff,{'schema_version':'phase1-handoff-v1','date':datetime.now(timezone.utc).isoformat(),
        'status':'COMPLETE','files':files,'file_count':len(files),
        'active_corpus':'project01/datasets/llm_v2/chunks.jsonl','active_kg':'project01/artifacts/llm_v2/kg/seed_r2.json',
        'evaluation_protocol':'project01/docs/llm_v2/evaluation_protocol.md',
        'active_question_set':'project01/datasets/llm_v2/evaluation_v1/manifest.json',
        'reuse_map':'project01/docs/llm_v2/reuse_map.json',
        'provider':'gemini-3.8-flash via Interactions, embedding-001 768D; free_only',
        'quota_confirmation':'project01/artifacts/llm_v2/phase1/quota_user_confirmation.json',
        'phase2_requirements':['archive original notebook/UI/backend before edits and preserve old resolvers',
                               'install only small locked serving environment, not GPU envs',
                               'port group source from local snapshot into full notebook cells/export',
                               'implement quota-aware multi-day journal and refresh actual usage',
                               'development then freeze before 40x2 outputs; no old TEST/evaluation rerun',
                               'clean-start without reference folder, deletion only after Phase3 gate'],
        'source_reference_still_present':True,'source_runtime_independence_proven':False,
        'new_pipeline_web_or_benchmark_executed':False,'automatic_next_phase':False})
    for row in files:assert sha(ROOT/row['path'])==row['sha256']
    checkpoint=load(DOC/'checkpoint.json')
    checkpoint.update(status='IN_PROGRESS',active_phase=None,next_phase=2,completed_phases=[1],
      current_step='Phase 1 COMPLETE: source transfer, Gemini generation/embedding preflight, quota confirmed, corpus, source-checked mini-KG and 20+40 protocol ready. Await user request for Phase 2; no active worker.',
      active_processes=[],api_calls_this_plan=5)
    checkpoint['phases']['1'].update(status='COMPLETE',handoff='docs/final_project01/llm_v2/phase1_handoff.json')
    checkpoint['phases']['2']['status']='READY'
    checkpoint['completed_steps'] += [
      'Phase1 transferred36 source files, recorded21 omissions and resolved63 internal imports; original57 hashes checked',
      'Saved user-authorized key only in ignored project01/.env; secret scan PASS',
      'Generation Interactions gemini-3.8-flash PASS; embedding-001 768D PASS; earlier timeout/404 retained',
      'User confirmed free quotas and chose same model with multi-day evaluation',
      'Prepared new MedQuAD corpus45 docs/210 QA/316 chunks/409 refs with original URLs/offsets',
      'Curated mini-KG r2:35 entities/35 reviewed assertions/20 source chunks; first seed retained',
      'Authored new20 dev/40 held-out questions, references and rubric; zero model outputs',
      'Locked72 serving dependencies with existing WSL Python; no install or GPU env change',
      'Read-only old evidence and Phase1 input audits PASS; handoff hash read-back PASS']
    checkpoint['remaining_steps']=[
      'Phase2: archive and port local group snapshot into3 notebooks/export, isolated serving env, quota-aware RAG/KG+Gemini comparison/UI, development then freeze and multi-day40x2 evaluation; independent clean-start',
      'Phase3: integrate live implementation into tieuluan3 Chapter6/final DOCX, independence gate then delete only reference folder and smoke again']
    cfg=checkpoint['pending_configuration']
    cfg.update(generation_model_id='gemini-3.8-flash',embedding_model_id='gemini-embedding-001',
      generation_endpoint='v1beta/interactions',embedding_dimensions=768,
      key_probe_status='PASS_GENERATION_AND_EMBEDDING',credential_status='PRESENT_IN_IGNORED_PROJECT01_DOTENV',
      model_selection_status='ACCESS_PROBED_PUBLIC_FREE_TIER_AND_USER_QUOTA_CONFIRMED',
      project_tier_verification='USER_CONFIRMED_AI_STUDIO_FREE_QUOTA; INVOICE_NOT_INDEPENDENTLY_VERIFIED',
      quota={'generation':{'rpm':5,'tpm':250000,'rpd':20},'embedding':{'rpm':100,'tpm':30000,'rpd':1000}},
      user_selected_multi_day_evaluation=True,refresh_usage_before_next_session=True,
      request_when='Configuration ready; refresh usage at Phase2 start, do not request provider/budget/key again')
    checkpoint['evaluation'].update(status='QUESTIONS_AND_PROTOCOL_READY_NOT_RUN',actual_development_questions=20,
       actual_held_out_questions=40,model_outputs=0,protocol='project01/docs/llm_v2/evaluation_protocol.md',
       expected_generation_calls_nominal=200,expected_generation_calls_with_max_feedback=320)
    checkpoint['reference_review']['status']='TRANSFERRED_AND_PORT_MAP_READY'
    checkpoint['reference_cleanup']['phase1_transfer_status']='COMPLETE_36_COPIED_21_OMITTED_WITH_REASONS'
    checkpoint['mini_kg'].update(status='CURATED_SOURCE_CHECKED_SEED_R2_READY_RUNTIME_PENDING_PHASE2',
      active_seed='project01/artifacts/llm_v2/kg/seed_r2.json',entities=35,assertions=35,source_chunks=20,
      source_documents=17,automatic_extraction_calls=0,reviewer='Codex assistant; not clinical expert')
    checkpoint['api_usage_summary']={'http_requests':5,'model_list':1,'generation_attempts':3,'generation_successes':1,
      'embedding_attempts':1,'embedding_successes':1,'generation_timeout_usage':'unknown',
      'old_model_404_retained':True,'held_out_outputs':0,'paid_budget_usd':0,'actual_invoice_verified':False}
    checkpoint['last_updated']=datetime.now(timezone.utc).isoformat()
    dump(DOC/'checkpoint.json',checkpoint)
    print(json.dumps({'phase1':'COMPLETE','next_phase':2,'auto_started_phase2':False,
                       'handoff_files':len(files),'handoff_readback':'PASS','api_requests':5,'held_out_outputs':0}))


if __name__=='__main__':main()
