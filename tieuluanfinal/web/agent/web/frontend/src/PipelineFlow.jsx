import React from 'react';
import AnswerText from './AnswerText.jsx';
import './pipeline-flow.css';

const LABELS={
  pre_retrieval:'Pre-retrieval',retrieval:'Retrieval',rerank:'Reranking',
  reporter:'Reporter Agent',verifier:'Verifier Agent',repair:'Sửa bản nháp',
  verify_repair:'Kiểm chứng lại',release:'Kết quả cuối'
};
const STATUS={complete:'Hoàn tất',running:'Đang chạy',failed:'Lỗi',skipped:'Bỏ qua',not_recorded:'Không được ghi lại'};
const fmt=(value,digits=3)=>value==null||value===''||!Number.isFinite(Number(value))?'—':Number(value).toLocaleString('vi-VN',{maximumFractionDigits:digits});
function getStages(job,result){
 const rows=result?.pipeline_trace?.length?result.pipeline_trace:job?.pipeline_traces?.agentic_rag;
 return Array.isArray(rows)?rows:[];
}

function statusClass(value){return ['complete','running','failed','skipped','not_recorded'].includes(value)?value:'pending';}
function StageBadge({value}){return <span className={'pipeline-badge '+statusClass(value)}>{STATUS[value]||'Chưa chạy'}</span>;}
function ChipList({items,empty='—'}){return items?.length?<div className="pipeline-chips">{items.map((item,index)=><span key={`${String(item)}-${index}`}>{String(item)}</span>)}</div>:<span className="pipeline-muted">{empty}</span>;}

function PreRetrieval({data}){
  const output=data.output||{};const plan=output.plan||{};
  return <div className="pipeline-output-grid"><div><b>Truy vấn sau viết lại</b><ol>{(output.queries||plan.queries||[]).map((q,i)=><li key={i}>{q}</li>)}</ol></div><div><b>Thực thể KG được phép dùng</b><ChipList items={output.entity_ids_used||plan.entity_ids}/><b className="pipeline-subhead">Hướng quan hệ cần kiểm tra</b>{plan.relation_direction?.length?<ul>{plan.relation_direction.map((edge,i)=><li key={i}>{edge.subject} → {edge.relation} → {edge.object}</li>)}</ul>:<p className="pipeline-muted">Không có hướng quan hệ được ghi lại.</p>}</div></div>;
}

function Retrieval({data}){
  const output=data.output||{};const candidates=output.candidates||[];const graph=output.graph||{};
  return <><div className="pipeline-metrics"><span><b>{fmt(output.candidate_count,0)}</b> ứng viên</span><span><b>{fmt(output.kg_candidate_count,0)}</b> có đóng góp KG</span><span><b>{fmt(graph.relationships?.length,0)}</b> cạnh KG liên quan</span></div>{output.per_query_counts&&<div><b>Số ứng viên theo truy vấn</b><ChipList items={Object.entries(output.per_query_counts).map(([q,n])=>`${q}: ${n}`)}/></div>}<div className="pipeline-table-wrap"><table><thead><tr><th>Rank đầu</th><th>Đoạn / tiêu đề</th><th>RRF</th><th>Dense</th><th>BM25</th><th>KG</th></tr></thead><tbody>{candidates.map((row,index)=><tr key={row.chunk_id||index}><td>{row.original_rank??index+1}</td><td><b>{row.metadata?.title||'Không có tiêu đề'}</b><small>{row.chunk_id}</small></td><td>{fmt(row.rrf_score??row.score)}</td><td>{fmt(row.dense_rank,0)}</td><td>{fmt(row.sparse_rank,0)}</td><td>{row.kg_rank==null?'—':fmt(row.kg_rank,0)}</td></tr>)}</tbody></table></div>{graph.relationships?.length>0&&<details><summary>Các cạnh KG được nối vào truy hồi</summary>{graph.relationships.map((edge,i)=><div className="pipeline-kg" key={edge.id||i}><b>{edge.subject} → {edge.relation} → {edge.object}</b>{edge.conditions&&<p>{edge.conditions}</p>}{edge.quote&&<blockquote>{edge.quote}</blockquote>}<small>{edge.source_chunk_ids?.join(', ')}</small></div>)}</details>}</>;
}

