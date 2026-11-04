import React from 'react';
import './processing.css';

const VARIANTS=['P0','P1','P2'];
const EXPLANATIONS={
  P0:{title:'Gọi công cụ trực tiếp',text:'Chọn công cụ theo chế độ rồi đóng gói đầu ra. Lượt này không có agent kiểm chứng riêng.'},
  P1:{title:'Điều phối và chia nhiệm vụ',text:'Coordinator giao việc cho Risk / Knowledge Agent. Các công cụ vẫn giống P0; chưa có bước Verifier.'},
  P2:{title:'Điều phối, kiểm chứng và tổng hợp',text:'Sau các công cụ, Verifier kiểm đầu ra; Reporter trình bày kết quả. Chỉ tìm lại khi kiểm chứng yêu cầu.'},
};
const CHECK_NAMES={
  numeric_consistency:'Điểm nhất quán với logit, hồ sơ và model đã dùng',
  citation_integrity:'Nội dung và mã tài liệu khớp kho nguồn',
  verbatim_focused_claim_support:'Trích đoạn khớp nguồn và từ khóa chủ đề',
  numeric_available:'Có đầu ra mô hình theo yêu cầu',
  knowledge_available:'Có đầu ra truy hồi theo yêu cầu',
};
const number=(value,digits=1)=>value==null?'—':Number(value).toLocaleString('vi-VN',{maximumFractionDigits:digits});

function stages(result){
  const trace=result.trace||[];
  const plan=trace.find(node=>node.tool==='plan_request');
  const prediction=trace.filter(node=>node.tool==='predict_cdc');
  const validation=trace.find(node=>node.tool==='validate_profile');
  const retrieval=trace.filter(node=>node.tool.startsWith('retrieve_medical'));
  const verification=trace.filter(node=>node.tool.startsWith('check_outputs'));
  const compose=trace.find(node=>node.tool==='compose');
  const unseen=trace.length===0;
  const notRun=unseen?'Chưa nhận trace':'Không chạy';
  return [
    {key:'plan',title:plan?.agent==='Coordinator'?'Coordinator':'Chọn công cụ trực tiếp',nodes:plan?[plan]:[],status:plan?'Đã lập kế hoạch':notRun,
      detail:plan?.output.policy?'Yêu cầu bị từ chối theo phạm vi demo.':plan?`Cần ${[plan.output.need_risk&&'mô hình',plan.output.need_knowledge&&'tri thức'].filter(Boolean).join(' + ')||'không gọi công cụ'}.`:'Không có bước lập kế hoạch được ghi nhận.'},
    {key:'risk',title:'Risk Agent',nodes:[...(validation?[validation]:[]),...prediction],status:prediction.length?'Đã gọi mô hình':validation?'Cần bổ sung hồ sơ':notRun,
      detail:prediction.length?`${prediction.length} lần thử predict; ${result.risk?'có đầu ra được trả về':'đầu ra không được trả về'}.`:validation?`Thiếu: ${result.profile_validation?.missing?.join(', ')||'không'}; sai: ${[...(result.profile_validation?.invalid||[]),...(result.profile_validation?.extra||[])].join(', ')||'không'}.`:'Lượt này không ghi nhận xử lý hồ sơ.'},
    {key:'knowledge',title:'Knowledge Agent',nodes:retrieval,status:retrieval.length?'Đã truy hồi':notRun,
      detail:retrieval.length?`${retrieval.length} lần thử tìm kiếm; ${result.knowledge?.evidence?.length||0} đoạn ứng viên; ${result.retrieval_loops??'—'} lượt tìm bổ sung.`:'Lượt này không ghi nhận tìm kiếm kiến thức.'},
    {key:'verify',title:'Verifier',nodes:verification,status:verification.length?(result.verification?.status==='passed'?'Qua kiểm tra':'Có kiểm tra chưa đạt'):notRun,
      detail:verification.length?`${verification.length} lần kiểm tra; ${Object.keys(result.verification?.checks||{}).length} tiêu chí ở lần cuối.`:unseen?'Không đủ trace để xác định bước đã chạy.':'Không có bước kiểm chứng riêng trong lượt này.'},
    {key:'report',title:compose?.agent==='Reporter'?'Reporter':'Đóng gói trực tiếp',nodes:compose?[compose]:[],status:compose?'Đã trình bày':notRun,
      detail:compose?`${compose.output.section_count} phần kết quả; ${compose.agent==='Reporter'?'sau bước kiểm chứng nếu có đầu ra cần kiểm tra':'dùng kết quả công cụ, không thêm Verifier'}.`:'Không có bước trình bày được ghi nhận.'},
  ];
}

function equality(results,read){
  const rows=VARIANTS.map(key=>results[key]);
  if(rows.some(row=>!row))return 'Chờ đủ ba kết quả để đối chiếu.';
  if(rows.some(row=>!row.input_sha256)||new Set(rows.map(row=>row.input_sha256)).size!==1)return 'Các lượt chưa xác nhận cùng đầu vào.';
  const values=rows.map(read);
  if(values.every(value=>value==null))return 'Không có đầu ra này để đối chiếu.';
  if(values.some(value=>value==null))return 'Có cấu hình không trả đầu ra này.';
  return new Set(values.map(value=>JSON.stringify(value))).size===1?'Giống nhau ở cả ba lượt.':'Có khác biệt giữa các lượt.';
}

