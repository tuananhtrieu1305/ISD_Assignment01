import { expect, test } from "../../apps/web/node_modules/@playwright/test/index.mjs";
import { readFileSync } from "node:fs";

const reference = JSON.parse(readFileSync(new URL("../../artifacts/manifests/phase32/http_cpu_v2.json", import.meta.url), "utf8"));
const cases = [
  ["/ml", "ch2_cdc_diabetes", "mlp", 3],
  ["/cnn", "ch3_idrid", "cnn", 3],
  ["/rnn", "ch4_gold_pink_sheet", "rnn", 3],
  ["/rnn", "ch4_gold_pink_sheet", "lstm", 3],
  ["/rag", "ch5_finqa", "kg_rag", 5],
  ["/agents", "ch6_gold_tasks", "multi_agent", 3],
];

for (const [route, dataset, family, count] of cases) {
  test(`CPU-only Render runtime ${dataset}/${family}`, async ({ page }) => {
    let completed;
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    page.on("response", async response => {
      if (/\/api\/v3\/jobs\/job_[a-f0-9]+$/.test(response.url()) && response.ok()) {
        const job = await response.json();
        if (["succeeded", "failed", "partial"].includes(job.status)) completed = job;
      }
    });
    await page.goto(`${route}?dataset=${dataset}&family=${family}&section=run`);
    await expect(page.getByTestId("model-runner")).toBeVisible();
    await page.getByRole("button", { name: /Chạy cả 3 mô hình|Chạy B0–B4|So sánh A0/ }).click();
    await expect.poll(() => completed?.status, { timeout: 95_000 }).toBe("succeeded");
    await expect(page.getByTestId("model-result")).toHaveCount(count);
    expect(completed.results.every(slot => slot.actual_backend === "numpy" && slot.actual_device === "cpu")).toBeTruthy();
    const old = reference.results.find(row => row.dataset_id === dataset && row.family === family);
    expect(completed.results.map(slot => slot.implementation)).toEqual(old.job.results.map(slot => slot.implementation));
    if (["mlp", "cnn", "rnn", "lstm"].includes(family)) {
      completed.results.forEach((slot, index) => {
        expect(slot.artifact_sha256).toBe(old.job.results[index].artifact_sha256);
        expect(slot.prediction).toEqual(old.job.results[index].prediction);
      });
    }
    if (family === "multi_agent") await expect(page.getByTestId("agent-trace")).toBeVisible();
    expect(errors).toEqual([]);
  });
}

test("deep-link refresh keeps LSTM selection", async ({ page }) => {
  await page.goto("/rnn?dataset=ch4_gold_pink_sheet&family=lstm&section=theory");
  await expect(page.getByTestId("function-composition")).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "LSTM", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("function-composition")).toBeVisible();
});

test("HTTP readiness and exact-origin CORS", async ({ request }) => {
  const ready = await request.get("http://127.0.0.1:5000/ready");
  expect(ready.status()).toBe(200);
  const good = await request.get("http://127.0.0.1:5000/api/v3/chapters", { headers: { Origin: "https://isd-assignment01-web.onrender.com" } });
  expect(good.status()).toBe(200);
  expect(good.headers()["access-control-allow-origin"]).toBe("https://isd-assignment01-web.onrender.com");
  const bad = await request.get("http://127.0.0.1:5000/api/v3/chapters", { headers: { Origin: "https://untrusted.invalid" } });
  expect(bad.status()).toBe(403);
});
