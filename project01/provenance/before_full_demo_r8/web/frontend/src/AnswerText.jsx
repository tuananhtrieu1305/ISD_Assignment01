import React from 'react';

// A small text-only renderer: React escapes all model text; no HTML execution.
export default function AnswerText({text}){
  return <>{String(text||'Không có câu trả lời hoàn chỉnh.').split('\n').map((line,index)=><p key={index} className={line.trim()?'answer-line':'answer-space'}>{line.split(/(\*\*[^*]+\*\*)/g).map((part,i)=>part.startsWith('**')&&part.endsWith('**')?<strong key={i}>{part.slice(2,-2)}</strong>:part.startsWith('*')&&part.endsWith('*')?<em key={i}>{part.slice(1,-1)}</em>:<React.Fragment key={i}>{part}</React.Fragment>)}</p>)}</>;
}