export default function ProcessingSummary({output,results,selected,onTrace}){
  const explanation=EXPLANATIONS[selected];
  const checks=Object.entries(output.verification?.checks||{});
  const rows=[
    {label:'Bước điều phối',read:row=>row.trace?.find(node=>node.tool==='plan_request')?.agent==='Coordinator'?'Coordinator':row.trace?.some(node=>node.tool==='plan_request')?'Gọi trực tiếp':'Chưa ghi nhận'},
    {label:'Bước Verifier',read:row=>row.trace?.some(node=>node.agent==='Verifier')?`${row.trace.filter(node=>node.tool.startsWith('check_outputs')).length} lần kiểm tra`:'Chưa ghi nhận'},
    {label:'Bước Reporter',read:row=>row.trace?.find(node=>node.tool==='compose')?.agent==='Reporter'?'Reporter':row.trace?.some(node=>node.tool==='compose')?'Đóng gói trực tiếp':'Chưa ghi nhận'},
    {label:'Tìm kiếm bổ sung',read:row=>row.retrieval_loops==null?'Chưa nhận số đo':`${row.retrieval_loops} lượt`},
    {label:'Số bước trace',read:row=>row.trace?.length?`${row.trace.length} bước`:'Chưa nhận trace'},
  ];
  return <section className="panel processing-summary" aria-label="So sánh cách xử lý">
    <div className="processing-heading"><div><span className="eyebrow">KHÁC NHAU Ở CÁCH XỬ LÝ</span><h2>{selected} · {explanation.title}</h2><p>{explanation.text}</p></div><button type="button" onClick={onTrace}>Xem trace đầy đủ ↗</button></div>
    <ol className="processing-stages" aria-label={`Các bước thực tế của ${selected}`}>
      {stages(output).map((stage,index)=><li key={stage.key} className={`${stage.nodes.length?'recorded':'not-recorded'} ${stage.key==='verify'?'verification-stage':''}`}><div className="stage-number">{String(index+1).padStart(2,'0')}<span>{stage.nodes.length?'Có trong trace':'Chưa ghi nhận'}</span></div><h3>{stage.title}</h3><strong>{stage.status}</strong><p>{stage.detail}</p>{stage.nodes.length>0&&<small>{number(stage.nodes.reduce((total,node)=>total+(node.duration_ms||0),0),3)} ms trong trace</small>}</li>)}
    </ol>
    <div className="processing-details">
      <section className="verification-detail" aria-label="Kiểm chứng lượt hiện tại"><h3>Kiểm chứng trong lượt {selected}</h3>{checks.length?<ul>{checks.map(([key,passed])=><li key={key}><span className={`check-mark ${passed?'pass':'fail'}`}>{passed?'Đạt':'Chưa đạt'}</span><span>{CHECK_NAMES[key]||key}</span></li>)}</ul>:<p>{output.verification?.status==='not_run'?'Lượt này không chạy Verifier hoặc chưa có bước kiểm chứng được trả về.':'Không có tiêu chí kiểm chứng đầu ra trong lượt này.'}</p>}<p className="footnote">Đây là kiểm tra tính nhất quán, nguồn và từ khóa; chưa phải đánh giá ngữ nghĩa của chuyên gia y khoa.</p></section>
      <section className="output-equality" aria-label="Đối chiếu đầu ra"><h3>Đầu ra có thực sự khác nhau?</h3><dl><dt>Điểm mô hình</dt><dd>{equality(results,row=>row.risk?{score:row.risk.score,class_id:row.risk.class_id}:null)}</dd><dt>Trích đoạn trả lời</dt><dd>{equality(results,row=>row.knowledge?.answer||null)}</dd><dt>Citation</dt><dd>{equality(results,row=>row.knowledge?.citations?.length?[...row.knowledge.citations].sort():null)}</dd></dl><p className="footnote">Cùng checkpoint và bộ truy hồi thường cho cùng đầu ra. Nhiều bước kiểm tra hơn không mặc nhiên tạo câu trả lời khác hoặc tốt hơn.</p></section>
    </div>
    <details className="processing-matrix"><summary>Đối chiếu các bước P0 / P1 / P2 của lượt chạy này</summary><div className="table-scroll"><table><thead><tr><th>Bước xử lý</th>{VARIANTS.map(key=><th key={key} className={key===selected?'current-column':''}>{key}{key===selected?' · đang xem':''}</th>)}</tr></thead><tbody>{rows.map(row=><tr key={row.label}><th scope="row">{row.label}</th>{VARIANTS.map(key=><td key={key} className={key===selected?'current-column':''}>{results[key]?row.read(results[key]):'Chưa chạy'}</td>)}</tr>)}</tbody></table></div></details>
  </section>;
}
