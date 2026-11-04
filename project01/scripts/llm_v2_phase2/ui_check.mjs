import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'../../..');
const out=path.join(root,'project01/artifacts/llm_v2/phase2/ui');await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:path.join(root,'.local/ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});const checks=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
function ok(value,name){if(!value)throw Error(name);checks.push(name);}
try{
 await page.goto('http://127.0.0.1:8052');await page.getByRole('heading',{name:'Hỏi rõ. Hiểu có căn cứ.'}).waitFor();
 ok(await page.getByRole('navigation',{name:'Khu vực demo'}).getByRole('button').count()===3,'three tabs');
 ok(await page.getByRole('button',{name:'So sánh hai câu trả lời'}).count()===1,'two-model comparison primary action');
 ok(await page.getByText('Chạy P0, P1 và P2',{exact:true}).count()===0,'old ablation absent from primary flow');
 await page.screenshot({path:path.join(out,'input-desktop.png'),fullPage:true});
 await page.getByRole('button',{name:/03.*So sánh/}).click();
 ok(await page.getByRole('heading',{name:'Đánh giá chưa hoàn tất'}).isVisible(),'honest pending evaluation no invented scores');
 await page.getByRole('button',{name:/01.*Câu hỏi/}).click();
 await page.setViewportSize({width:390,height:844});
 ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'mobile no page overflow');
 await page.screenshot({path:path.join(out,'input-mobile.png'),fullPage:true});
 ok(errors.length===0,'no JS runtime errors');
 await fs.writeFile(path.join(out,'layout_verification.json'),JSON.stringify({status:'PASS',checks,errors,mocked:false,live_LLM_calls:0,scope:'layout and real read-only API only; answer acceptance pending live development'},null,2));
 console.log(JSON.stringify({status:'PASS',checks}));
}finally{await browser.close();}
