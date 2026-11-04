// Deterministic, bounded force layout for the small local graph; no service or dependency.
export const GRAPH_WIDTH=1000;
export const GRAPH_HEIGHT=680;
export function layoutGraph(nodes,edges){
 const degree=Object.fromEntries(nodes.map(n=>[n.id,0]));
 edges.forEach(e=>{degree[e.source]=(degree[e.source]||0)+1;degree[e.target]=(degree[e.target]||0)+1;});
 const sorted=[...nodes].sort((a,b)=>(degree[b.id]-degree[a.id])||a.id.localeCompare(b.id));
 const points=Object.fromEntries(sorted.map((n,i)=>{const a=i*2.3999632297,r=45+Math.sqrt(i)*43;return [n.id,{x:500+Math.cos(a)*r,y:340+Math.sin(a)*r}];}));
 for(let iteration=0;iteration<260;iteration++){
  const force=Object.fromEntries(nodes.map(n=>[n.id,{x:0,y:0}]));
  for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){
   const a=nodes[i].id,b=nodes[j].id,dx=points[a].x-points[b].x,dy=points[a].y-points[b].y,d=Math.max(1,Math.hypot(dx,dy));
   const magnitude=7000/(d*d)+(d<85?(85-d)*.055:0);
   force[a].x+=dx/d*magnitude;force[a].y+=dy/d*magnitude;force[b].x-=dx/d*magnitude;force[b].y-=dy/d*magnitude;
  }
  for(const edge of edges){
   if(!points[edge.source]||!points[edge.target])continue;
   const a=edge.source,b=edge.target,dx=points[b].x-points[a].x,dy=points[b].y-points[a].y,d=Math.max(1,Math.hypot(dx,dy));
   const magnitude=(d-145)*.012/Math.sqrt(Math.max(1,degree[a],degree[b]));
   force[a].x+=dx/d*magnitude;force[a].y+=dy/d*magnitude;force[b].x-=dx/d*magnitude;force[b].y-=dy/d*magnitude;
  }
  const cooling=1-iteration/330;
  for(const n of nodes){const p=points[n.id],f=force[n.id];f.x+=(500-p.x)*.0015;f.y+=(340-p.y)*.0015;
   p.x=Math.max(65,Math.min(935,p.x+Math.max(-7,Math.min(7,f.x))*cooling));
   p.y=Math.max(55,Math.min(605,p.y+Math.max(-7,Math.min(7,f.y))*cooling));}
 }
 return points;
}
