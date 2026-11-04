import React from 'react';
import AnswerText from './AnswerText.jsx';
import './pipeline-flow.css';

const STAGE_ORDER=['pre_retrieval','risk','retrieval','rerank','reporter','verifier','repair','verify_repair','release'];
const LABELS={
  pre_retrieval:'Pre-retrieval',risk:'Risk Agent',retrieval:'Retrieval',rerank:'Reranking',
  reporter:'Reporter Agent',verifier:'Verifier Agent',repair:'Sửa bản nháp',
  verify_repair:'Kiểm chứng lại',release:'Kết quả cuối'
};
const STATUS={complete:'Hoàn tất',running:'Đang chạy',failed:'Lỗi',skipped:'Bỏ qua',not_recorded:'Không được ghi lại'};
const fmt=(value,digits=3)=>value==null||value===''||!Number.isFinite(Number(value))?'—':Number(value).toLocaleString('vi-VN',{maximumFractionDigits:digits});
const safeUrl=value=>{try{const url=new URL(value);return ['http:','https:'].includes(url.protocol)?url.href:null;}catch{return null;}};

function stage(id,status,input,output,extra={}){
  return {id,label:LABELS[id]||id,owner:'—',status,input,output,duration_ms:null,call_counts:null,...extra};
}

function legacyTrace(result){
  if(!result)return [];
  const plan=result.plan||{};
  const retrieved=result.retrieved||[];
  const evidence=result.evidence||[];
  const reranking=result.reranking;
  const graph=result.graph||{};
  return [
    stage('pre_retrieval','complete',{question:plan.original_question||result.question||'—'},
      {plan,queries:plan.queries||[],entity_ids_used:plan.entity_ids||[],next:'retrieval'},
      {owner:'Coordinator',recording:'reconstructed_from_saved_fields'}),
    result.risk
      ?stage('risk','complete',{profile_present:true,profile_values_exposed:false},result.risk,{owner:'Risk Agent',recording:'reconstructed_from_saved_fields'})
      :stage('risk','skipped',{profile_present:false},{reason:'Lượt này không kèm hồ sơ CDC.'},{owner:'Risk Agent',recording:'reconstructed_from_saved_fields'}),
    stage('retrieval','complete',{queries:plan.queries||[],top_k_per_query:20,entity_ids:plan.entity_ids||[]},
      {candidate_count:retrieved.length,per_query_counts:null,candidates:retrieved,kg_candidate_count:retrieved.filter(row=>row.kg_rank!=null).length,graph,next:'rerank'},
      {owner:'Retriever Agent',recording:'reconstructed_from_saved_fields'}),
    stage('rerank','complete',{question:plan.original_question||result.question||'—',candidate_count:retrieved.length},
      reranking||{candidate_count:retrieved.length,scored_count:null,evidence_count:evidence.length,threshold:null,top_n:6,
        ranking:retrieved.map((row,index)=>({chunk_id:row.chunk_id,title:row.metadata?.title,input_rank:row.original_rank??index+1,
          model_rank:evidence.findIndex(item=>item.chunk_id===row.chunk_id)>=0?evidence.findIndex(item=>item.chunk_id===row.chunk_id)+1:null,
          rerank_score:evidence.find(item=>item.chunk_id===row.chunk_id)?.rerank_score??null,
          selected:evidence.some(item=>item.chunk_id===row.chunk_id),reason:evidence.some(item=>item.chunk_id===row.chunk_id)?'selected':'not_recorded'})),
        note:'Bản lịch sử không lưu toàn bộ điểm và lý do loại của reranker.'},
      {owner:'Reranker Agent',recording:'reconstructed_from_saved_fields'}),
    stage('reporter','not_recorded',{evidence_chunk_ids:evidence.map(row=>row.chunk_id),evidence_count:evidence.length},
      {reason:'Bản nháp Reporter ban đầu không được lưu trong kết quả lịch sử; không dùng câu trả lời cuối để giả làm bản nháp.'},
      {owner:'Reporter Agent',recording:'missing_in_legacy_result'}),
    stage('verifier','complete',{evidence_chunk_ids:evidence.map(row=>row.chunk_id)},
      {review:result.verification||null,note:'Đây là kết quả kiểm chứng cuối được lưu; lịch sử không tách lần kiểm chứng trước và sau sửa.'},
      {owner:'Verifier Agent',recording:'reconstructed_from_saved_fields'}),
    stage('release',result.status==='complete'?'complete':'failed',{approved:result.verification?.approved===true},
      {answer_vi:result.answer_vi,citation_ids:(result.citations||[]).map(row=>row.chunk_id),status:result.status},
      {owner:'Coordinator',recording:'reconstructed_from_saved_fields'})
  ];
}

