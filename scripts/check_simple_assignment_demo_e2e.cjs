const { chromium } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

const base = process.env.DEMO_BASE_URL || 'http://127.0.0.1:8811';
const output = path.resolve(__dirname, '../artifacts/simple_demo_a01.png');
const browserCandidates = [
  process.env.CHROMIUM_PATH,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
].filter(Boolean);
const executablePath = browserCandidates.find((candidate) => fs.existsSync(candidate));

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1365, height: 900 } });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(base, { waitUntil: 'networkidle' });

  if (await page.locator('textarea').count()) throw new Error('Raw JSON textarea remains');
  if (await page.locator('#table-select, #metric-select').count()) throw new Error('Data explorer remains');
  const inputs = page.locator('#input-fields input, #input-fields select');
  if (await inputs.count() !== 6) throw new Error(`Expected 6 diabetes fields, got ${await inputs.count()}`);

  const response = page.waitForResponse((item) => item.url().endsWith('/api/diabetes/compare') && item.request().method() === 'POST');
  await page.locator('#submit').click();
  const apiResponse = await response;
  if (apiResponse.status() !== 200) throw new Error(`API returned ${apiResponse.status()}`);
  await page.locator('.result-card').first().waitFor({ state: 'visible' });
  const cardCount = await page.locator('.result-card').count();
  if (cardCount !== 5) throw new Error(`Expected 5 model cards, got ${cardCount}`);
  if (!await page.locator('.summary-card').isVisible()) throw new Error('Consensus summary missing');
  if (errors.length) throw new Error(`Browser errors: ${errors.join('; ')}`);

  await page.screenshot({ path: output, fullPage: true });
  const receipt = { status: 'PASS', base, inputs: 6, model_cards: cardCount, textarea: 0, data_explorer: 0, browser_errors: errors, screenshot: output };
  fs.writeFileSync(path.resolve(__dirname, '../artifacts/simple_demo_a01_e2e.json'), JSON.stringify(receipt, null, 2));
  console.log(JSON.stringify(receipt));
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
