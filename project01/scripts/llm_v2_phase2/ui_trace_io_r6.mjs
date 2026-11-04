// Render local saved outputs only. No compare/resume route may reach the backend.
import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';

const root=path.resolve(import.meta.dirname,'../../..');
const out=path.join(root,'project01/artifacts/llm_v2/phase2/development/trace_io_r6');
const row=JSON.parse(await fs.readFile(path.join(root,'project01/artifacts/llm_v2/phase2/development/gemini3_switch_r5/gemini3-r5d/development.json'),'utf8'));
const browser=await chromium.launch({executablePath:path.join(root,'.local/ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
const checks=[],errors=[];let mutationPosts=0;
function ok(value,name){if(!value)throw Error(name);checks.push(name);}

try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',error=>errors.push(error.message));
  for(const pattern of ['**/api/v2/compare','**/api/v2/jobs/*/resume']){
    await page.route(pattern,route=>{mutationPosts++;return route.abort();});
  }
  await page.route('**/ready',route=>route.fulfill({json:{status:'ready',index_ready:true,key_present:true,
    generation_model:'gemini-3-flash-preview',generation_endpoint:'v1beta/generateContent',runtime_revision:'trace-io-r6',
    embedding_model:'gemini-embedding-001',chunks:316,kg_assertions:35,live_enabled:false,usage:{generation_attempts:16}}}));
  await page.route('**/api/v2/development',route=>route.fulfill({json:{mode:'saved_development_not_new_live_call',rows:[row]}}));
  await page.route('**/api/v2/examples',route=>route.continue());
  await page.goto('http://127.0.0.1:8031');
  ok((await page.locator('textarea').inputValue())==='Bệnh thận có làm tăng nguy cơ tiểu đường không?','short kidney question is default');
  await page.getByText('Xem development đã lưu · không gọi API mới',{exact:true}).click();
  await page.getByRole('button',{name:/Vận động.*Gemini 3 Flash.*Hoàn tất/}).click();
  await page.getByRole('button',{name:/03.*Luồng xử lý/}).click();
  ok(await page.getByRole('heading',{name:'Mỗi bước nhận gì, trả gì.'}).isVisible(),'dedicated pipeline heading visible');
  ok(await page.getByText('Kết quả lịch sử',{exact:true}).isVisible(),'legacy reconstruction is explicit');
  ok(await page.getByText('Pre-retrieval',{exact:true}).first().isVisible(),'pre-retrieval stage visible');
  ok(await page.getByText('20 ứng viên',{exact:true}).first().isVisible(),'retrieval candidate count visible');
  ok(await page.getByText('6 evidence sau rerank',{exact:true}).isVisible(),'rerank retained count visible');
  ok(await page.getByText(/Bản nháp Reporter ban đầu không được lưu/).isVisible(),'missing reporter draft is not fabricated');
  ok(await page.getByText('Kết quả cuối',{exact:true}).first().isVisible(),'release stage visible');
  ok(await page.getByText('Đọc tab này không gửi thêm request Gemini.').isVisible(),'zero-call tab note visible');
  await page.screenshot({path:path.join(out,'pipeline-saved-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'pipeline mobile has no page overflow');
  await page.screenshot({path:path.join(out,'pipeline-saved-mobile.png'),fullPage:true});
  ok(errors.length===0&&mutationPosts===0,'no JS errors and no mutation request');
  const receipt={status:'PASS',checks,errors,mutation_posts:mutationPosts,new_live_API_calls:0,
    fixture:'actual saved gemini3-r5d output; pipeline legacy view labels missing intermediate outputs',clinical_review:false};
  await fs.writeFile(path.join(out,'ui_checks.json'),JSON.stringify(receipt,null,2));
  console.log(JSON.stringify(receipt));
}finally{
  await browser.close();
}
