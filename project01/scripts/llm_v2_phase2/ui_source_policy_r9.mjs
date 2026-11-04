// Built-UI check with intercepted local API. No Gemini request is made.
import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(import.meta.dirname,'../../..'),project=path.join(root,'project01');
const out=path.join(project,'artifacts/llm_v2/phase2/development/source_policy_r9');
const profiles=JSON.parse(await fs.readFile(path.join(project,'datasets/demo_profiles.json'),'utf8'));
const schema=JSON.parse(await fs.readFile(path.join(project,'datasets/profile_schema.json'),'utf8'));
const checks=[],errors=[];let posts=0,used=0;
const ok=(value,name)=>{assert(value,name);checks.push(name);};
const browser=await chromium.launch({headless:true,executablePath:path.join(root,'.local/ms-playwright/chromium-1248/chrome-win64/chrome.exe')});
try{
 const context=await browser.newContext();
 await context.route('**/*',async route=>{
  const url=new URL(route.request().url());
  if(url.hostname!=='policy-r9.local')return route.abort();
  if(route.request().method()!=='GET'){posts++;return route.abort();}
  if(url.pathname==='/ready')return route.fulfill({json:{status:'ready',live_enabled:true,runtime_revision:'source-verification-r9',generation_model:'gemini-3-flash-preview',generation_endpoint:'v1beta/generateContent',usage:{generation_cap:18,generation_attempts:used}}});
  if(url.pathname==='/api/v2/examples')return route.fulfill({json:{questions:[],profiles:profiles.profiles,schema}});
  if(url.pathname==='/api/v2/development')return route.fulfill({json:{rows:[]}});
  if(url.pathname==='/api/v2/summary')return route.fulfill({json:{}});
  return route.fulfill({path:path.join(project,'web/frontend/dist',url.pathname==='/'?'index.html':url.pathname.slice(1))});
 });
 const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
 await page.goto('http://policy-r9.local',{waitUntil:'networkidle'});
 ok(await page.getByText(/Cả hai nhánh dùng cùng tiêu chuẩn kiểm chứng nguồn/).isVisible(),'shared source standard is disclosed in the UI');
 await page.getByRole('button',{name:'Demo đủ 5 agent · Đi bộ & 58%',exact:true}).click();
 ok(await page.locator('input[type="checkbox"]').isChecked(),'full demo still enables Risk');
 ok(await page.getByRole('button',{name:/So sánh hai câu trả lời/}).isEnabled(),'new runtime version passes the UI guard');
 used=16;
 await page.reload({waitUntil:'networkidle'});
 ok(await page.getByRole('button',{name:/So sánh hai câu trả lời/}).isDisabled(),'three-generation quota guard remains effective');
 ok(posts===0&&errors.length===0,'no mutation/provider calls and no browser errors');
 await fs.mkdir(out,{recursive:true});
 const result={status:'PASS',checks,errors,API_calls:0,mutation_posts:posts};
 await fs.writeFile(path.join(out,'ui_verification.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));
}finally{await browser.close();}
