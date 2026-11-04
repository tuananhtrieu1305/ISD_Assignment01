import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const root=process.cwd(),folder=path.join(root,'tieuluanfinal/artifacts/final_ch06');
const browser=await chromium.launch({headless:true,executablePath:path.join(root,'.local/ms-playwright/chromium-1248/chrome-win64/chrome.exe')});
try{
 const page=await browser.newPage({viewport:{width:1100,height:420},deviceScaleFactor:2});
 await page.goto(pathToFileURL(path.join(folder,'stage_latency.svg')).href);
 await page.locator('svg').screenshot({path:path.join(folder,'stage_latency.png')});
 console.log('Notebook SVG rendered as report PNG');
}finally{await browser.close();}
