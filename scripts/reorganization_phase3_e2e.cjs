const {chromium,expect}=require('@playwright/test');
const fs=require('node:fs');const path=require('node:path');
const root=path.resolve(__dirname,'..'),out=path.join(root,'docs/reorganization/phase3');
const allProjects=['A01','A02','A03','A04','A05','A06','tieuluan1','tieuluan2','tieuluan3','agent01','agent02'];
const projects=process.env.ONLY_PROJECTS?allProjects.filter(p=>process.env.ONLY_PROJECTS.split(',').includes(p)):allProjects;
const previous=process.env.ONLY_PROJECTS?JSON.parse(fs.readFileSync(path.join(out,'e2e.json'),'utf8')):null;
const keep=row=>!projects.some(p=>row.name.startsWith(p+' '));
const report={checks:previous?previous.checks.filter(keep):[],failures:previous?previous.failures.filter(keep):[],training_steps:0,scientific_TEST_forward:0};
async function check(name,fn){try{await fn();report.checks.push({name,status:'PASS'});console.log('PASS',name);}catch(error){report.failures.push({name,message:error.message});console.log('FAIL',name,error.message.slice(0,600));}finally{fs.writeFileSync(path.join(out,'e2e.json'),JSON.stringify({...report,status:report.failures.length?'FAIL':'IN_PROGRESS'},null,2));}}
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||undefined});
try{for(const project of projects){const i=allProjects.indexOf(project);
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),base=`http://127.0.0.1:${8011+i}`;
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await check(project+' navigation and notebook links',async()=>{
  await page.goto(base);await expect(page.locator('h1')).toBeVisible();
  if(project.startsWith('A')){
   await page.waitForFunction(()=>window.ASSIGN_DATA?.tasks.length>0);
   const tasks=await page.evaluate(()=>window.ASSIGN_DATA.tasks);
   for(const task of tasks){await page.locator(`#datasets button[data-id="${task.id}"]`).click();await expect(page.locator('#task-title')).toHaveText(task.title);await expect(page.locator('#chart .barrow').first()).toBeVisible();
    for(const notebook of task.notebooks){const response=await page.request.get(base+'/'+notebook.href);expect(response.status()).toBe(200);const doc=await response.json();expect(doc.cells.length).toBeGreaterThan(1);}
   }
   await page.locator('#datasets button').first().click();
   if(['A01','A02','A03'].includes(project)){
    for(const task of tasks){await page.locator(`#datasets button[data-id="${task.id}"]`).click();await expect(page.locator('#predict')).toBeVisible();
     const response=page.waitForResponse(r=>r.url().endsWith(task.endpoint)&&r.request().method()==='POST');await page.locator('#predict').click();const r=await response;expect(r.status(),(await r.text()).slice(0,900)).toBe(200);await expect(page.locator('#status')).toContainText('Đã hoàn tất');
    }
    await page.locator('#input').fill('not json');await page.locator('#predict').click();await expect(page.locator('#status')).toContainText('Không thể xử lý');
   }
  }else if(project==='agent01'){
   for(let step=0;step<24;step++)await page.locator('#step').click();await expect(page.locator('#status')).toContainText('Đã đến đích');await page.locator('#reset').click();await page.locator('#manual').click();await page.locator('[data-action="0"]').click();await expect(page.locator('#status')).toContainText('Va tường');
   const r=await page.request.get(base+'/Discovering_AI_Agent.ipynb');expect(r.status()).toBe(200);expect((await r.json()).cells.length).toBeGreaterThan(5);
  }else if(project==='agent02'){
   for(let step=0;step<20;step++)await page.locator('#step').click();await expect(page.locator('#progress-label')).toContainText('20');
   for(const kernel of ['iid','persistent','gold']){await page.locator('#kernel').selectOption(kernel);expect((await page.locator('#comparison').innerText()).length).toBeGreaterThan(30);}
   await page.locator('details').nth(1).locator('summary').click();const count=await page.locator('#figure-select option').count();expect(count).toBe(20);
   for(let j=0;j<count;j++){await page.locator('#figure-select').selectOption({index:j});await expect(page.locator('#figure')).toBeVisible();await page.waitForFunction(()=>document.querySelector('#figure').complete&&document.querySelector('#figure').naturalWidth>0);}
   await page.locator('#q-form button').click();await expect(page.locator('#q-result')).not.toBeEmpty();
   const r=await page.request.get(base+'/AG02_Code_and_Results.ipynb');expect(r.status()).toBe(200);
  }else if(project==='tieuluan1'){
   await expect(page.getByText('4 mô hình sẵn sàng')).toBeVisible();
   for(const route of ['/ml','/cnn','/rnn']){await page.goto(base+route);await expect(page.locator('h1')).toBeVisible();await page.getByRole('button',{name:/Nạp.*mẫu/}).first().click();const response=page.waitForResponse(r=>r.url().includes('/api/predict/')&&r.request().method()==='POST');await page.getByRole('button',{name:/Chạy mô hình/}).first().click();expect((await response).status()).toBe(200);await expect(page.locator('.result-card').first()).toBeVisible({timeout:30000});}
  }else{
   await expect(page.getByText('API ready',{exact:true})).toBeVisible({timeout:30000});
   const chapters=project==='tieuluan2'?['/','/ml','/cnn','/rnn','/rag']:['/','/ml','/cnn','/rnn','/rag','/agents'];
   for(const route of chapters){await page.goto(base+route);await expect(page.locator('h1')).toBeVisible();}
   if(project==='tieuluan2'){expect(await page.locator('a[href^="/agents"]').count()).toBe(0);const r=await page.request.get(base+'/api/v3/chapters/6');expect(r.status()).toBe(404);}
   for(const [route,ds,family] of [['/ml','ch2_cdc_diabetes','mlp'],['/cnn','ch3_cifar10','cnn'],['/rnn','ch4_gold_pink_sheet','rnn'],['/rnn','ch4_gold_pink_sheet','lstm'],['/rag','ch5_finqa','kg_rag'],...(project==='tieuluan3'?[['/agents','ch6_house_tasks','multi_agent']]:[])]){
    await page.goto(base+`${route}?dataset=${ds}&family=${family}&section=run`);const button=page.getByRole('button',{name:/Chạy cả 3|Chạy B0|So sánh A0/});await expect(button).toBeEnabled({timeout:30000});await button.click();await expect(page.getByText('Job đã hoàn tất',{exact:false}).or(page.locator('.v3-result').first())).toBeVisible({timeout:45000});
   }
  }
 });
 await check(project+' mobile/assets/screenshot',async()=>{await page.goto(base);await page.screenshot({path:path.join(out,project+'-desktop.png'),fullPage:true});await page.setViewportSize({width:390,height:844});await page.reload();await expect(page.locator('h1')).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBeTruthy();await page.screenshot({path:path.join(out,project+'-mobile.png'),fullPage:true});expect(errors).toEqual([]);});
 await page.close();
}
}finally{await browser.close();report.status=report.failures.length?'FAIL':'PASS';fs.writeFileSync(path.join(out,'e2e.json'),JSON.stringify(report,null,2));}if(report.failures.length)process.exitCode=1;
})();
