/** Local, dependency-free browser smoke for the Phase 16 KG-RAG page. */

import { spawn } from "node:child_process";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const browserPath = process.env.BROWSER_PATH;
if (!browserPath) throw new Error("Set BROWSER_PATH to a Chromium-compatible browser executable.");

const root = path.resolve(import.meta.dirname, "../../..");
const outputDirectory = path.join(root, "artifacts/e2e/ch5");
const assetDirectory = path.join(root, "report/assets/ch5_knowledge_rag");
const screenshotPath = path.join(assetDirectory, "phase16_agent_medical.png");
const reportPath = path.join(outputDirectory, "phase16_e2e.json");
const profilePath = await mkdtemp(path.join(os.tmpdir(), "phase16-edge-"));
await mkdir(outputDirectory, { recursive: true });
await mkdir(assetDirectory, { recursive: true });

const browser = spawn(
  browserPath,
  [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "--hide-scrollbars",
    "--remote-debugging-port=9222",
    `--user-data-dir=${profilePath}`,
    "--window-size=1440,1200",
    "http://127.0.0.1:5173/rag",
  ],
  { stdio: "ignore", windowsHide: true },
);

const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function browserTab() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const tabs = await fetch("http://127.0.0.1:9222/json/list").then((response) => response.json());
      const page = tabs.find((item) => item.type === "page" && item.url.includes("127.0.0.1:5173"));
      if (page) return page;
    } catch {
      // Browser startup is intentionally polled with a bounded deadline.
    }
    await delay(100);
  }
  throw new Error("Headless browser did not expose the local UI within 6 seconds.");
}

const tab = await browserTab();
const socket = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});

let nextId = 0;
const pending = new Map();
socket.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (!message.id || !pending.has(message.id)) return;
  const { resolve, reject } = pending.get(message.id);
  pending.delete(message.id);
  if (message.error) reject(new Error(message.error.message));
  else resolve(message.result);
});

function cdp(method, params = {}) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const result = await cdp("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

let report;
try {
  await cdp("Page.enable");
  await cdp("Runtime.enable");
  for (let attempt = 0; attempt < 60; attempt += 1) {
    if (await evaluate("document.querySelector('#rag-question') !== null")) break;
    await delay(100);
  }
  await evaluate(`(() => {
    const textarea = document.querySelector('#rag-question');
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(textarea, 'What are common complications of diabetes?');
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    document.querySelector('.rag-query-panel').requestSubmit();
    return true;
  })()`);

  let completed = false;
  for (let attempt = 0; attempt < 200; attempt += 1) {
    completed = await evaluate("document.querySelector('.rag-answer') !== null");
    if (completed) break;
    await delay(100);
  }
  if (!completed) throw new Error("Agent result was not rendered within 20 seconds.");

  const assertions = await evaluate(`(() => ({
    title: document.querySelector('.rag-hero h1')?.textContent?.trim(),
    domain: document.querySelector('.domain-badge')?.textContent?.trim(),
    tool: [...document.querySelectorAll('.rag-result-meta span')][1]?.textContent?.trim(),
    citationCount: document.querySelectorAll('.citation-list code').length,
    evidenceCount: document.querySelectorAll('.evidence-stack details').length,
    graphNodes: document.querySelectorAll('.graph-trace li').length,
    abstained: document.querySelector('.rag-answer')?.classList.contains('abstained'),
    artifactVersion: document.querySelector('.rag-result-footer code')?.textContent?.trim(),
  }))()`);
  const passed =
    assertions.domain === "medical" &&
    assertions.tool === "medical_retriever" &&
    assertions.citationCount > 0 &&
    assertions.evidenceCount > 0 &&
    assertions.graphNodes > 0 &&
    assertions.abstained === false &&
    assertions.artifactVersion?.startsWith("phase16-b4-");
  if (!passed) throw new Error(`UI assertions failed: ${JSON.stringify(assertions)}`);

  const screenshot = await cdp("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
  });
  await writeFile(screenshotPath, Buffer.from(screenshot.data, "base64"));
  report = {
    phase: 16,
    status: "PASS",
    url: "http://127.0.0.1:5173/rag",
    viewport: { width: 1440, height: 1200 },
    assertions,
    screenshot: path.relative(root, screenshotPath).replaceAll("\\", "/"),
  };
} finally {
  socket.close();
  browser.kill();
  await delay(250);
  await rm(profilePath, { recursive: true, force: true });
}

await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(JSON.stringify(report, null, 2));
