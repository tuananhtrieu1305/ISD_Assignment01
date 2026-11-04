"""Operational runner; implementation is exported from notebook cells."""
from pathlib import Path
import argparse,asyncio,hashlib,json,sys,time
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'web/backend'))
from project01_llm_v2.agents import AgenticRuntime
from project01_llm_v2.indexing import DocumentIndexer,DocumentChunker
from project01_llm_v2.embedding import Embedder,VectorDBClient
from project01_llm_v2.bm25 import BM25Store
from project01_llm_v2.provider import ProviderUnavailable,atomic_json,read_json
from project01_llm_v2.evaluation import resume_branch,evaluate


async def index():
    runtime=AgenticRuntime(P,True);folder=runtime.folder;folder.mkdir(parents=True,exist_ok=True)
    store=VectorDBClient(folder/'vectors.json');sparse=BM25Store(folder/'bm25')
    indexer=DocumentIndexer(DocumentChunker(),Embedder(runtime.gateway),store,sparse)
    if (folder/'complete.json').exists():
        print(json.dumps({'index':'ALREADY_COMPLETE','count':len(store.points)}));return
    import fcntl
    with (folder/'builder.lock').open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        existing={p['id'] for p in store.points};remaining=[c for c in runtime.chunks if c.chunk_id not in existing]
        while remaining:
            batch=remaining[:8]
            try:
                await indexer._index_dense_chunks(batch);remaining=remaining[len(batch):]
                atomic_json(folder/'progress.json',{'status':'BUILDING','count':len(store.points),'target':316,'updated':time.time()})
                print(json.dumps({'index_count':len(store.points),'target':316}),flush=True)
            except ProviderUnavailable as exc:
                atomic_json(folder/'progress.json',{'status':exc.code,'count':len(store.points),'target':316,'updated':time.time()})
                if exc.code=='waiting_minute':await asyncio.sleep(60);continue
                print(json.dumps({'status':exc.code,'count':len(store.points)}));return
        assert {p['id'] for p in store.points}=={c.chunk_id for c in runtime.chunks}
        await sparse.build(runtime.chunks);await sparse.save()
        runtime.graph.export(P/'artifacts/llm_v2/kg/runtime_graph_v1.json')
        from project01_llm_v2.kg import visualize_graph
        visualize_graph(runtime.graph.neighborhood('Bệnh thận và tiểu đường'),P/'artifacts/llm_v2/kg/neighborhood_development.html')
        atomic_json(folder/'complete.json',{'status':'PASS','fingerprint':runtime.fingerprint,'count':len(store.points),
            'vector_sha256':hashlib.sha256((folder/'vectors.json').read_bytes()).hexdigest(),'model':'gemini-embedding-001','dimensions':768,'normalization':'L2','training_steps':0})
        print(json.dumps({'index':'PASS','count':len(store.points)}))


async def development(only_case=None,claim_revision='development-v1'):
    # Predeclared subset before model outputs: known direction regression + activity.
    source=P/'datasets/llm_v2/evaluation_v1/development_questions.jsonl'
    cases={r['id']:r for r in map(json.loads,source.read_text(encoding='utf-8').splitlines())}
    folder=P/'artifacts/llm_v2/phase2/development';folder.mkdir(parents=True,exist_ok=True)
    protocol=folder/'selection.json'
    if not protocol.exists():atomic_json(protocol,{'selected_ids':['v2-dev-11','v2-dev-05'],'reason':'known direction failure and common lifestyle question; selected before any Phase2 generation','held_out_used':False})
    runtime=AgenticRuntime(P,True)
    for case_id in read_json(protocol)['selected_ids']:
        if only_case and case_id!=only_case:continue
        path=folder/(case_id+'.json');case=cases[case_id]
        state=read_json(path) if path.exists() else {'question_id':case_id,'question':case['question_vi'],'results':{},'status':'running'}
        for variant in ['llm_direct','agentic_rag']:
            if variant in state['results']:continue
            try:
                row=await resume_branch(runtime,variant,case['question_vi'],claim_revision+':'+case_id,progress=lambda s:print(s,flush=True))
                state['results'][variant]=row;state['status']='complete' if len(state['results'])==2 else 'partial';atomic_json(path,state)
            except ProviderUnavailable as exc:
                state['status']=exc.code;state['error_type']=type(exc).__name__;atomic_json(path,state)
                print(json.dumps({'development':case_id,'status':exc.code}));return
        print(json.dumps({'development':case_id,'status':state['status'],'results':{k:v['status'] for k,v in state['results'].items()}}),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['inspect','index','development','evaluate']);parser.add_argument('--max-new-outputs',type=int);parser.add_argument('--case-id',choices=['v2-dev-11','v2-dev-05']);parser.add_argument('--claim-revision',default='development-v1')
    args=parser.parse_args()
    if args.stage=='inspect':print(json.dumps(AgenticRuntime(P).readiness()))
    elif args.stage=='index':asyncio.run(index())
    elif args.stage=='development':asyncio.run(development(args.case_id,args.claim_revision))
    else:print(json.dumps(asyncio.run(evaluate(P,args.max_new_outputs))))


if __name__=='__main__':main()
