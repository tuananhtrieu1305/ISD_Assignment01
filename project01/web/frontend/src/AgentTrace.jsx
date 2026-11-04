import React from 'react';

const format=value=>value==null?'—':Number(value).toLocaleString('vi-VN',{maximumFractionDigits:3});

export default function AgentTrace({output}){
  return <section className="trace inline-trace" aria-label="Nhật ký xử lý chi tiết">
    {(output.trace||[]).map((node,index)=><article key={node.node_id}><div className="trace-dot">{index+1}</div><div><div className="trace-heading"><h3>{node.agent}</h3><span>{format(node.duration_ms)} ms</span></div><p><code>{node.tool}</code><span className="tag">{node.outcome}</span></p><details><summary>Kết quả bước xử lý</summary><pre>{JSON.stringify(node.output,null,2)}</pre></details></div></article>)}
    {!output.trace?.length&&<p>Chưa nhận được trace; không suy thời gian hoặc số công cụ bằng 0.</p>}
    <div className="info">Worker đã kết thúc: {output.worker_terminated?'Có':'Chưa xác nhận'}. Nhật ký ghi hành động, công cụ và kết quả.</div>
  </section>;
}