function Rerank({data}){
  const output=data.output||{};const ranking=output.ranking||[];const local=String(output.provider||'').startsWith('local_');
  const ordered=[...ranking].sort((a,b)=>(a.model_rank??9999)-(b.model_rank??9999)||(a.input_rank??9999)-(b.input_rank??9999));
  return <><div className="pipeline-metrics"><span><b>{fmt(output.candidate_count,0)}</b> đầu vào</span><span><b>{fmt(output.scored_count,0)}</b> {local?'đã chấm local':'model đề xuất'}</span><span><b>{fmt(output.evidence_count,0)}</b> evidence giữ lại</span><span><b>{fmt(output.api_calls,0)}</b> API rerank</span></div>{local&&<p className="pipeline-notice">Reranker chạy local bằng hybrid RRF + lexical coverage + KG source boost; không gọi Gemini.</p>}{output.note&&<p className="pipeline-notice">{output.note}</p>}<div className="pipeline-table-wrap"><table><thead><tr><th>Rank đầu</th><th>Rank sau</th><th>Đoạn</th><th>Điểm rerank</th><th>Quyết định</th></tr></thead><tbody>{ordered.map((row,index)=><tr key={row.chunk_id||index} className={row.selected?'selected':''}><td>{fmt(row.input_rank,0)}</td><td>{fmt(row.model_rank,0)}</td><td><b>{row.title||row.chunk_id}</b><small>{row.title?row.chunk_id:''}</small></td><td>{fmt(row.rerank_score)}</td><td>{row.selected?'Giữ lại':row.reason==='below_threshold'?'Dưới ngưỡng':row.reason==='over_top_n'?'Ngoài top N':row.reason==='not_proposed'?'Model không đề xuất':'Không được ghi lại'}</td></tr>)}</tbody></table></div><p className="pipeline-footnote">Dấu “—” nghĩa là không có điểm được lưu hoặc model không đề xuất, không phải điểm 0.</p></>;
}

function Draft({data}){const draft=data.output?.draft;return draft?<div><span className="pipeline-draft-label">BẢN NHÁP · CHƯA KIỂM CHỨNG</span><AnswerText text={draft.answer_vi||draft.answer||''}/>{draft.claims?.length>0&&<details><summary>Các claim Reporter tạo</summary><ul>{draft.claims.map((claim,i)=><li key={claim.id||claim.claim_id||i}><b>{claim.id||claim.claim_id||`C${i+1}`}</b>: {claim.text_vi||claim.text||claim.claim}<small>{claim.citation_chunk_ids?.join(', ')}</small></li>)}</ul></details>}</div>:<p className="pipeline-notice">{data.output?.reason||'Không có bản nháp được ghi lại.'}</p>;}
function Verify({data}){const review=data.output?.review||data.output||{};return <div><p><b>Kết luận:</b> {review.approved===true?'Đạt kiểm chứng':review.approved===false?'Chưa đạt':'Chưa có kết luận'}</p>{review.feedback&&<p>{review.feedback}</p>}{review.draft_revised&&<details><summary>Bản đã được Verifier sửa và kiểm</summary><AnswerText text={review.revised_draft?.answer_vi||''}/></details>}{review.code_errors?.length>0&&<div><b>Lỗi kiểm tra bằng code</b><ChipList items={review.code_errors}/></div>}{review.claim_reviews?.length>0&&<ul>{review.claim_reviews.map((item,i)=><li key={item.claim_id||i}><b>{item.claim_id}</b>: {item.status} {item.evidence_ids?.length?`(${item.evidence_ids.join(', ')})`:''}</li>)}</ul>}{data.output?.note&&<p className="pipeline-footnote">{data.output.note}</p>}</div>;}
function Release({data}){const output=data.output||{};return <div><span className="pipeline-draft-label final">CÂU TRẢ LỜI ĐƯỢC PHÁT HÀNH</span><AnswerText text={output.answer_vi||''}/>{(output.citation_chunk_ids||output.citation_ids)?.length>0&&<p><b>Nguồn được trích:</b> {(output.citation_chunk_ids||output.citation_ids).join(', ')}</p>}</div>;}

function StageOutput({row}){
  if(row.status==='failed')return <p className="pipeline-notice">Bước này dừng với mã lỗi: <b>{row.error?.code||'unknown'}</b>. Thông báo nội bộ và dữ liệu nhạy cảm không được đưa lên giao diện.</p>;
  if(row.status==='not_recorded')return <p className="pipeline-notice">{row.output?.reason||'Output này không được lưu.'}</p>;
  if(row.id==='pre_retrieval')return <PreRetrieval data={row}/>;
  if(row.id==='retrieval')return <Retrieval data={row}/>;
  if(row.id==='rerank')return <Rerank data={row}/>;
  if(row.id==='reporter'||row.id==='repair')return <Draft data={row}/>;
  if(row.id==='verifier'||row.id==='verify_repair')return <Verify data={row}/>;
  if(row.id==='release')return <Release data={row}/>;
  return <pre className="pipeline-json">{JSON.stringify(row.output??{},null,2)}</pre>;
}

const AGENTS=[
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
