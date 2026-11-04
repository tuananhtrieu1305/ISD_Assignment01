// Raster fallback for the original, hash-locked SVG. No network and no source edits.
import {chromium} from '../apps/web/node_modules/playwright-core/index.mjs';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));
const source='report/assets/ch1/ai_history_timeline.svg';
const svg=readFileSync(path.join(root,source));
const sha=createHash('sha256').update(svg).digest('hex');
const lock=JSON.parse(readFileSync(path.join(root,'artifacts/manifests/phase34/experiment_lock.json'),'utf8'));
const record=lock.files.find(row=>row.path===source);
if(!record || record.sha256!==sha) throw new Error('Original SVG is not hash-locked');
const text=svg.toString('utf8');
if(!text.startsWith('<svg ') || /<(script|foreignObject)|\bhref\s*=|\bon\w+\s*=/i.test(text)) throw new Error('Unsupported SVG surface');
const target=path.join(root,'report/phase35/assets/ai_history_timeline_chromium.png');
const receipt=path.join(root,'artifacts/manifests/phase35/timeline_browser_render.json');
if(existsSync(target)||existsSync(receipt)) throw new Error('Refusing to overwrite render evidence');
mkdirSync(path.dirname(target),{recursive:true});
const browser=await chromium.launch({headless:true});
let version;
try {
 version=browser.version();
 const page=await browser.newPage({viewport:{width:1600,height:1050},deviceScaleFactor:2});
 await page.route('**/*',route=>route.abort());
 await page.setContent('<!doctype html><html><head><style>html,body{margin:0;padding:0;background:white}</style></head><body>'+text+'</body></html>');
 await page.evaluate(()=>document.fonts.ready);
 const font=await page.locator('text.event').first().evaluate(node=>getComputedStyle(node).fontFamily);
 if(!font.includes('Times New Roman')) throw new Error('Font family mismatch');
 await page.locator('svg').screenshot({path:target});
 writeFileSync(receipt,JSON.stringify({status:'PASS',source,source_sha256:sha,output:path.relative(root,target).replaceAll('\\','/'),output_sha256:createHash('sha256').update(readFileSync(target)).digest('hex'),browser_version:version,font_family:font,network_requests_allowed:false,device_scale_factor:2,source_modified:false},null,2)+'\n',{flag:'wx'});
} finally {await browser.close();}
console.log(JSON.stringify({status:'PASS',target,browser:version}));
