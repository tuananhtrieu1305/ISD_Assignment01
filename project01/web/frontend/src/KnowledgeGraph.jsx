import React,{useEffect,useMemo,useRef,useState} from 'react';
import {GRAPH_WIDTH as W,GRAPH_HEIGHT as H,layoutGraph} from './kg-layout.js';
import './knowledge-graph.css';

const COLORS=['#2a61df','#0c9a8d','#bc6c25','#8958c7','#d65172','#4e8b46','#5a7c9b','#1a89b2'];
const RELATIONS={SUBTYPE_OF:'Là một loại',CHARACTERIZED_BY:'Đặc trưng bởi',SUPPORTS:'Hỗ trợ',INCREASES_RISK_OF:'Tăng nguy cơ',MAY_DAMAGE:'Có thể gây hại',HAS_SYMPTOM:'Có triệu chứng',ASSESSES:'Đánh giá'};
function label(node){return node?.aliases?.find(a=>/[\u00c0-\u1eff]/i.test(a))||node?.label||node?.id||'';}
function lines(text){const result=[''];for(const word of text.split(' ')){if((result[result.length-1]+' '+word).length>22)result.push(word);else result[result.length-1]+=(result[result.length-1]?' ':'')+word;}return result.length>2?[result[0],result[1]+'…']:result;}
function safeUrl(value){try{const u=new URL(value);return ['http:','https:'].includes(u.protocol)?u.href:null;}catch{return null;}}

