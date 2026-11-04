// Render actual saved Gemini3 outputs, never submit a new compare request.
import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'../../..');
const out=path.join(root,'project01/artifacts/llm_v2/phase2/development/gemini3_switch_r5');
const row=JSON.parse(await fs.readFile(path.join(out,'gemini3-r5d/development.json'),'utf8'));
const ready=JSON.parse(await fs.readFile(path.join(out,'readiness_snapshot.json'),'utf8'));
const browser=await chromium.launch({executablePath:path.join(root,'.local/ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
const checks=[],errors=[];let posts=0;
function ok(v,n){if(!v)throw Error(n);checks.push(n);}
try{
 const page=await browser.newPage({viewport:{width:1440,height:1050}});
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/v2/compare',route=>{posts++;return route.abort();});
 await page.route('**/ready',route=>route.fulfill({json:{...ready,live_enabled:false}}));
 await page.route('**/api/v2/development',route=>route.fulfill({json:{mode:'saved_development_not_new_live_call',rows:[row]}}));
 await page.goto('http://127.0.0.1:8031');
 await page.getByText('Xem development đã lưu · không gọi API mới',{exact:true}).click();
 await page.getByRole('button',{name:/Vận động.*Gemini 3 Flash.*Hoàn tất/}).click();
 ok(await page.getByText('Development đã lưu · không phải lượt live mới',{exact:true}).isVisible(),'saved development lineage visible');
 const direct=page.getByRole('region',{name:'LLM trực tiếp',exact:true});
 const rag=page.getByRole('region',{name:'Đa agent + RAG',exact:true});
 const normalize=text=>text.replaceAll('**','').replace(/\s+/g,' ').trim();
 ok(normalize(await direct.locator('.primary-answer').innerText())===normalize(row.results.llm_direct.answer_vi),'actual direct answer displayed as escaped formatted text');
 ok((await rag.locator('.primary-answer').innerText()).includes('Vận động thể chất'),'actual verified RAG answer displayed');
 ok(await page.getByText('Gemini 3 Flash (preview)',{exact:true}).count()===2,'both answer panels label actual Gemini3 model');
 await page.getByText('Nguồn, KG & kiểm chứng · 4 đoạn được dùng',{exact:true}).click();
 ok(await page.locator('.supporting-evidence a').count()===4,'four original source URLs available');
 await page.screenshot({path:path.join(out,'saved-pair-desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});
 ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'saved pair mobile no horizontal overflow');
 await page.screenshot({path:path.join(out,'saved-pair-mobile.png'),fullPage:true});
 ok(errors.length===0&&posts===0,'no JS errors and no generation POST submitted');
 await fs.writeFile(path.join(out,'saved_UI_checks.json'),JSON.stringify({status:'PASS',checks,errors,new_live_API_calls:0,
  source:'actual saved gemini3-r5d outputs; GET readiness/development routed to these local receipts',clinical_review:false},null,2));
 console.log(JSON.stringify({status:'PASS',checks}));
}finally{await browser.close();}