function getStages(job,result){
  const live=job?.pipeline_traces?.agentic_rag;
  if(Array.isArray(result?.pipeline_trace)&&result.pipeline_trace.length)return {rows:result.pipeline_trace,legacy:false};
  if(Array.isArray(live)&&live.length)return {rows:live,legacy:false};
  if(result)return {rows:legacyTrace(result),legacy:true};
  return {rows:[],legacy:false};
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
  const output=data.output||{};const ranking=output.ranking||[];
  const ordered=[...ranking].sort((a,b)=>(a.model_rank??9999)-(b.model_rank??9999)||(a.input_rank??9999)-(b.input_rank??9999));
  return <><div className="pipeline-metrics"><span><b>{fmt(output.candidate_count,0)}</b> đầu vào</span><span><b>{fmt(output.scored_count,0)}</b> model đề xuất</span><span><b>{fmt(output.evidence_count,0)}</b> evidence giữ lại</span><span><b>{fmt(output.threshold)}</b> ngưỡng</span></div>{output.note&&<p className="pipeline-notice">{output.note}</p>}<div className="pipeline-table-wrap"><table><thead><tr><th>Rank đầu</th><th>Rank sau</th><th>Đoạn</th><th>Điểm rerank</th><th>Quyết định</th></tr></thead><tbody>{ordered.map((row,index)=><tr key={row.chunk_id||index} className={row.selected?'selected':''}><td>{fmt(row.input_rank,0)}</td><td>{fmt(row.model_rank,0)}</td><td><b>{row.title||row.chunk_id}</b><small>{row.title?row.chunk_id:''}</small></td><td>{fmt(row.rerank_score)}</td><td>{row.selected?'Giữ lại':row.reason==='below_threshold'?'Dưới ngưỡng':row.reason==='over_top_n'?'Ngoài top N':row.reason==='not_proposed'?'Model không đề xuất':'Không được ghi lại'}</td></tr>)}</tbody></table></div><p className="pipeline-footnote">Dấu “—” nghĩa là không có điểm được lưu hoặc model không đề xuất, không phải điểm 0.</p></>;
}

function Draft({data}){const draft=data.output?.draft;return draft?<div><span className="pipeline-draft-label">BẢN NHÁP · CHƯA KIỂM CHỨNG</span><AnswerText text={draft.answer_vi||draft.answer||''}/>{draft.claims?.length>0&&<details><summary>Các claim Reporter tạo</summary><ul>{draft.claims.map((claim,i)=><li key={claim.claim_id||i}><b>{claim.claim_id||`C${i+1}`}</b>: {claim.text||claim.claim}</li>)}</ul></details>}</div>:<p className="pipeline-notice">{data.output?.reason||'Không có bản nháp được ghi lại.'}</p>;}
function Verify({data}){const review=data.output?.review||data.output||{};return <div><p><b>Kết luận:</b> {review.approved===true?'Đạt kiểm chứng':review.approved===false?'Chưa đạt':'Chưa có kết luận'}</p>{review.feedback&&<p>{review.feedback}</p>}{review.code_errors?.length>0&&<div><b>Lỗi kiểm tra bằng code</b><ChipList items={review.code_errors}/></div>}{review.claim_reviews?.length>0&&<ul>{review.claim_reviews.map((item,i)=><li key={item.claim_id||i}><b>{item.claim_id}</b>: {item.status} {item.evidence_ids?.length?`(${item.evidence_ids.join(', ')})`:''}</li>)}</ul>}{data.output?.note&&<p className="pipeline-footnote">{data.output.note}</p>}</div>;}
function Release({data}){const output=data.output||{};return <div><span className="pipeline-draft-label final">CÂU TRẢ LỜI ĐƯỢC PHÁT HÀNH</span><AnswerText text={output.answer_vi||''}/>{output.citation_ids?.length>0&&<p><b>Nguồn được trích:</b> {output.citation_ids.join(', ')}</p>}</div>;}

