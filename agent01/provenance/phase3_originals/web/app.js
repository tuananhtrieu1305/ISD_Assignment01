'use strict';
const {maze, result} = DEMO_DATA;
const $ = id => document.getElementById(id);
const actions = [[0,-1],[0,1],[-1,0],[1,0]];
let mode='replay', index=0, moves=0, reward=0, position=[0,0], visited=new Set(['0,0']), timer=null, ended=false;
const cells=[];
maze.forEach((row,r)=>row.forEach((wall,c)=>{
  const cell=document.createElement('div');cell.className='cell'+(wall?' wall':'');
  if(!wall)cell.title=`Ô (${r}, ${c})`;
  $('maze').appendChild(cell);cells.push(cell);
}));
function draw(){
  cells.forEach((cell,i)=>{const r=Math.floor(i/10),c=i%10;cell.classList.toggle('visited',visited.has(`${r},${c}`));cell.classList.toggle('agent',r===position[0]&&c===position[1]);cell.classList.toggle('endpoint',i===0||i===99);cell.textContent=r===position[0]&&c===position[1]?'':i===0?'S':i===99?'G':'';});
  $('steps').replaceChildren(document.createTextNode(String(moves)));
  if(mode==='replay'){const small=document.createElement('small');small.textContent=' / '+result.learned_moves;$('steps').appendChild(small);}
  $('reward').textContent=reward;
  $('step').disabled=ended;$('play').disabled=ended;
  document.querySelectorAll('[data-action]').forEach(b=>b.disabled=ended);
  $('maze').setAttribute('aria-label',`Mê cung 10 nhân 10. Agent tại (${position}), ${moves} bước, tổng thưởng ${reward}. S: (0,0), G: (9,9).`);
}
function stop(){if(timer!==null)clearInterval(timer);timer=null;$('play').textContent='▶ Chạy demo';}
function reset(){stop();index=0;moves=0;reward=0;position=[0,0];visited=new Set(['0,0']);ended=false;$('status').textContent='Sẵn sàng tại ô (0, 0).';draw();}
function advance(){
  if(ended)return;
  index++;moves++;position=[...result.path[index]];visited.add(position.join(','));
  const goal=index===result.path.length-1;reward+=goal?50:-1;ended=goal;
  $('status').textContent=goal?`Đã đến đích! ${moves} bước · thưởng ${reward} · bằng BFS.`:`Ô (${position}) · nhận −1 · bước ${moves}.`;
  if(goal)stop();draw();
}
function manualMove(action){
  if(mode!=='manual'||ended)return;
  const d=actions[action],next=[position[0]+d[0],position[1]+d[1]];moves++;
  if(next[0]<0||next[0]>9||next[1]<0||next[1]>9||maze[next[0]][next[1]]){reward-=10;ended=true;$('status').textContent='Va tường hoặc ra ngoài: −10. Lượt kết thúc, bấm Thử lại.';}
  else{position=next;visited.add(position.join(','));ended=position[0]===9&&position[1]===9;reward+=ended?50:-1;$('status').textContent=ended?`Đến đích sau ${moves} bước! Tổng thưởng ${reward}.`:`Ô (${position}) · nhận −1.`;}
  if(!ended&&moves>=400){ended=true;$('status').textContent='Đã đạt giới hạn an toàn 400 bước. Bấm Thử lại.';}draw();
}
function setMode(next){mode=next;reset();const manual=mode==='manual';$('manual').setAttribute('aria-pressed',manual);$('replay').setAttribute('aria-pressed',!manual);$('playback').hidden=manual;$('manual-controls').hidden=!manual;$('mode-label').textContent=manual?'Bạn điều khiển':'Đường đi đã học';$('control-title').textContent=manual?'Bạn tìm được đường chứ?':'Theo dấu agent';$('description').textContent=manual?'Đưa agent từ S đến G. Chọn hướng đi để quan sát phần thưởng của môi trường.':'Phát lại chính sách greedy từ kết quả notebook đã thực thi, với seed 42.';}
$('play').onclick=()=>{if(timer!==null){stop();return;}timer=setInterval(advance,Number($('speed').value));$('play').textContent='Ⅱ Tạm dừng';};
$('speed').onchange=()=>{if(timer!==null){stop();$('play').click();}};
$('step').onclick=()=>{stop();advance();};$('reset').onclick=reset;$('manual-reset').onclick=reset;
$('manual').onclick=()=>setMode('manual');$('replay').onclick=()=>setMode('replay');
document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>manualMove(Number(b.dataset.action)));
document.addEventListener('keydown',e=>{if(mode!=='manual'||/INPUT|SELECT|TEXTAREA/.test(e.target.tagName))return;const map={ArrowLeft:0,ArrowRight:1,ArrowUp:2,ArrowDown:3};if(e.key in map){e.preventDefault();manualMove(map[e.key]);}});
draw();
