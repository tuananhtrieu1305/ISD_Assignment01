"""Write Phase-1 contracts, source port map and source catalogs; no inference."""
from pathlib import Path
import json
import hashlib
import tomllib

P=Path(__file__).resolve().parents[2]
ROOT=P.parent
D=P/'datasets/llm_v2'
DOC=P/'docs/llm_v2'
A=P/'artifacts/llm_v2/phase1'


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def rows(path):return list(map(json.loads,path.read_text(encoding='utf-8').splitlines()))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):
    if path.exists():raise RuntimeError(f'Input exists: {path.name}')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    config={
      'config_version':'llm-v2-phase1','status':'DESIGN_READY_NOT_PIPELINE_IMPLEMENTED',
      'provider':'google_ai_studio_gemini_developer_api','key_env':'GEMINI_API_KEY','allow_paid_api':False,
      'paid_spend_limit_usd':0,'generation_model':'gemini-3.8-flash','endpoint':'v1beta/interactions',
      'store':False,'temperature':0,'thinking_level':'low','external_tools':[],
      'embedding':{'model':'gemini-embedding-001','dimensions':768,'normalize':'L2',
                   'document_task':'RETRIEVAL_DOCUMENT','query_task':'RETRIEVAL_QUERY','cache':'model+dimension+task+text_sha256'},
      'quota':{'source':'user AI Studio readings in conversation, 2026-11-02; not a quota discovery API',
               'tier':'free_only_user_confirmed','generation':{'rpm':5,'tpm':250000,'rpd':20},
               'embedding':{'rpm':100,'tpm':30000,'rpd':1000},
               'application_caps':{'generation_rpm':4,'generation_rpd':18,'embedding_rpm':60,'embedding_rpd':900},
               'observed_usage_user_snapshot':{'generation_rpm':1,'generation_tpm':6,'generation_rpd':2,
                                               'embedding_rpm':0,'embedding_tpm':0,'embedding_rpd':0},
               'embedding_probe_after_snapshot':1,'provider_reset_timezone':'America/Los_Angeles',
               'refresh_usage_before_session':True,'external_usage_not_fully_visible_to_app':True,
               'user_selected_multi_day_evaluation':True,'no_key_rotation_to_evade_quota':True},
      'queue':{'concurrency':1,'request_timeout_seconds':90,'comparison_deadline_seconds':900,
               'max_minute_limit_retries':2,'max_retry_wait_seconds_per_attempt':60,
               'daily_quota_action':'checkpoint_stop_no_paid_fallback','timeout_after_send':'unknown_do_not_automatically_replay_evaluation_claim'},
      'pipeline':{'candidate_top_k':20,'evidence_top_n':6,'max_queries':3,'rrf_k':60,
                  'weights':{'dense':0.4,'sparse':0.4,'kg':0.2},'kg_default_hops':1,'kg_max_hops':2,
                  'max_feedback_rounds':1,'generation_calls_nominal_per_rag':4,'generation_calls_max_feedback_per_rag':7},
      'token_limits':{'answer_output':768,'planner_output':512,'reranker_output':768,'verifier_output':768,
                      'source_context_max_characters':24000,'usage_missing_value':None},
      'run_api_default':False,'run_evaluation_default':False,'run_training_default':False,
      'evaluation_outputs':80,'evaluation_phase':2,
      'corpus':'datasets/llm_v2/chunks.jsonl','kg_seed':'artifacts/llm_v2/kg/seed_r2.json',
      'historical_score_reused':False,'requires_phase2_model_prompt_index_freeze':True}
    dump(DOC/'provider_config.example.json',config)
    contracts={
      'schema_version':'llm-v2-contract-v1','additional_properties':'reject unless explicitly versioned',
      'QueryPlan':{'required':['original_question','language','intent','queries','entity_ids','relation_direction','scope'],
                    'intent':['knowledge','risk','combined','out_of_scope'],'queries':'1..3 strings; preserve original and negation',
                    'entity_ids':'allowlisted canonical IDs; unknown not invented','relation_direction':'subject,relation,object,negated,conditions'},
      'Evidence':{'required':['chunk_id','content','source_refs','ranks','retrieval_channels'],
                  'source_refs':'document_id,qa_id,title,section,source_url,snapshot_url,answer_start,answer_end',
                  'ranks':'dense_rank,sparse_rank,kg_rank,rrf_score,original_rank,rerank_score',
                  'graph_support':'assertion_ids,quote,source_chunk_ids,direction,conditions; optional'},
      'Claim':{'required':['id','text_vi','citation_chunk_ids'],'citation_chunk_ids':'subset of supplied evidence IDs',
               'clinical_numbers':'must be exact source or immutable server CDC value, not generated probability'},
      'Draft':{'required':['answer_vi','claims','limitations'],'answer_vi':'direct answer first; 768 output token cap'},
      'Verification':{'required':['approved','claim_reviews','direction_ok','numeric_ok','source_integrity_ok','feedback'],
                       'claim_reviews':'claim_id + supported/partial/unsupported/contradicted + evidence_ids',
                       'release_rule':'release exact approved draft or explicit evidence-limited answer; no free rewrite after verification'},
      'Usage':{'required':['model_requested','model_returned','endpoint','attempts','latency_ms','cache_status','usage_source'],
               'optional_nullable':['input_tokens','output_tokens','thought_tokens','cached_tokens','total_tokens'],
               'cache_status':['live','local_cache'],'usage_source':['provider','estimate','unavailable'],
               'cost':'free-tier configured USD=0; invoice verification separate'},
      'Result':{'required':['variant','status','answer_vi','claims','citations','usage','latency_ms','freeze_id'],
                 'variant':['llm_direct','agentic_rag'],
                 'status':['complete','limited_evidence','waiting_quota','provider_error','timeout','verification_failed'],
                 'direct_claim_citations':'optional; do not invent internal citations',
                 'risk_tool':'optional immutable CDC score + task/limitations; not personal incidence probability'},
      'CompareJob':{'states':['queued','running','waiting_quota','complete','partial','failed'],
                    'polling':'separate partial branch status; never label unverified streaming draft as approved'},
      'validation_required_phase2':['schema','all IDs resolve','quote exact span','directed relation and qualifiers',
                                    'claim support','prompt-injection data isolation','frozen CDC score identity',
                                    'shared queue/deadline/quota','no secret in public result']}
    dump(DOC/'contracts.json',contracts)
    mapping=[
      ('retrieval/pre_retrieval.py','QueryStrategy/_parse_lines, QueryRewriting, QueryDecomposition, QueryExpansion, PreRetriever',
       'Keep strategy flow/parser; injected Gemini bridge; remove hardwired ChatOpenAI; medical prompt, cap3, shared Coordinator call','01','query'),
      ('retrieval/hybrid_searcher.py','HybridSearcher.search/_dense_search/_sparse_search/_fuse',
       'Keep rank fusion and metadata; extend KG ranks; local NumPy store; shared queue no API fan-out','01','hybrid'),
      ('retrieval/retriever.py','Retriever._prepare_queries/retrieve/_merge_results',
       'Keep query preparation/dedup and max-score merge initially; enforce query/candidate cap; no hidden provider calls','01','retriever'),
      ('database/bm25_store.py','BM25Store.build/search/save/load/_tokenize/_text_for_index',
       'Port implementation; medical metadata, new fingerprinted index; do not load legal pickle','01','bm25'),
      ('indexing/chunking.py','DocumentChunker.split_markdown/split_file/_validate_chunk_config',
       'Keep section-first/overlap split and interface; medical section/QA boundaries, exact offsets/content IDs; validate against phase1 prepared data','01','indexing'),
      ('indexing/indexer.py','DocumentIndexer.index_file/_index_dense_chunks/_text_for_embedding/_chunk_payload',
       'Keep index flow/payload builder; content+corpus+embedding fingerprint, no document-id-only stale skip','01','indexing'),
      ('indexing/embedding.py','Embedder.embed_text/embed_batch',
       'Keep async interface; Gemini embedding SDK via queue; 768 dimensions, task-specific L2 vectors and hash cache; no BGE weight download','01','embedding'),
      ('database/vector_db.py','VectorDBClient query/upsert interface',
       'Local NumPy implementation adapter; retain interface, omit Qdrant connection/singleton','01','vector_store'),
      ('retrieval/reranker.py','BaseReranker.rerank/_to_ranked_result and RankedResult',
       'Keep interface/conversion/original_rank; add GeminiReranker and JSON validation; remove top-level CrossEncoder import; no mandatory Cohere/BGE','01','reranker'),
      ('generation/prompt.py','PromptBuilder.build_messages/build_context/_format_source',
       'Keep numbered-source formatting and call flow; medical Vietnamese prompt/claim citations; untrusted-evidence delimiters','02','generation'),
      ('generation/generator.py','BaseGenerator.generate/_extract_text, GeminiGenerator',
       'Keep generation flow/interface; _create_llm shared SDK Interactions bridge compatible with LangChain; typed claims+usage; remove OpenAIGenerator active path','02','generation'),
      ('pipeline.py','ChatbotPipeline.ask',
       'Keep retrieve→rerank→generate composition; expose stages to Knowledge/Reporter; add frozen Risk and Verifier without double generation','02','agents'),
      ('api/schemas.py','APIModel/MetaData/Chunk/SearchResult/RankedResult/SourceResponse',
       'Keep Pydantic base and inheritance; replace legal fields with source refs, add KG/claim/usage contract','01','schemas'),
      ('core/config.py','settings factory structure',
       'Use explicit config injection; remove legal/provider globals requiring external credentials at import','02','provider'),
      ('core/logging.py','get_logger',
       'Retain logging interface with redaction; avoid logging raw profile/key/request body','02','provider'),
    ]
    nb={'01':'01_Data_KB_RAG.ipynb','02':'02_Diabetes_Multi_Agent.ipynb','03':'03_Evaluation.ipynb'}
    transfer=load(P/'provenance/group_rag_kg_source/transfer_manifest.json')
    copied={r['original_path']:r for r in transfer['files'] if r['disposition']=='copied'}
    mapped=[]
    for file,symbols,change,n,mod in mapping:
        original='RAG_KG_Tham_khao/PTHTTM-RAG/chatbot/app/'+file
        row=copied[original]
        mapped.append({'original_path':original,'original_sha256':row['original_sha256'],
          'copied_path':row['copied_path'],'copied_sha256':row['copied_sha256'],'symbols':symbols,
          'keep_and_adapt':change,'target_notebook':'project01/notebooks/'+nb[n],
          'target_cell_tag':'llm-v2-'+mod,'target_export':'project01/web/backend/project01_llm_v2/'+mod+'.py',
          'status':'COPIED_PORT_PENDING_PHASE2'})
    kg=copied['RAG_KG_Tham_khao/PTHTTM-RAG/chatbot/Extract_Graph.ipynb']
    mapped.append({'original_path':kg['original_path'],'original_sha256':kg['original_sha256'],
      'copied_path':kg['copied_path'],'copied_sha256':kg['copied_sha256'],
      'symbols':'extract_entities_and_relationships,load_extraction_cache,save_extraction_cache,normalize_key,normalize_extraction,build_graph_payload,visualize_graph',
      'keep_and_adapt':'Port cache/normalizer/aggregation/JSON/PyVis; replace OpenAI/Groq with Gemini; chunk+model+prompt+schema cache; evidence spans; no Cypher/Neo4j I/O',
      'target_notebook':'project01/notebooks/'+nb['01'],'target_cell_tag':'llm-v2-kg',
      'target_export':'project01/web/backend/project01_llm_v2/kg.py','status':'COPIED_PORT_PENDING_PHASE2'})
    dump(DOC/'reuse_map.json',{'version':'reuse-v1','runtime_imports_from_provenance':False,'source_of_truth':'3 inline notebooks, one-way export',
                              'components':mapped,'supporting_files':'remaining copied __init__, tests, frontend, README/compose retained as source reference only; tests port to medical fixtures',
                              'not_used':'FastAPI/auth/full group frontend, legal data/index/graph, alternate providers, Qdrant/Neo4j I/O; see transfer manifest omitted list'})
    documents=rows(D/'corpus_documents.jsonl');chunks=rows(D/'chunks.jsonl')
    dump(D/'source_catalog.json',{'source_repository':'https://github.com/abachaa/MedQuAD',
          'commit':'577bd37b96c02d1833b2c9eed2de9f96964e96cb','acquisition_receipt':'project01/artifacts/llm_v2/phase1/acquisition.json',
          'license':'CC BY 4.0 dataset; individual website terms retained',
          'documents':[{k:r[k] for k in ['document_id','title','source_url','snapshot_url','source_xml_path']} for r in documents],
          'source_age':'historical snapshot; not verified against live clinical pages',
          'original_url_status':'recovered from XML, not guessed; live availability not checked'})
    char_total=sum(len(c['content']) for c in chunks)
    dump(D/'examples.json',{'synthetic':False,'examples':[{k:c[k] for k in ['chunk_id','title','section','content','source_refs']} for c in chunks[:3]],
                          'selection':'first3 sorted content-hash IDs, not cherry-picked model success','total_chunk_characters':char_total})
    lock=tomllib.loads((P/'environment/llm_v2/uv.lock').read_text())
    dump(A/'serving_dependency_resolution.json',{'python':'WSL3.11.17','lock':'project01/environment/llm_v2/uv.lock',
          'lock_sha256':sha(P/'environment/llm_v2/uv.lock'),'resolved_packages':len(lock['package']),
          'package_versions':{r['name']:r['version'] for r in lock['package']},
          'installed':False,'gpu_environments_modified':False,'runtime_smoke':'PENDING_PHASE2'})
    dump(A/'quota_user_confirmation.json',{'date':'2026-11-02','source':'user supplied AI Studio readings in task conversation',
          'generation_model':'gemini-3.8-flash','generation':config['quota']['generation'],
          'embedding_model':'gemini-embedding-001','embedding':config['quota']['embedding'],
          'initial_usage_snapshot':config['quota']['observed_usage_user_snapshot'],
          'decision':'Keep Gemini 3.8 Flash; run multiple days; do not reduce 40x2 evaluation',
          'paid_budget_usd':0,'billing_invoice_independently_verified':False,'refresh_required_before_phase2':True})
    print(json.dumps({'port_components':len(mapped),'source_documents':len(documents),'total_chunk_characters':char_total,
                      'dependency_packages':len(lock['package']),'model_probed':'gemini-3.8-flash'}))


if __name__=='__main__':main()
