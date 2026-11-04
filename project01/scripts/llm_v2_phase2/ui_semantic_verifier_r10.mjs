// New built UI with intercepted local jobs, no provider call or user server restart.
import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'../../..'),P=path.join(root,'project01');
const out=path.join(P,'artifacts/llm_v2/phase2/development/semantic_verifier_r10');
const fixture=JSON.parse(await fs.readFile(path.join(out,'offline_pipeline_fixture.json'),'utf8'));
const profiles=JSON.parse(await fs.readFile(path.join(P,'datasets/demo_profiles.json'),'utf8'));
const schema=JSON.parse(await fs.readFile(path.join(P,'datasets/profile_schema.json'),'utf8'));
const checks=[],errors=[];let posts=0,payload=null,used=0,missingBMI=false;
const ok=(value,name)=>{assert(value,name);checks.push(name);};
const browser=await chromium.launch({headless:true,executablePath:path.join(root,'.local/ms-playwright/chromium-1248/chrome-win64/chrome.exe')});
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 await context.route('**/*',async route=>{
  const url=new URL(route.request().url());if(url.hostname!=='offline-r10.local')return route.abort();
  const pathname=url.pathname;
  if(pathname==='/ready')return route.fulfill({json:{status:'ready',live_enabled:true,runtime_revision:'semantic-verifier-r10',generation_model:'gemini-3-flash-preview',generation_endpoint:'v1beta/generateContent',usage:{generation_cap:18,generation_attempts:used}}});
  if(pathname==='/api/v2/examples'){
   const rows=structuredClone(profiles.profiles);if(missingBMI)delete rows[0].profile.bmi;
   return route.fulfill({json:{questions:[],profiles:rows,schema}});
  }
  if(pathname==='/api/v2/summary')return route.fulfill({json:{}});
  if(pathname==='/api/v2/development')return route.fulfill({json:{rows:[]}});
  if(pathname==='/api/v2/compare'){posts++;payload=route.request().postDataJSON();return route.fulfill({json:{id:'offline-r10'}});}
  if(pathname==='/api/v2/jobs/offline-r10')return route.fulfill({json:{...fixture,elapsed_seconds:0}});
  return route.fulfill({path:path.join(P,'web/frontend/dist',pathname==='/'?'index.html':pathname.slice(1))});
 });
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://offline-r10.local',{waitUntil:'networkidle'});
 ok(await page.locator('input[type="checkbox"]').isChecked(),'Risk is enabled by default without using the preset button');
 ok(await page.getByText(/Đã kèm hồ sơ CDC đủ 21 trường/).isVisible(),'default TRAIN profile is disclosed');
 await page.getByRole('textbox').fill(fixture.question);
 await page.getByRole('button',{name:/So sánh hai câu trả lời/}).click();
 await page.getByText(/Kết quả công cụ CDC: score 0.395520/).first().waitFor();
 ok(payload.mode==='combined'&&Object.keys(payload.profile).length===21,'typing a custom question still sends all21 profile fields');
 ok(posts===1,'one click sends one local comparison job');
 await page.getByRole('button',{name:/03.*Luồng xử lý/}).click();
 ok(await page.locator('.pipeline-map a').count()===7&&await page.locator('.pipeline-map .skipped').count()===0,'all7 stages visible and Risk is not skipped');
 ok(await page.getByText('Gemini + kiểm integrity',{exact:true}).isVisible(),'role map names Gemini semantic verifier');
 ok(await page.getByText('4 generation request',{exact:true}).isVisible(),'role map shows new four-generation budget');
 ok(await page.locator('#pipeline-verifier').getByText('Đạt kiểm chứng',{exact:false}).isVisible(),'Verifier decision is rendered');
 await page.locator('#pipeline-verifier').screenshot({path:path.join(out,'offline-semantic-verifier-ui.png')});
 used=15;await page.reload({waitUntil:'networkidle'});
 ok(await page.getByRole('button',{name:/So sánh hai câu trả lời/}).isDisabled(),'three slots cannot start a four-generation comparison');
 used=0;missingBMI=true;await page.reload({waitUntil:'networkidle'});
 ok(await page.getByRole('button',{name:/So sánh hai câu trả lời/}).isDisabled(),'missing BMI is blocked before any job');
 ok(await page.getByText(/Hồ sơ cần sửa: bmi/).isVisible(),'missing field is named on the form');
 await page.getByRole('button',{name:'Chỉ hỏi kiến thức · bỏ Risk',exact:true}).click();
 ok(await page.getByRole('button',{name:/So sánh hai câu trả lời/}).isEnabled(),'explicit knowledge-only mode remains available');
 ok(posts===1&&errors.length===0,'no extra jobs or browser errors');
 const receipt={status:'PASS',checks,errors,intercepted_local_jobs:posts,new_generation_API_calls:0,new_embedding_API_calls:0,fixture:'offline engineering test; not Gemini quality evidence'};
 await fs.writeFile(path.join(out,'ui_verification.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));
}finally{await browser.close();}
