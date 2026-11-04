// Error-path UI checks. Compare/job responses intercepted; zero Gemini calls.
import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'../../..');
const out=path.join(root,'project01/artifacts/llm_v2/phase2/development/job_lifecycle_r4');
const browser=await chromium.launch({executablePath:path.join(root,'.local/ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
const checks=[],errors=[];
function ok(value,name){if(!value)throw Error(name);checks.push(name);}
try{
 const page=await browser.newPage({viewport:{width:1440,height:1050}});
 page.on('pageerror',e=>errors.push(e.message));
 let polls=0,compares=0;
 await page.route('**/api/v2/compare',route=>{compares++;return route.fulfill({json:{id:'synthetic-timeout',status:'queued'},status:202});});
 await page.route('**/api/v2/jobs/synthetic-timeout',route=>{
  polls++;
  const running=polls===1;
  return route.fulfill({json:{id:'synthetic-timeout',status:running?'running':'failed',question:'Vận động có ích gì cho cân nặng và đường huyết?',results:{},
   progress:running?'LLM trực tiếp · chờ Gemini':'Đã dừng do lỗi',created_at:Date.now()/1000-60,observed_at:Date.now()/1000,
   elapsed_seconds:running?60:180,stage_elapsed_seconds:running?60:180,
   branch_states:{llm_direct:running?'running':'failed',agentic_rag:running?'pending':'skipped'},
   error:running?null:{code:'unknown',error_type:'APITimeoutError',message:'Gemini không trả kết quả trong khoảng 180 giây (timeout). Không tự gọi lại; kết quả xử lý tại provider chưa xác định.'}}});
 });
 await page.goto('http://127.0.0.1:8031');
 await page.getByRole('button',{name:'So sánh hai câu trả lời'}).click();
 await page.getByText('Chưa đến lượt',{exact:true}).waitFor();
 ok(await page.getByText(/Đã chờ: 60 giây/).isVisible(),'elapsed and stage timers visible while Gemini is pending');
 ok(await page.getByText('Chờ nhánh LLM trực tiếp hoàn tất; nhánh này chưa gửi request.',{exact:true}).isVisible(),'RAG correctly labelled pending rather than generating');
 await page.getByText(/Gemini không trả kết quả trong khoảng 180 giây/).waitFor({timeout:12000});
 ok(await page.locator('.spinner').count()===0,'spinner stops on provider timeout');
 ok(await page.getByText('Chưa chạy do bước trước bị lỗi',{exact:true}).isVisible(),'RAG skipped status shown on provider timeout');
 ok(await page.getByText('Tổng thời gian: 180 giây',{exact:true}).isVisible(),'terminal elapsed freezes at measured duration');
 await page.waitForTimeout(5500);
 ok(polls===2&&compares===1,'terminal job polling stops and no automatic compare retry');
 await page.screenshot({path:path.join(out,'timeout-desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});
 ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'timeout UI mobile has no horizontal overflow');
 await page.screenshot({path:path.join(out,'timeout-mobile.png'),fullPage:true});
 await page.getByRole('button',{name:/01.*Câu hỏi/}).click();
 ok(await page.getByRole('button',{name:'So sánh hai câu trả lời'}).isEnabled(),'input unlocked after terminal error');
 ok(errors.length===0,'no frontend runtime errors');
 await fs.writeFile(path.join(out,'ui_checks.json'),JSON.stringify({status:'PASS',checks,errors,compare_posts_intercepted:compares,new_live_API_calls:0,
  mock_scope:'synthetic timeout lifecycle only; not answer quality or live provider availability'},null,2));
 console.log(JSON.stringify({status:'PASS',checks}));
}finally{await browser.close();}
