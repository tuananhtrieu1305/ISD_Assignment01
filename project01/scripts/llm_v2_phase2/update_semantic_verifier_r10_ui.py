"""Update the UI and budget config for the user-requested r10 verifier."""
from pathlib import Path
import json
P=Path(__file__).resolve().parents[2]
path=P/'web/frontend/src/main.jsx';source=path.read_text(encoding='utf-8')
edits=[
 ("[useProfile,setUseProfile]=useState(false)","[useProfile,setUseProfile]=useState(true)"),
 ("ready.runtime_revision!=='source-verification-r9'","ready.runtime_revision!=='semantic-verifier-r10'"),
 ("generationRemaining<3","generationRemaining<4"),
 ("{generationRemaining}/3 generation","{generationRemaining}/4 generation"),
 ('pipeline r9 có quy tắc kiểm chứng nguồn dùng chung (vẫn 3 generation).','pipeline r10: Risk mặc định bật và Verifier Gemini (4 generation).'),
 ('2 generation request · pre-retrieval + Reporter; rerank và kiểm chứng chạy local.','3 generation request · pre-retrieval + Reporter + Verifier Gemini; rerank chạy local.'),
 ('Mỗi lượt dùng đúng3 generation request.','Mỗi lượt hợp lệ dùng 4 generation request.'),
 ('BM25, KG, reranker và Code Verifier chạy local.','BM25, KG, reranker và Risk chạy local; Verifier gọi Gemini một lần.'),
 ('if(busy)return;clearTimeout(timer.current);','if(busy)return;if(useProfile&&!profileReady){setError("Hồ sơ chưa đủ hoặc không hợp lệ: "+profileIssues.join(", "));return;}clearTimeout(timer.current);'),
 ("disabled={busy||runtimeMismatch||insufficientBudget||ready?.status!=='ready'||!ready?.live_enabled}","disabled={busy||runtimeMismatch||insufficientBudget||(useProfile&&!profileReady)||ready?.status!=='ready'||!ready?.live_enabled}"),
 ("<p>{useProfile?'Đã kèm hồ sơ CDC đủ 21 trường.","<p>{useProfile&&profileReady?'Đã kèm hồ sơ CDC đủ 21 trường."),
 ("Chưa gửi câu hỏi hoặc gọi Gemini.'}</p></div>","Chưa gửi câu hỏi hoặc gọi Gemini.'}</p><div className=\"demo-mode\" role=\"group\" aria-label=\"Chế độ xử lý\"><button type=\"button\" disabled={busy} aria-pressed={useProfile} onClick={()=>setUseProfile(true)}>Đủ 5 agent · kèm hồ sơ TRAIN</button><button type=\"button\" disabled={busy} aria-pressed={!useProfile} onClick={()=>setUseProfile(false)}>Chỉ hỏi kiến thức · bỏ Risk</button></div>{useProfile&&!profileReady&&<p role=\"status\">{examples?'Hồ sơ cần sửa: '+profileIssues.join(', '):'Đang tải hồ sơ TRAIN mẫu…'}</p>}</div>"),
 ("const local=result.verification?.provider==='local_code';","const local=result.verification?.provider==='local_code';\n const semantic=result.verification?.provider==='gemini_semantic_plus_local_integrity';"),
 ("{local?'Code Verifier kiểm gì?':'Verifier lịch sử kiểm gì?'}","{semantic?'Verifier Gemini kiểm gì?':local?'Code Verifier kiểm gì?':'Verifier lịch sử kiểm gì?'}"),
 ("{local?'Chỉ kiểm tra schema, citation, provenance và số liệu bằng Python;", "{semantic?'Gemini kiểm ý nghĩa/điều kiện/số và có thể sửa bản nháp trong một request. Code vẫn kiểm citation/hash/score CDC. Đây là cùng model, không phải thẩm định lâm sàng độc lập.':local?'Chỉ kiểm tra schema, citation, provenance và số liệu bằng Python;")
]
for old,new in edits:
    assert source.count(old)==1,(old,source.count(old))
    source=source.replace(old,new)
marker=" const insufficientBudget=ready?.status==='ready'&&generationRemaining<4;"
addition="""
 const profileIssues=useProfile?Object.entries(examples?.schema?.limits||{}).filter(([name,bounds])=>typeof profile[name]!=='number'||!Number.isFinite(profile[name])||profile[name]<bounds[0]||profile[name]>bounds[1]||(name!=='bmi'&&!Number.isInteger(profile[name]))).map(([name])=>name):[];
 const profileReady=Boolean(examples&&Object.keys(profile).length===21&&profileIssues.length===0);
"""
assert source.count(marker)==1;source=source.replace(marker,marker+addition)
path.write_text(source,encoding='utf-8')

path=P/'web/frontend/src/PipelineFlow.jsx';source=path.read_text(encoding='utf-8')
old=source[source.index('function AgentRoles('):source.index('\nexport default function PipelineFlow')]
new="""function AgentRoles({result}){
  const current=result?.verification?.provider==='gemini_semantic_plus_local_integrity'||!result;
  const count=result?.generation_calls_contract?.comparison_total||(current?4:3);
  return <div className="agent-role-map"><div><small>01 · COORDINATOR</small><b>Gemini pre-retrieval</b><span>1 generation · lập intent, truy vấn và chiều quan hệ.</span></div><div><small>02 · KNOWLEDGE AGENT</small><b>BM25 + embedding + KG</b><span>Truy hồi; reranker local, không gọi generation.</span></div><div><small>03 · RISK AGENT</small><b>Checkpoint NumPy CDC</b><span>Chế độ đủ 5 agent gửi hồ sơ 21 field; không gọi API.</span></div><div><small>04 · REPORTER</small><b>Gemini tạo câu trả lời</b><span>1 generation · evidence và kết quả Risk.</span></div><div><small>05 · VERIFIER</small><b>{current?'Gemini + kiểm integrity':'Quy tắc Python · lịch sử'}</b><span>{current?'1 generation · kiểm ý nghĩa/số; code giữ citation và score.':'Revision này chưa có kiểm ngữ nghĩa bằng Gemini.'}</span></div><p>Nhánh LLM trực tiếp dùng thêm 1 generation riêng. Tổng một lượt so sánh: <strong>{count} generation request</strong>. Embedding query thuộc hạn mức embedding riêng. {result?.trace_revision&&<em>{result.trace_revision}</em>}</p></div>;
}
"""
source=source.replace(old,new).replace('<AgentRoles readyRevision={result?.trace_revision}/>','<AgentRoles result={result}/>')
source=source.replace("{review.feedback&&<p>{review.feedback}</p>}","{review.feedback&&<p>{review.feedback}</p>}{review.draft_revised&&<details><summary>Bản đã được Verifier sửa và kiểm</summary><AnswerText text={review.revised_draft?.answer_vi||''}/></details>}")
path.write_text(source,encoding='utf-8')

path=P/'docs/llm_v2/runtime_config.json';config=json.loads(path.read_text(encoding='utf-8'))
config['config_version']='llm-v2-semantic-verifier-r10'
config['pipeline'].update(verifier_provider='gemini_semantic_plus_local_integrity',generation_calls_per_rag=3,generation_calls_per_comparison=4)
config['token_limits']['verifier_output']=1280
path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
