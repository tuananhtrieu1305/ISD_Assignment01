import { chromium } from "../apps/web/node_modules/@playwright/test/index.mjs";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { createHash } from "node:crypto";

const base = fileURLToPath(new URL("./", import.meta.url));
const browser = await chromium.launch({headless:true,args:["--disable-lcd-text","--force-color-profile=srgb"]});
try {
  const context = await browser.newContext({viewport:{width:1100,height:1000},deviceScaleFactor:2});
  const page = await context.newPage();
  await page.route(/^https?:/, route => route.abort());
  await page.goto(pathToFileURL(path.join(base,"evidence/notebook_browser/executed_notebook.html")).href);
  await page.evaluate(() => document.fonts.ready);
  const cells = page.locator(".code_cell");
  if (await cells.count() !== 9) throw new Error("Unexpected notebook cell count");
  const destination = path.join(base,"screenshots");
  mkdirSync(destination,{recursive:true});
  const receipt = [];
  for(let index=0;index<9;index++) {
    const cell = cells.nth(index);
    const colors = await cell.evaluate(element => [...element.querySelectorAll("pre,span,a")]
      .map(node=>getComputedStyle(node).color));
    if(colors.some(color=>color!=="rgb(0, 0, 0)")) throw new Error("Nonblack notebook text");
    const filename = `cell-${String(index+1).padStart(2,"0")}.png`;
    const target = path.join(destination,filename);
    await cell.screenshot({path:target,animations:"disabled"});
    const box = await cell.boundingBox();
    receipt.push({cell:index+1,path:`screenshots/${filename}`,width:box.width,height:box.height,
      sha256:createHash("sha256").update(readFileSync(target)).digest("hex"),
      capture:"Chromium screenshot of HTML exported from actual executed notebook",
      text_color:"#000000"});
  }
  writeFileSync(path.join(base,"evidence/screenshot_manifest.json"),JSON.stringify(receipt,null,2)+"\n");
  console.log(JSON.stringify(receipt));
} finally { await browser.close(); }
