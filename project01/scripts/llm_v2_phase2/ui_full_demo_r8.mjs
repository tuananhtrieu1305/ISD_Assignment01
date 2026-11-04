// Real built UI, intercepted local API, no provider request or running backend.
import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';

const root=path.resolve(import.meta.dirname,'../../..');
const project=path.join(root,'project01');
const out=path.join(project,'artifacts/llm_v2/phase2/development/full_demo_r8');
const fixture=JSON.parse(await fs.readFile(path.join(out,'offline_pipeline_fixture.json'),'utf8'));
const profiles=JSON.parse(await fs.readFile(path.join(project,'datasets/demo_profiles.json'),'utf8'));
const schema=JSON.parse(await fs.readFile(path.join(project,'datasets/profile_schema.json'),'utf8'));
const checks=[];
const ok=(value,name)=>{assert(value,name);checks.push(name);};
const browser=await chromium.launch({executablePath:path.join(root,'.local/ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
let comparisonPosts=0,submitted=null;
const errors=[];
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 await context.route('**/*',async route=>{
  const url=new URL(route.request().url());
  if(url.hostname!=='offline-r8.local')return route.abort();
  const pathname=url.pathname;
  if(pathname==='/ready')return route.fulfill({json:{status:'ready',live_enabled:true,generation_model:'gemini-3-flash-preview',generation_endpoint:'v1beta/generateContent',runtime_revision:'full-demo-r8',usage:{generation_attempts:0,generation_cap:18}}});
  if(pathname==='/api/v2/examples')return route.fulfill({json:{questions:[],profiles:profiles.profiles,schema}});
  if(pathname==='/api/v2/development')return route.fulfill({json:{rows:[]}});
  if(pathname==='/api/v2/summary')return route.fulfill({json:{}});
  if(pathname==='/api/v2/compare'){
   comparisonPosts++;submitted=route.request().postDataJSON();
   return route.fulfill({json:{id:'offline-r8-ui'}});
  }
  if(pathname==='/api/v2/jobs/offline-r8-ui')return route.fulfill({json:{...fixture,id:'offline-r8-ui',elapsed_seconds:0}});
  if(pathname.startsWith('/api/'))return route.abort();
  const target=path.join(project,'web/frontend/dist',pathname==='/'?'index.html':pathname.slice(1));
  return route.fulfill({path:target});
 });
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://offline-r8.local',{waitUntil:'networkidle'});
 await page.getByRole('button',{name:'Demo đủ 5 agent · Đi bộ & 58%',exact:true}).click();
 ok(await page.getByRole('textbox').inputValue()===fixture.question,'preset sets the selected short question');
 ok(await page.locator('input[type="checkbox"]').isChecked(),'preset enables Risk Agent');
 ok(await page.getByText(/Đã kèm hồ sơ CDC đủ 21 trường/).isVisible(),'selected profile is disclosed');
 ok(comparisonPosts===0,'selecting preset does not start an API job');
 await page.getByRole('button',{name:/So sánh hai câu trả lời/}).click();
 await page.getByText(/Kết quả công cụ CDC: score 0.395520/).first().waitFor();
 ok(submitted.mode==='combined'&&Object.keys(submitted.profile).length===21,'local job receives the complete CDC profile');
 ok(submitted.question===fixture.question&&comparisonPosts===1,'one click starts exactly one local comparison job');
 await page.getByRole('button',{name:/03.*Luồng xử lý/}).click();
 ok(await page.locator('.pipeline-map a').count()===7,'all seven stages are visible');
 ok(await page.locator('.pipeline-map .skipped').count()===0,'Risk stage is not marked skipped');
 ok(await page.locator('#pipeline-risk').getByText('Hoàn tất',{exact:true}).isVisible(),'Risk completion is rendered');
 ok(await page.locator('#pipeline-reporter pre').textContent().then(text=>text.includes('risk_tool_summary')),'Reporter shows that it consumes the Risk result');
 await page.locator('#pipeline-reporter summary').click();
 ok(await page.locator('#pipeline-reporter').getByText(/Nguồn mô tả giảm nguy cơ 58%/).isVisible(),'Reporter claim text is rendered from text_vi');
 await page.screenshot({path:path.join(out,'offline-full-pipeline-ui.png'),fullPage:true});
 await page.locator('#pipeline-risk').screenshot({path:path.join(out,'offline-risk-output.png')});
 await page.locator('#pipeline-reporter').screenshot({path:path.join(out,'offline-reporter-output.png')});
 await page.setViewportSize({width:390,height:844});
 ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'pipeline fits a narrow mobile viewport');
 ok(errors.length===0,'no JavaScript errors');
 const receipt={status:'PASS',checks,errors,intercepted_local_comparison_posts:comparisonPosts,new_generation_API_calls:0,new_embedding_API_calls:0,fixture:'offline engineering test; not live Gemini quality evidence'};
 await fs.writeFile(path.join(out,'ui_verification.json'),JSON.stringify(receipt,null,2));
 console.log(JSON.stringify(receipt));
}finally{await browser.close();}
