// R7 UI contract test. Saved/synthetic fixtures only; every mutation route is aborted.
import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';

const root=path.resolve(import.meta.dirname,'../../..');
const out=path.join(root,'project01/artifacts/llm_v2/phase2/development/three_generation_r7');
await fs.mkdir(out,{recursive:true});
const saved=JSON.parse(await fs.readFile(path.join(root,'project01/artifacts/llm_v2/phase2/development/gemini3_switch_r5/gemini3-r5d/development.json'),'utf8'));
const row=structuredClone(saved);
row.claim_revision='synthetic-r7-ui-only';
row.results.agentic_rag.trace_revision='io-r7-three-generation';
row.results.agentic_rag.reranking={...(row.results.agentic_rag.reranking||{}),provider:'local_weighted_rrf_lexical_kg',api_calls:0};
row.results.agentic_rag.verification={...row.results.agentic_rag.verification,provider:'local_code',api_calls:0,semantic_review:'not_performed_local_code_only'};

const browser=await chromium.launch({executablePath:path.join(root,'.local/ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
const checks=[],errors=[];let mutationPosts=0;
function ok(value,name){if(!value)throw Error(name);checks.push(name);}
try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',error=>errors.push(error.message));
  for(const pattern of ['**/api/v2/compare','**/api/v2/jobs/*/resume'])await page.route(pattern,route=>{mutationPosts++;return route.abort();});
  await page.route('**/ready',route=>route.fulfill({json:{status:'ready',index_ready:true,key_present:true,
    generation_model:'gemini-3-flash-preview',generation_endpoint:'v1beta/generateContent',runtime_revision:'three-generation-r7',
    generation_calls_per_comparison:3,reranker_provider:'local_weighted_rrf_lexical_kg',verifier_provider:'local_code',
    embedding_model:'gemini-embedding-001',chunks:316,kg_assertions:35,live_enabled:true,
    usage:{generation_attempts:16,generation_cap:18,embedding_attempts:5,embedding_cap:900}}}));
  await page.route('**/api/v2/development',route=>route.fulfill({json:{mode:'synthetic_r7_ui_only',rows:[row]}}));
  await page.goto('http://127.0.0.1:8031');
  ok(await page.getByText(/Còn 2\/3 generation request cần thiết/).isVisible(),'UI warns when fewer than3 slots remain');
  ok(await page.getByRole('button',{name:/So sánh hai câu trả lời/}).isDisabled(),'new comparison is disabled under budget');
  ok(await page.getByText(/Mỗi lượt dùng đúng3 generation request/).isVisible(),'three-call contract visible');
  await page.getByText('Xem development đã lưu · không gọi API mới',{exact:true}).click();
  await page.getByRole('button',{name:/Vận động.*Gemini 3 Flash.*Hoàn tất/}).click();
  await page.getByRole('button',{name:/03.*Luồng xử lý/}).click();
  ok(await page.getByText('Gemini pre-retrieval',{exact:true}).isVisible(),'Coordinator tool visible');
  ok(await page.getByText('BM25 + embedding + KG',{exact:true}).isVisible(),'Knowledge tools visible');
  ok(await page.getByText('Checkpoint NumPy CDC',{exact:true}).isVisible(),'Risk tool visible');
  ok(await page.getByText('Gemini tạo câu trả lời',{exact:true}).isVisible(),'Reporter tool visible');
  ok(await page.getByText('Quy tắc Python',{exact:true}).isVisible(),'Code Verifier tool visible');
  ok(await page.getByText(/Tổng một lượt so sánh: 3 generation request/).isVisible(),'agent map explains total calls');
  await page.screenshot({path:path.join(out,'roles-and-three-call-budget.png'),fullPage:true});
  ok(errors.length===0&&mutationPosts===0,'no JS errors and no mutation request');
  const receipt={status:'PASS',checks,errors,mutation_posts:mutationPosts,new_live_API_calls:0,
    fixture:'saved r5 answer with synthetic r7 metadata for presentation only; not a model-quality result'};
  await fs.writeFile(path.join(out,'ui_checks.json'),JSON.stringify(receipt,null,2));
  console.log(JSON.stringify(receipt));
}finally{await browser.close();}
