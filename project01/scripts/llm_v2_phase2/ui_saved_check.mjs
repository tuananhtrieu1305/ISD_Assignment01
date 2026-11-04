import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'../../..'),out=path.join(root,'project01/artifacts/llm_v2/phase2/ui');
const browser=await chromium.launch({executablePath:path.join(root,'.local/ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1050}}),checks=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
function ok(value,name){if(!value)throw Error(name);checks.push(name);}
try{
 await page.goto('http://127.0.0.1:8052');
 await page.getByText('Dữ liệu & cấu hình sẵn sàng',{exact:true}).waitFor();
 await page.getByText('Xem development đã lưu · không gọi API mới',{exact:true}).click();
 await page.getByRole('button',{name:'Bệnh thận có làm tăng nguy cơ tiểu đường không? ↗',exact:true}).click();
 const direct=page.getByRole('region',{name:'LLM trực tiếp',exact:true});
 const rag=page.getByRole('region',{name:'Đa agent + RAG',exact:true});
 ok(await direct.isVisible()&&await rag.isVisible(),'both comparison answer panels present');
 const answer=await direct.locator('.primary-answer').innerText();
 ok(answer.includes('bệnh thận')&&!answer.includes('**'),'actual saved answer rendered as escaped formatted text');
 ok(await rag.getByText('Chưa có kết quả',{exact:true}).isVisible(),'failed RAG never replaced with fabricated answer');
 ok(await page.getByText('Lượt development chưa hoàn tất do lỗi API; chỉ hiển thị nhánh có kết quả thật.',{exact:true}).isVisible(),'saved partial state retains failure notice');
 ok(await page.getByText('Development đã lưu · không phải lượt live mới',{exact:true}).isVisible(),'cache/saved lineage explicit');
 await page.screenshot({path:path.join(out,'partial-answer-desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});
 ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'answer mobile no horizontal overflow');
 await page.screenshot({path:path.join(out,'partial-answer-mobile.png'),fullPage:true});
 await page.getByRole('button',{name:/03.*So sánh/}).click();
 ok(await page.getByRole('heading',{name:'Đánh giá chưa hoàn tất'}).isVisible(),'new held-out remains pending');
 ok(errors.length===0,'no JS errors');
 await fs.writeFile(path.join(out,'saved_results_verification.json'),JSON.stringify({status:'PASS',checks,errors,mocked:false,new_LLM_calls:0,
  answer_source:'real persisted development direct output; RAG failed',live_full_pipeline_acceptance:'NOT_PASS_PROVIDER_TIMEOUT_503'},null,2));
 console.log(JSON.stringify({status:'PASS',checks}));
}finally{await browser.close();}
