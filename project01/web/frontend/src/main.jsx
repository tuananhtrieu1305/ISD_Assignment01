import React,{useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';
import './comparison.css';
import './question-demo.css';
import AnswerText from './AnswerText.jsx';
import PipelineFlow from './PipelineFlow.jsx';
import KnowledgeGraph from './KnowledgeGraph.jsx';

const API=(import.meta.env.VITE_API_BASE_URL||'').replace(/\/$/,'');
const BRANCHES=[['llm_direct','LLM trực tiếp','Kiến thức sẵn có của Gemini'],['agentic_rag','Đa agent + RAG','Truy hồi · KG · kiểm chứng']];
const NAV=[['input','01','Câu hỏi'],['result','02','Câu trả lời'],['pipeline','03','Luồng xử lý'],['graph','04','Đồ thị tri thức']];
const fmt=(v,d=1)=>v==null||!Number.isFinite(Number(v))?'—':Number(v).toLocaleString('vi-VN',{maximumFractionDigits:d});
const modelName=id=>({'gemini-3-flash-preview':'Gemini 3 Flash (preview)','gemini-3.8-flash':'Gemini 3.8 Flash'}[id]||id||'Gemini');
const stateName={complete:'Hoàn tất',verification_failed:'Chưa kiểm chứng đạt',waiting_quota:'Chờ quota',running:'Đang xử lý',queued:'Đang chờ',failed:'Đã dừng do lỗi',interrupted:'Bị gián đoạn',skipped:'Chưa chạy',pending:'Chưa đến lượt'};
async function api(path,body){
 let response;
 try{response=await fetch(API+path,{...(body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{}),signal:AbortSignal.timeout(10000)});}
 catch(e){if(e.name==='TimeoutError'||e.name==='AbortError')throw new Error('Backend chưa phản hồi trong 10 giây. Request đã gửi không được tự gửi lại.');throw e;}
 const data=await response.json();if(!response.ok)throw new Error(data.error?.message||`HTTP ${response.status}`);return data;
}
function safeUrl(value){try{const u=new URL(value);return ['http:','https:'].includes(u.protocol)?u.href:null;}catch{return null;}}

function App(){
 const [tab,setTab]=useState('input'),[ready,setReady]=useState(null),[question,setQuestion]=useState('');
 const [job,setJob]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[now,setNow]=useState(Date.now());
 const timer=useRef(null),activeJob=useRef(null),lastRefresh=useRef(0);
 const refresh=()=>{lastRefresh.current=Date.now();return api('/ready').then(setReady).catch(()=>setReady({status:'unavailable'}));};
 useEffect(()=>{refresh();return()=>{clearTimeout(timer.current);activeJob.current=null;};},[]);
 useEffect(()=>{if(!busy)return;const tick=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(tick);},[busy]);
 async function poll(id){
  try{const next=await api('/api/v2/jobs/'+id);if(activeJob.current!==id)return;setJob(next);setNow(Date.now());
   if(Date.now()-lastRefresh.current>10000)refresh();
   if(['queued','running'].includes(next.status)){const elapsed=next.elapsed_seconds??0;timer.current=setTimeout(()=>poll(id),elapsed<30?2000:elapsed<120?5000:10000);}
   else{setBusy(false);refresh();}
  }catch(e){if(activeJob.current!==id)return;setError(e.message);setBusy(false);}
 }
 async function run(event){
  event.preventDefault();if(busy||!question.trim())return;
  clearTimeout(timer.current);activeJob.current=null;setError('');setBusy(true);setJob(null);setTab('result');
  try{const data=await api('/api/v2/compare',{question:question.trim()});activeJob.current=data.id;poll(data.id);}
  catch(e){setError(e.message);setBusy(false);}
 }
 async function resume(){if(!job?.id||busy)return;setBusy(true);setError('');try{await api('/api/v2/jobs/'+job.id+'/resume',{});activeJob.current=job.id;poll(job.id);}catch(e){setError(e.message);setBusy(false);}}
 const results=job?.results||{};
 const mismatch=ready?.status==='ready'&&ready.runtime_revision!=='four-agent-r11';
 const remaining=Math.max(0,(ready?.usage?.generation_cap??18)-(ready?.usage?.generation_attempts??18));
 const heading={input:'Bạn muốn hỏi điều gì?',result:'Hai câu trả lời, cạnh nhau.',pipeline:'Một câu hỏi. Bốn agent.',graph:'Kho tri thức, nhìn thành đồ thị.'};
 const elapsed=Math.max(0,(job?.elapsed_seconds??0)+(busy?Math.max(0,now/1000-(job?.observed_at??now/1000)):0));
 return <div className="app"><header className="header"><a className="brand" href="#" onClick={e=>{e.preventDefault();setTab('input');}}><span className="brand-icon">D<span>↗</span></span><span><small>PROJECT 01 · TRÍ TUỆ NHÂN TẠO</small><strong>Diabetes <em>/</em> Agent Lab</strong></span></a><span className={`health ${ready?.status==='ready'?'ready':'unavailable'}`}><i/>{ready?.status==='ready'?'Sẵn sàng':'Đang kiểm tra kết nối'}</span></header>
  <div className="layout"><aside className="sidebar"><p className="eyebrow">KHÔNG GIAN THỰC NGHIỆM</p><nav aria-label="Khu vực demo">{NAV.map(([id,n,label])=><button key={id} className={'nav-item '+(tab===id?'active':'')} onClick={()=>setTab(id)}><span>{n}</span>{label}<b>↗</b></button>)}</nav><div className="sidebar-note"><span className="tiny-icon">KG</span><strong>Hỏi một câu.<br/>Đối chiếu hai cách trả lời.</strong><p>4 agent · RAG + KG<br/>{modelName(ready?.generation_model)}</p></div></aside>
   <main><div className="page-heading"><span className="eyebrow">DIABETES / KNOWLEDGE LAB</span><h1>{heading[tab]}</h1>{tab==='pipeline'&&<p>Theo dõi đúng luồng đã chạy: câu hỏi, truy hồi, câu trả lời và kiểm chứng.</p>}</div>
    {mismatch&&<div className="alert" role="alert">Backend còn bản cũ. Dừng và khởi động lại launcher, rồi Ctrl+F5 để nạp bản 4 agent.</div>}
    {error&&<div className="alert error" role="alert">{error}</div>}
    {tab==='input'&&<form className="panel prompt-panel question-only" onSubmit={run}><label className="field question"><span>Câu hỏi của bạn</span><textarea value={question} onChange={e=>setQuestion(e.target.value)} maxLength={4096} rows={4} placeholder="Nhập câu hỏi về tiểu đường…" required disabled={busy}/></label><button className="run-button" type="submit" disabled={busy||!question.trim()||mismatch||ready?.status!=='ready'||!ready?.live_enabled||remaining<4}>{busy?'Đang xử lý…':'Trả lời'}<span>→</span></button>{ready?.status==='ready'&&remaining<4&&<p className="input-warning" role="status">Cần 4 generation request; hiện còn {remaining}.</p>}</form>}
    {tab==='result'&&(job?<><section className="submitted"><span className="eyebrow">CÂU HỎI ĐÃ GỬI</span><h2>{job.question}</h2><div className="run-meta"><span className="tag">{stateName[job.status]||job.status}</span>{busy&&<span className="live-progress"><span className="spinner"/>{job.progress||'Đang khởi tạo…'}</span>}<span>{fmt(elapsed,0)} giây</span></div>{job.error&&<div className="alert" role="status">{job.error.message}{job.status==='waiting_quota'&&<button disabled={busy} onClick={resume}>Tiếp tục lượt này</button>}</div>}</section><div className="answer-comparison">{BRANCHES.map(([id,title,subtitle])=><Answer key={id} id={id} title={title} subtitle={subtitle} result={results[id]} busy={busy} generationModel={ready?.generation_model} branchState={job.branch_states?.[id]||'pending'}/>)}</div>{(results.agentic_rag||job.pipeline_traces?.agentic_rag)&&<div className="pipeline-jump"><button onClick={()=>setTab('pipeline')}>Xem luồng xử lý →</button></div>}{results.agentic_rag&&<Evidence result={results.agentic_rag}/>}</>:<section className="panel empty"><h2>Chưa có câu trả lời.</h2><button onClick={()=>setTab('input')}>Nhập câu hỏi →</button></section>)}
    {tab==='pipeline'&&<PipelineFlow job={job} onResult={()=>setTab('result')}/>}
    {tab==='graph'&&<KnowledgeGraph api={api}/>}
    <footer>PROJECT01 <span>·</span> Gemini + MedQuAD <span>·</span> Demo học thuật</footer>
   </main></div></div>;
}

function Answer({id,title,subtitle,result,busy,branchState,generationModel}){
 const usage=result?.usage||[],tokens=usage.reduce((sum,row)=>sum+(row.usage?.total_tokens||0),0);
 const incomplete=usage.some(row=>row.finish_reasons?.some(reason=>reason!=='STOP'));
 return <section className={'answer-column '+(id==='agentic_rag'?'grounded':'')} aria-label={title}><div className="answer-column-head"><span className="eyebrow">{subtitle}</span><h2>{title}</h2><small>{modelName(result?.model||generationModel)}</small></div>{result&&incomplete?<p className="answer-placeholder">Provider trả đầu ra chưa hoàn chỉnh; chưa coi là câu trả lời đã hoàn tất.</p>:result?<><span className="tag">{stateName[result.status]||result.status}</span><div className="primary-answer"><AnswerText text={result.answer_vi}/></div><div className="answer-stats"><span>{fmt(result.latency_ms/1000)} s</span><span>{tokens?fmt(tokens,0)+' tokens provider':'Chưa có usage token'}</span><span>{result.citations?.length||0} nguồn</span></div></>:<div className="answer-placeholder"><span>{busy&&branchState==='running'?'Đang thực hiện…':stateName[branchState]||'Chưa có kết quả'}</span><p>{branchState==='pending'?'Nhánh này đang chờ đến lượt.':'Kết quả thật sẽ xuất hiện sau khi bước xử lý hoàn tất.'}</p></div>}</section>;
}
function Evidence({result}){
 return <details className="panel supporting-evidence"><summary>Nguồn & kiểm chứng · {result.citations?.length||0} đoạn được dùng</summary><h2>Đối chiếu bằng chứng</h2>{result.citations?.map(row=><details key={row.chunk_id}><summary>[Nguồn {result.evidence.findIndex(e=>e.chunk_id===row.chunk_id)+1}] {row.metadata.title}</summary><p>{row.content}</p>{safeUrl(row.metadata.source)&&<a href={safeUrl(row.metadata.source)} target="_blank" rel="noreferrer">Mở nguồn gốc ↗</a>}<small>{row.chunk_id}</small></details>)}<details><summary>Nhận xét của Verifier</summary><p>{result.verification?.feedback}</p><ul>{result.verification?.claim_reviews?.map(row=><li key={row.claim_id}>{row.claim_id}: {row.status}</li>)}</ul><p>Gemini kiểm theo evidence và code kiểm integrity; đây không phải thẩm định độc lập của chuyên gia.</p></details><p className="footnote">MedQuAD là snapshot lịch sử; nguồn được giữ để đối chiếu, không tự coi là hướng dẫn hiện hành.</p></details>;
}
createRoot(document.getElementById('root')).render(<App/>);