function StageOutput({row}){
  if(row.status==='failed')return <p className="pipeline-notice">Bước này dừng với mã lỗi: <b>{row.error?.code||'unknown'}</b>. Thông báo nội bộ và dữ liệu nhạy cảm không được đưa lên giao diện.</p>;
  if(row.status==='not_recorded')return <p className="pipeline-notice">{row.output?.reason||'Output này không được lưu.'}</p>;
  if(row.id==='pre_retrieval')return <PreRetrieval data={row}/>;
  if(row.id==='retrieval')return <Retrieval data={row}/>;
  if(row.id==='rerank')return <Rerank data={row}/>;
  if(row.id==='reporter'||row.id==='repair')return <Draft data={row}/>;
  if(row.id==='verifier'||row.id==='verify_repair')return <Verify data={row}/>;
  if(row.id==='release')return <Release data={row}/>;
  if(row.id==='risk'&&row.status==='skipped')return <p className="pipeline-muted">{row.output?.reason}</p>;
  return <pre className="pipeline-json">{JSON.stringify(row.output??{},null,2)}</pre>;
}

export default function PipelineFlow({job,onResult}){
  const result=job?.results?.agentic_rag;
  const {rows,legacy}=getStages(job,result);
  const byId=new Map(rows.map(row=>[row.id,row]));
  const visible=STAGE_ORDER.map(id=>byId.get(id)).filter(Boolean);
  if(!job)return <section className="panel pipeline-empty"><h2>Chưa có lượt xử lý để xem.</h2><p>Gửi một câu hỏi hoặc mở kết quả development đã lưu. Chỉ chuyển sang tab này không gọi thêm API.</p></section>;
  if(!visible.length)return <section className="panel pipeline-empty"><h2>Pipeline RAG chưa bắt đầu.</h2><p>Nhánh trực tiếp có thể đang chạy trước. Các bước dưới đây chỉ xuất hiện khi chúng thực sự được thực thi.</p></section>;
  return <section className="pipeline-flow" aria-label="Luồng input và output của pipeline đa agent">
    {legacy&&<div className="pipeline-legacy"><b>Kết quả lịch sử</b><span>Tab này tái dựng từ các trường đã lưu. Output trung gian không tồn tại sẽ được ghi rõ, không tự tạo lại.</span></div>}
    <div className="pipeline-map" aria-label="Các bước pipeline">{visible.map((row,index)=><React.Fragment key={row.id}><a href={`#pipeline-${row.id}`} className={statusClass(row.status)}><small>{index+1}</small><span>{row.label||LABELS[row.id]}</span><b>{STATUS[row.status]||'Chưa chạy'}</b></a>{index<visible.length-1&&<i>→</i>}</React.Fragment>)}</div>
    <div className="pipeline-summary"><span><b>{fmt(byId.get('pre_retrieval')?.output?.queries?.length,0)}</b> truy vấn</span><span><b>{fmt(byId.get('retrieval')?.output?.candidate_count,0)}</b> ứng viên</span><span><b>{fmt(byId.get('rerank')?.output?.evidence_count,0)}</b> evidence sau rerank</span><span><b>{byId.get('verifier')?.output?.review?.approved===true?'Đạt':byId.get('verify_repair')?.output?.review?.approved===true?'Đạt':'—'}</b> Verifier</span></div>
    <div className="pipeline-stages">{visible.map((row,index)=><article id={`pipeline-${row.id}`} className={'pipeline-stage '+statusClass(row.status)} key={row.id}><header><span className="pipeline-index">{String(index+1).padStart(2,'0')}</span><div><small>{row.owner||'—'}</small><h2>{row.label||LABELS[row.id]}</h2></div><StageBadge value={row.status}/></header><div className="pipeline-io"><div><h3>Input</h3><pre className="pipeline-json compact">{JSON.stringify(row.input??{},null,2)}</pre></div><div><h3>Output</h3><StageOutput row={row}/></div></div><footer>{row.duration_ms!=null&&<span>{fmt(row.duration_ms,0)} ms</span>}{(row.call_counts||row.calls)&&<span>{fmt((row.call_counts||row.calls).live,0)} call live · {fmt((row.call_counts||row.calls).cache,0)} cache</span>}<span>{row.recording==='captured_during_execution'?'Ghi trong lúc thực thi':row.recording==='missing_in_legacy_result'?'Không có trong bản lịch sử':'Đọc từ kết quả đã lưu'}</span></footer></article>)}</div>
    <div className="pipeline-actions"><button type="button" onClick={onResult}>Xem câu trả lời cuối →</button><p>Đọc tab này không gửi thêm request Gemini. Đây là log giải thích pipeline, không phải chẩn đoán y khoa.</p></div>
  </section>;
}
