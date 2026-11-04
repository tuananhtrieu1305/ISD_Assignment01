"""Replace the duplicate role/step maps by one four-role execution view."""
from pathlib import Path
P=Path(__file__).resolve().parents[2]
path=P/'web/frontend/src/PipelineFlow.jsx';source=path.read_text(encoding='utf-8')
start=source.index('function legacyTrace(');end=source.index('function statusClass(')
source=source[:start]+"""function getStages(job,result){
 const rows=result?.pipeline_trace?.length?result.pipeline_trace:job?.pipeline_traces?.agentic_rag;
 return Array.isArray(rows)?rows:[];
}

"""+source[end:]
source=source.replace("const STAGE_ORDER=['pre_retrieval','risk','retrieval','rerank','reporter','verifier','repair','verify_repair','release'];\n",'')
source=source.replace("pre_retrieval:'Pre-retrieval',risk:'Risk Agent',retrieval:'Retrieval'","pre_retrieval:'Pre-retrieval',retrieval:'Retrieval'")
start=source.index("  if(row.id==='risk'&&row.status==='skipped')")
end=source.index('  return <pre',start)
source=source[:start]+source[end:]
source=source.replace("output.citation_ids?.length>0","(output.citation_chunk_ids||output.citation_ids)?.length>0").replace("output.citation_ids.join(', ')","(output.citation_chunk_ids||output.citation_ids).join(', ')")
start=source.index('function AgentRoles(')
source=source[:start]+"""const AGENTS=[
 {id:'coordinator',label:'Coordinator',tool:'Gemini · pre-retrieval',steps:['pre_retrieval']},
 {id:'knowledge',label:'Knowledge Agent',tool:'BM25 · embedding · KG · rerank local',steps:['retrieval','rerank']},
 {id:'reporter',label:'Reporter',tool:'Gemini · tổng hợp câu trả lời',steps:['reporter']},
 {id:'verifier',label:'Verifier',tool:'Gemini + integrity · duyệt và phát hành',steps:['verifier','release']}
];
function roleStatus(agent,byId){
 const rows=agent.steps.map(id=>byId.get(id)).filter(Boolean);
 if(rows.some(row=>row.status==='failed'))return 'failed';
 if(rows.some(row=>row.status==='running'))return 'running';
 if(rows.length===agent.steps.length&&rows.every(row=>row.status==='complete'))return 'complete';
 if(rows.length)return 'running';
 return 'pending';
}
export default function PipelineFlow({job,onResult}){
 const result=job?.results?.agentic_rag,rows=getStages(job,result);
 if(!job)return <section className="panel pipeline-empty"><h2>Chưa có lượt xử lý.</h2><p>Gửi câu hỏi để xem input/output của từng agent.</p></section>;
 if(rows.some(row=>row.id==='risk'))return <section className="panel pipeline-empty"><h2>Đây là lượt cũ có hồ sơ CDC.</h2><p>Hãy gửi câu hỏi mới để xem luồng 4 agent hiện hành. Kết quả cũ được giữ nguyên.</p></section>;
 const byId=new Map(rows.map(row=>[row.id,row]));
 return <section className="pipeline-flow" aria-label="Luồng bốn agent">
  <nav className="pipeline-map four-agent-map" aria-label="Pipeline duy nhất">{AGENTS.map((agent,index)=><React.Fragment key={agent.id}><a href={'#agent-'+agent.id} className={statusClass(roleStatus(agent,byId))}><small>{String(index+1).padStart(2,'0')}</small><span>{agent.label}</span><em>{agent.tool}</em><b>{STATUS[roleStatus(agent,byId)]||'Chưa đến lượt'}</b></a>{index<AGENTS.length-1&&<i>→</i>}</React.Fragment>)}</nav>
  <p className="pipeline-footnote">4 agent · 1 generation cho nhánh trực tiếp + 3 cho pipeline. Truy hồi/rerank thuộc Knowledge Agent; embedding dùng hạn mức riêng.</p>
  <div className="pipeline-stages">{AGENTS.map((agent,index)=><article id={'agent-'+agent.id} key={agent.id} className={'pipeline-stage '+statusClass(roleStatus(agent,byId))}><header><span className="pipeline-index">{index+1}</span><div><small>{agent.tool}</small><h2>{agent.label}</h2></div><StageBadge value={roleStatus(agent,byId)}/></header>{agent.steps.map(id=>{const row=byId.get(id);return <section className="agent-substep" id={'pipeline-'+id} key={id}>{agent.steps.length>1&&<h3 className="substep-name">{row?.label||LABELS[id]}</h3>}{row?<><div className="pipeline-io"><div><h3>Input</h3><pre className="pipeline-json compact">{JSON.stringify(row.input??{},null,2)}</pre></div><div><h3>Output</h3><StageOutput row={row}/></div></div><div className="substep-meta">{row.duration_ms!=null&&<span>{fmt(row.duration_ms,0)} ms</span>}{row.calls&&<span>{row.calls.live||0} call live · {row.calls.cache||0} cache</span>}<span>{row.recording==='captured_during_execution'?'Ghi trong lúc thực thi':'Đọc kết quả đã lưu'}</span></div></>:<p className="pipeline-muted substep-wait">Chưa đến bước này.</p>}</section>;})}</article>)}</div>
  <div className="pipeline-actions"><button type="button" onClick={onResult}>Về câu trả lời →</button></div>
 </section>;
}
"""
path.write_text(source,encoding='utf-8')