export default function KnowledgeGraph({api}){
 const [data,setData]=useState(null),[error,setError]=useState(''),[query,setQuery]=useState('');
 const [selected,setSelected]=useState(null),[positions,setPositions]=useState({}),[zoom,setZoom]=useState(1),[pan,setPan]=useState({x:0,y:0});
 const [nearOnly,setNearOnly]=useState(false),[labels,setLabels]=useState(false);
 const svg=useRef(null),drag=useRef(null);
 useEffect(()=>{let active=true;api('/api/v2/knowledge-graph').then(value=>{if(active)setData(value);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[api]);
 const layout=useMemo(()=>data?layoutGraph(data.nodes,data.edges):{},[data]);
 useEffect(()=>{setPositions(layout);},[layout]);
 const types=useMemo(()=>[...new Set(data?.nodes.map(n=>n.type)||[])].sort(),[data]);
 const colors=Object.fromEntries(types.map((type,i)=>[type,COLORS[i%COLORS.length]]));
 const nodes=useMemo(()=>new Map(data?.nodes.map(n=>[n.id,n])||[]),[data]);
 const selectedNode=selected?.type==='node'?nodes.get(selected.id):null;
 const selectedEdge=selected?.type==='edge'?data?.edges.find(e=>e.id===selected.id):null;
 const neighbors=useMemo(()=>{const ids=new Set();if(selectedNode){ids.add(selectedNode.id);data.edges.forEach(e=>{if(e.source===selectedNode.id||e.target===selectedNode.id){ids.add(e.source);ids.add(e.target);}});}else if(selectedEdge){ids.add(selectedEdge.source);ids.add(selectedEdge.target);}return ids;},[data,selectedNode,selectedEdge]);
 const search=query.trim().toLocaleLowerCase('vi');
 const matches=useMemo(()=>new Set((data?.nodes||[]).filter(n=>!search||[n.id,n.label,...n.aliases].join(' ').toLocaleLowerCase('vi').includes(search)).map(n=>n.id)),[data,search]);
 function point(event){const value=svg.current.createSVGPoint();value.x=event.clientX;value.y=event.clientY;const matrix=svg.current.getScreenCTM();return matrix?value.matrixTransform(matrix.inverse()):{x:0,y:0};}
 function changeZoom(factor,anchor={x:W/2,y:H/2}){const next=Math.max(.45,Math.min(2.8,zoom*factor)),ratio=next/zoom;setPan({x:anchor.x-(anchor.x-pan.x)*ratio,y:anchor.y-(anchor.y-pan.y)*ratio});setZoom(next);}
 useEffect(()=>{const el=svg.current;if(!el)return;const wheel=event=>{event.preventDefault();changeZoom(event.deltaY<0?1.1:1/1.1,point(event));};el.addEventListener('wheel',wheel,{passive:false});return()=>el.removeEventListener('wheel',wheel);},[zoom,pan,data]);
 function down(event){if(event.button!==0)return;const node=event.target.closest('[data-node-id]'),edge=event.target.closest('[data-edge-id]'),p=point(event);
  if(edge)return;
  if(node){setSelected({type:'node',id:node.dataset.nodeId});drag.current={kind:'node',id:node.dataset.nodeId};}
  else drag.current={kind:'pan',x:p.x,y:p.y,pan};
  svg.current.setPointerCapture(event.pointerId);
 }
 function move(event){const active=drag.current;if(!active)return;const p=point(event);if(active.kind==='node')setPositions(old=>({...old,[active.id]:{x:(p.x-pan.x)/zoom,y:(p.y-pan.y)/zoom}}));else setPan({x:active.pan.x+p.x-active.x,y:active.pan.y+p.y-active.y});}
 function up(event){drag.current=null;if(svg.current?.hasPointerCapture(event.pointerId))svg.current.releasePointerCapture(event.pointerId);}
 function reset(){setZoom(1);setPan({x:0,y:0});setPositions(layout);setSelected(null);setQuery('');setNearOnly(false);}
 function focusNode(id){setSelected({type:'node',id});setQuery('');const p=positions[id];if(p){setZoom(1.25);setPan({x:W/2-p.x*1.25,y:H/2-p.y*1.25});}}
 if(error)return <section className="panel"><p role="alert">{error}</p></section>;
 if(!data)return <section className="panel"><p role="status">Đang đọc đồ thị tri thức…</p></section>;
 const visibleNodes=data.nodes.filter(n=>!nearOnly||!neighbors.size||neighbors.has(n.id));
 const visibleIds=new Set(visibleNodes.map(n=>n.id));
 const visibleEdges=data.edges.filter(e=>visibleIds.has(e.source)&&visibleIds.has(e.target));
 const related=selectedNode?data.edges.filter(e=>e.source===selectedNode.id||e.target===selectedNode.id):[];
 return <section className="knowledge-graph" aria-label="Đồ thị KG của kho tri thức">
  <div className="kg-toolbar"><div className="kg-search"><label htmlFor="kg-search">Tìm thực thể</label><input id="kg-search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Ví dụ: thận, vận động, tiểu đường…"/>{search&&<div className="kg-search-results">{[...matches].slice(0,6).map(id=><button key={id} onClick={()=>focusNode(id)}>{label(nodes.get(id))}</button>)}{!matches.size&&<span>Không tìm thấy thực thể.</span>}</div>}</div><div className="kg-counts"><strong>{data.nodes.length}</strong> thực thể <span>·</span> <strong>{data.edges.length}</strong> quan hệ có nguồn</div><div className="kg-controls"><button aria-label="Thu nhỏ đồ thị" onClick={()=>changeZoom(1/1.2)}>−</button><span>{Math.round(zoom*100)}%</span><button aria-label="Phóng to đồ thị" onClick={()=>changeZoom(1.2)}>+</button><button onClick={reset}>Đặt lại</button></div></div>
  <div className="kg-options"><label><input type="checkbox" checked={labels} onChange={e=>setLabels(e.target.checked)}/> Tên quan hệ</label><label><input type="checkbox" checked={nearOnly} onChange={e=>setNearOnly(e.target.checked)} disabled={!selected}/> Chỉ vùng đang chọn</label><span>Kéo nút để sắp xếp · kéo nền để di chuyển · cuộn để zoom</span></div>
  <div className="kg-canvas"><svg ref={svg} viewBox={`0 0 ${W} ${H}`} aria-label="Sơ đồ thực thể và quan hệ có hướng" onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up}>
   <defs><marker id="kg-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#7b8da8"/></marker><pattern id="kg-grid" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".7" fill="#dce4ee"/></pattern></defs>
   <rect width={W} height={H} fill="url(#kg-grid)"/>
   <g transform={`translate(${pan.x} ${pan.y}) scale(${zoom})`}>
    {visibleEdges.map((edge,index)=>{const a=positions[edge.source],b=positions[edge.target];if(!a||!b)return null;
     const dx=b.x-a.x,dy=b.y-a.y,d=Math.max(1,Math.hypot(dx,dy)),normal=(index%3-1)*20;
     const start={x:a.x+dx/d*24,y:a.y+dy/d*24},end={x:b.x-dx/d*29,y:b.y-dy/d*29};
     const cx=(a.x+b.x)/2-dy/d*normal,cy=(a.y+b.y)/2+dx/d*normal;
     const curve=`M${start.x},${start.y} Q${cx},${cy} ${end.x},${end.y}`;
     const active=selectedEdge?.id===edge.id||selectedNode&&(edge.source===selectedNode.id||edge.target===selectedNode.id);
     const dim=selected&&!active||search&&!matches.has(edge.source)&&!matches.has(edge.target);
     return <g key={edge.id} data-edge-id={edge.id} className={'kg-edge-line '+(active?'active ':'')+(dim?'dim':'')} role="button" tabIndex={0} aria-label={`${label(nodes.get(edge.source))} → ${RELATIONS[edge.relation]||edge.relation} → ${label(nodes.get(edge.target))}`} onClick={()=>setSelected({type:'edge',id:edge.id})} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelected({type:'edge',id:edge.id});}}}>
      <path d={curve} className="kg-edge-hit"/><path d={curve} className="kg-edge-stroke" markerEnd="url(#kg-arrow)"/>{(labels||active)&&<text x={(start.x+2*cx+end.x)/4} y={(start.y+2*cy+end.y)/4-5} textAnchor="middle">{RELATIONS[edge.relation]||edge.relation}</text>}
     </g>;
    })}
    {visibleNodes.map(node=>{const p=positions[node.id];if(!p)return null;const dim=selected&&neighbors.size&&!neighbors.has(node.id)||search&&!matches.has(node.id);const chosen=selectedNode?.id===node.id;
     return <g key={node.id} data-node-id={node.id} transform={`translate(${p.x} ${p.y})`} className={'kg-node '+(chosen?'selected ':'')+(dim?'dim':'')} role="button" tabIndex={0} aria-label={'Thực thể '+label(node)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelected({type:'node',id:node.id});}}}>
      <circle r={chosen?27:23} fill={colors[node.type]}/><text className="kg-node-initial" y="5" textAnchor="middle">{label(node).charAt(0).toUpperCase()}</text><text className="kg-node-label" y="42" textAnchor="middle">{lines(label(node)).map((line,index)=><tspan key={index} x="0" dy={index?14:0}>{line}</tspan>)}</text><title>{node.label} · {node.type}</title>
     </g>;
    })}
   </g>
  </svg></div>
  <div className="kg-legend">{types.map(type=><span key={type}><i style={{background:colors[type]}}/>{type}</span>)}</div>
  <section className="panel kg-inspector" aria-live="polite"><div><span className="eyebrow">ĐỐI CHIẾU TRI THỨC</span><h2>{selectedEdge?`${label(nodes.get(selectedEdge.source))} → ${label(nodes.get(selectedEdge.target))}`:selectedNode?label(selectedNode):'Chọn một nút hoặc cạnh'}</h2>{selectedEdge?<><p><b>{RELATIONS[selectedEdge.relation]||selectedEdge.relation}</b> <code>{selectedEdge.relation}</code></p>{selectedEdge.conditions&&<p>Điều kiện: {selectedEdge.conditions}</p>}</>:selectedNode?<><p>{selectedNode.label} · {selectedNode.type}</p><p>{related.length} quan hệ liên quan</p><div className="kg-related">{related.map(edge=><button key={edge.id} onClick={()=>setSelected({type:'edge',id:edge.id})}>{label(nodes.get(edge.source))} → {RELATIONS[edge.relation]||edge.relation} → {label(nodes.get(edge.target))}</button>)}</div></>:<p>Đây là mini-KG có kiểm nguồn đang hỗ trợ retrieval, không phải toàn bộ tri thức trong 316 đoạn KB. Mỗi cạnh giữ nguyên chiều và điều kiện của nguồn.</p>}</div><div>{selectedEdge?<><h3>Đoạn nguồn của quan hệ</h3><blockquote>{selectedEdge.quote}</blockquote>{safeUrl(selectedEdge.source_url)&&<a href={safeUrl(selectedEdge.source_url)} target="_blank" rel="noreferrer">Mở nguồn gốc ↗</a>}<small>{selectedEdge.source_chunk_ids.join(' · ')}</small></>:<p className="kg-inspector-hint">Bấm vào đường nối để đọc câu trích và nguồn. Các cạnh được trợ lý kiểm theo snapshot tài liệu, chưa phải thẩm định lâm sàng độc lập.</p>}</div></section>
 </section>;
}
