import React from 'react';
import './answer.css';

const ERROR_TEXT={
  request_outside_academic_scope:'Yêu cầu vượt phạm vi demo học thuật; hệ thống không đưa ra chẩn đoán, đơn thuốc hoặc liều điều trị cá nhân.',
  non_diabetes_domain:'Câu hỏi nằm ngoài chủ đề tiểu đường mà demo này hỗ trợ.',
  model_unavailable:'Chưa gọi được mô hình; không có kết quả phân loại hồ sơ.',
  index_unavailable:'Bộ tìm kiếm tri thức chưa sẵn sàng.',
  numeric_mismatch_rejected:'Kết quả số không nhất quán đã bị chặn.',
  unsupported_knowledge_rejected:'Phần trả lời không đạt kiểm tra bằng chứng đã bị chặn.',
  deadline:'Yêu cầu quá thời gian xử lý.',
  worker_error:'Công cụ gặp lỗi nên chưa thể hoàn tất yêu cầu.',
};
const FALLBACK={
  timeout:'Yêu cầu đã quá thời gian xử lý. Chưa có câu trả lời cuối cùng; bạn có thể thử lại.',
  insufficient_evidence:'Chưa tìm được trích đoạn đủ hỗ trợ câu hỏi trong kho hiện tại. Hãy hỏi cụ thể hơn hoặc thử một ví dụ có sẵn.',
  unavailable:'Chưa thể hoàn tất yêu cầu vì công cụ chưa cung cấp đủ kết quả.',
  refused:'Yêu cầu nằm ngoài phạm vi hỗ trợ của demo này.',
  clarification:'Cần bổ sung hồ sơ trước khi có thể chạy mô hình.',
};

export default function FinalAnswer({output,submitted}){
  // Present backend answer.sections; never invent a new medical synthesis in React.
  const sections=output.answer?.sections||[];
  const knowledge=sections.filter(section=>section.title==='Bằng chứng truy hồi · tiếng Anh');
  const model=sections.filter(section=>section.title==='Đầu ra mô hình khảo sát');
  const other=sections.filter(section=>!['Bằng chứng truy hồi · tiếng Anh','Đầu ra mô hình khảo sát','Giới hạn xử lý'].includes(section.title));
  const errors=(output.errors||[]).map(code=>ERROR_TEXT[code]||'Có phần chưa thể xử lý; xem chi tiết công cụ bên dưới.');
  const meaningful=knowledge.length+model.length+other.length;
  const query=submitted?.question||output.knowledge?.query_original;
  const hasKnowledge=submitted?.mode==='knowledge'||submitted?.mode==='combined';
  const citations=output.knowledge?.citations||[];
  return <section className="panel final-answer" aria-label="Câu trả lời cuối cùng">
    <div className="answer-heading"><div><span className="eyebrow">KẾT QUẢ CUỐI CÙNG · {output.variant}</span><h2>Câu trả lời cho bạn</h2></div><span className="tag">{output.variant==='P2'?'Có quy trình kiểm chứng':'Đầu ra công cụ trực tiếp'}</span></div>
    {query&&<div className="answered-question"><span>CÂU HỎI ĐÃ GỬI</span><p>{query}</p></div>}
    {knowledge.map((section,index)=><section className="answer-text" key={`knowledge-${index}`}><h3>Trả lời từ kho tri thức</h3><p lang="en">{section.text}</p></section>)}
    {hasKnowledge&&!knowledge.length&&<p className="answer-empty">{FALLBACK[output.status]||'Phần kiến thức chưa có trích đoạn đủ hỗ trợ để trả lời câu hỏi.'}</p>}
    {model.map((section,index)=><section className="answer-model" key={`model-${index}`}><h3>Kết quả từ hồ sơ khảo sát</h3><p>{section.text}</p></section>)}
    {other.map((section,index)=><section className="answer-notice" key={`notice-${index}`}><h3>{section.title}</h3><p>{section.text}</p></section>)}
    {!meaningful&&!hasKnowledge&&<p className="answer-empty">{FALLBACK[output.status]||'Chưa có câu trả lời cuối cùng từ các công cụ.'}</p>}
    {errors.length>0&&<div className="answer-notice"><h3>Phần chưa thể thực hiện</h3>{[...new Set(errors)].map(text=><p key={text}>{text}</p>)}</div>}
    <div className="answer-footer">{citations.length>0&&<a href="#supporting-details" onClick={()=>{const details=document.getElementById('supporting-details');if(details)details.open=true;}}>Đối chiếu {citations.length} đoạn được trích dẫn ↓</a>}<p>{knowledge.length?'Phần kiến thức là trích xuất tiếng Anh từ tài liệu, chưa phải bài trả lời viết lại bằng LLM. ':''}Demo học thuật; đầu ra mô hình không phải chẩn đoán hoặc xác suất mắc bệnh cá nhân đã hiệu chuẩn.</p></div>
  </section>;
}
