'use strict';
const $=id=>document.getElementById(id);
const fmt=(v,d=0)=>Number(v).toLocaleString('vi-VN',{minimumFractionDigits:d,maximumFractionDigits:d});
const action=a=>a?'Giảm giá 20%':'Giữ giá';
let cursor=0,totals=[0,0],timer=null;
function stop(){if(timer!==null)clearInterval(timer);timer=null;$('play').textContent='▶ Phát lại';}
function step(){
  if(cursor>=AG02_DATA.trace.length)return;
  const row=AG02_DATA.trace[cursor++];
  for(let a=0;a<2;a++){totals[a]+=row.rewards[a];$('action'+a).textContent=action(row.actions[a]);$('sales'+a).textContent=row.sales[a];$('reward'+a).textContent=fmt(row.rewards[a]);$('total'+a).textContent=fmt(totals[a]);}
  $('progress').value=cursor;$('progress-label').textContent=`Bước ${cursor} / ${AG02_DATA.trace.length}`;$('demand').textContent='Nhu cầu trước action: '+(row.states_before[0][0]?'cao':'thấp');
  const tr=document.createElement('tr');[row.step,row.states_before[0][0]?'Cao':'Thấp',action(row.actions[0]),action(row.actions[1]),row.sales.join(' / '),row.rewards.join(' / ')].forEach(value=>{const td=document.createElement('td');td.textContent=value;tr.appendChild(td);});$('trace-table').appendChild(tr);
  $('status').textContent=`Bước ${cursor}: A nhận ${row.rewards[0]}, B nhận ${row.rewards[1]} đơn vị lợi nhuận.`;
  if(cursor===AG02_DATA.trace.length){stop();$('step').disabled=true;$('play').disabled=true;$('status').textContent=`Đã hết episode train mẫu. Tổng thưởng A: ${fmt(totals[0])}, B: ${fmt(totals[1])}. Đây không phải điểm đánh giá cuối.`;}
}
function reset(){stop();cursor=0;totals=[0,0];$('trace-table').replaceChildren();$('progress').value=0;$('progress-label').textContent='Bước 0 / '+AG02_DATA.trace.length;$('demand').textContent='Nhu cầu: chưa bắt đầu';for(let a=0;a<2;a++){$('action'+a).textContent='Chưa hành động';$('sales'+a).textContent='—';$('reward'+a).textContent='—';$('total'+a).textContent='0';}$('play').disabled=false;$('step').disabled=false;$('status').textContent='Bấm Phát lại để xem hai shop hành động đồng thời và nhận thưởng.';}
$('play').onclick=()=>{if(timer!==null){stop();return;}timer=setInterval(step,Number($('speed').value));$('play').textContent='Ⅱ Tạm dừng';};
$('step').onclick=()=>{stop();step();};$('reset').onclick=reset;$('speed').onchange=()=>{if(timer!==null){stop();$('play').click();}};
const names={baseline:'Q-learning baseline',augmented:'Q thêm memory/time',rule:'Agent theo luật'};
function renderResults(){
  const rows=AG02_DATA.results.filter(r=>r.kernel===$('kernel').value);$('comparison').replaceChildren();
  for(const policy of ['baseline','augmented','rule']){const r=rows.find(r=>r.policy===policy),row=document.createElement('div');row.className='comparison-row';const label=document.createElement('span');label.textContent=names[policy];const track=document.createElement('div');track.className='bar-track';track.setAttribute('aria-hidden','true');const bar=document.createElement('div');bar.className='bar';bar.style.width=(Number(r.profit_mean)/50*100)+'%';track.appendChild(bar);const score=document.createElement('span');score.className='score';score.textContent=fmt(r.profit_mean,5)+' ± '+fmt(r.profit_std,5);row.appendChild(label);row.appendChild(track);row.appendChild(score);$('comparison').appendChild(row);}
  const base=rows.find(r=>r.policy==='baseline'),aug=rows.find(r=>r.policy==='augmented');$('result-note').textContent=`Lợi nhuận trung bình/bước ± std. Thanh thể hiện mean trên cùng thang 0–50. Trong kịch bản này, Q thêm memory/time thấp hơn baseline ${fmt(base.profit_mean-aug.profit_mean,5)} đơn vị/bước. Thiết kế state đầy đủ hơn chưa bảo đảm học tốt hơn trong budget hiện tại.`;
}
$('kernel').onchange=renderResults;
function renderFigure(){const f=AG02_DATA.figures[Number($('figure-select').value)];$('figure').src=f.local;$('figure').alt=f.id+' · '+f.caption_text;$('figure-caption').textContent=f.caption_text;$('figure-source').textContent='Nguồn: '+f.path;}
AG02_DATA.figures.forEach((f,i)=>{const opt=document.createElement('option');opt.value=i;opt.textContent=f.id+' · '+f.path.split('/').pop().replace('.png','').replaceAll('_',' ');$('figure-select').appendChild(opt);});$('figure-select').value='0';$('figure-select').onchange=renderFigure;
function calculate(e){if(e)e.preventDefault();const old=Number($('old-q').value),alpha=Number($('alpha').value),r=Number($('r').value),gamma=Number($('gamma').value),future=Number($('future').value);if(![old,alpha,r,gamma,future].every(Number.isFinite)||alpha<0||alpha>1||gamma<0||gamma>1){$('q-result').textContent='Nhập số hữu hạn; α và γ cần nằm từ 0 đến 1.';return;}const target=$('terminal').checked?r:r+gamma*future;const updated=old+alpha*(target-old);$('q-result').textContent=`Target = ${fmt(target,4)}\nChênh lệch = ${fmt(target-old,4)}\nQ mới = ${fmt(updated,4)}${$('terminal').checked?' · terminal: không dùng giá trị tương lai':''}`;}
$('q-form').onsubmit=calculate;renderResults();renderFigure();calculate();
