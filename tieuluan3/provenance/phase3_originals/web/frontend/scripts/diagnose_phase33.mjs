import { chromium } from 'playwright';
const browser = await chromium.launch({ headless: true });
try {
 const page = await browser.newPage();
 page.on('console', message => { if (message.type() === 'error') console.log('browser_error', message.text()); });
 page.on('requestfailed', request => console.log('request_failed', new URL(request.url()).origin, request.failure()?.errorText));
 await page.goto('http://localhost:5173/cnn?section=run');
 console.log('native_fetch_probe', await page.evaluate(async () => {
  const result = {};
  try { result.direct = (await fetch('http://127.0.0.1:5000/health')).status; } catch (e) { result.direct = String(e); }
  try { const object = { fetcher: fetch }; result.method = (await object.fetcher('http://127.0.0.1:5000/health')).status; } catch (e) { result.method = String(e); }
  return result;
 }));
 await page.locator('[role=alert], [data-testid=model-runner]').first().waitFor({ timeout: 30000 });
 console.log('observed', await page.locator('[role=alert]').allTextContents());
} finally { await browser.close(); }
