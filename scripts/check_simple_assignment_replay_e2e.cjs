const { chromium } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

const offline = process.env.DEMO_OFFLINE === '1';
const base = process.env.DEMO_BASE_URL || (offline ? 'http://demo.local' : undefined);
const project = process.env.DEMO_PROJECT;
const minimumCards = Number(process.env.MINIMUM_CARDS || 2);
if (!base || !project) throw new Error('DEMO_BASE_URL and DEMO_PROJECT are required');

const browserCandidates = [
  process.env.CHROMIUM_PATH,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
].filter(Boolean);
const executablePath = browserCandidates.find((candidate) => fs.existsSync(candidate));

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath });
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  if (offline) {
    // Exercise the real replay UI without WSL or a backend/model process.
    // Only /health is stubbed; all HTML/JS/CSS/data come from the current files.
    await context.route('http://demo.local/**', async (route) => {
      const pathname = new URL(route.request().url()).pathname;
      if (pathname === '/health') return route.fulfill({ json: { status: 'ok', mode: 'saved_results' } });
      const root = path.resolve(__dirname, '..');
      const relative = pathname.startsWith('/_demo-ui/')
        ? `_shared/simple_demo/${pathname.split('/').pop()}`
        : `${project}/web/${pathname === '/' ? 'index.html' : pathname.slice(1)}`;
      const file = path.resolve(root, relative);
      if (!file.startsWith(root + path.sep) || !fs.existsSync(file)) return route.fulfill({ status: 404 });
      return route.fulfill({ path: file });
    });
  }
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(base, { waitUntil: 'networkidle' });

  if (await page.locator('textarea').count()) throw new Error('Raw JSON textarea remains');
  if (await page.locator('#table-select, #metric-select').count()) throw new Error('Data explorer remains');
  await page.locator('#submit').click();
  await page.locator('.result-card').first().waitFor({ state: 'visible' });
  const cardCount = await page.locator('.result-card').count();
  if (cardCount < minimumCards) throw new Error(`Expected at least ${minimumCards} cards, got ${cardCount}`);
  const mode = (await page.locator('#mode-pill').textContent()).trim();
  if (mode !== 'Kết quả đã lưu') throw new Error(`Replay disclosure missing: ${mode}`);
  if (errors.length) throw new Error(`Browser errors: ${errors.join('; ')}`);

  const mobile = await context.newPage();
  await mobile.setViewportSize({ width: 390, height: 844 });
  await mobile.goto(base, { waitUntil: 'networkidle' });
  const overflow = await mobile.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  if (overflow > 1) throw new Error(`Mobile horizontal overflow: ${overflow}px`);

  const output = path.resolve(__dirname, `../artifacts/simple_demo_${project.toLowerCase()}.png`);
  await page.screenshot({ path: output, fullPage: true });
  const tasks = [];
  const tabs = page.locator('#datasets button');
  for (let index = 0; index < await tabs.count(); index += 1) {
    await tabs.nth(index).click();
    await page.locator('#submit').click();
    const cards = await page.locator('.result-card').count();
    if (cards < 2) throw new Error(`No comparison for task ${index}: ${cards} cards`);
    const text = await page.locator('#results').textContent();
    if (/undefined|NaN/.test(text)) throw new Error(`Invalid output for task ${index}`);
    const sample = page.locator('[name="sample"]');
    if (await sample.count() && await sample.locator('option').count() > 1) {
      await sample.selectOption({ index: 1 });
      await page.locator('#submit').click();
      if (await page.locator('.result-card').count() < 2) throw new Error(`Second sample failed: ${index}`);
    }
    tasks.push({ title: await tabs.nth(index).textContent(), cards });
  }
  if (errors.length) throw new Error(`Browser errors: ${errors.join('; ')}`);
  const receipt = { status: 'PASS', project, base, offline_browser_only: offline, model_cards: cardCount, tasks, mode, mobile_overflow_px: overflow, browser_errors: errors, screenshot: output };
  fs.writeFileSync(path.resolve(__dirname, `../artifacts/simple_demo_${project.toLowerCase()}_e2e.json`), JSON.stringify(receipt, null, 2));
  console.log(JSON.stringify(receipt));
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
