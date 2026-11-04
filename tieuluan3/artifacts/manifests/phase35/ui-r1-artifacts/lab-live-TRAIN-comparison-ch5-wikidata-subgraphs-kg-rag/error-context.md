# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: lab.spec.ts >> live TRAIN comparison ch5_wikidata_subgraphs/kg_rag
- Location: tests\v3\lab.spec.ts:89:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByTestId('model-runner')
Expected: visible
Timeout: 25000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByTestId('model-runner') with timeout 25000ms
  - waiting for getByTestId('model-runner')

```

```yaml
- link "Đến nội dung chính":
  - /url: "#lab-content"
- banner:
  - link "Model Lab — Tổng quan":
    - /url: /
    - text: TIỂU LUẬN TRÍ TUỆ NHÂN TẠO
    - strong: Model Lab/ 03
  - status: API ready
- navigation "Điều hướng chính":
  - link "Tổng quan":
    - /url: /
  - link "ML":
    - /url: /ml
  - link "CNN":
    - /url: /cnn
  - link "RNN–LSTM":
    - /url: /rnn
  - link "KG–RAG":
    - /url: /rag
  - link "Multi-Agent":
    - /url: /agents
- main:
  - paragraph: CHƯƠNG 05 / PHÒNG THÍ NGHIỆM TƯƠNG TÁC
  - heading "Tri thức có nguồn dẫn" [level=1]
  - paragraph: Tìm bằng chứng trước, trả lời sau. B0–B4 kết hợp truy hồi và liên kết đồ thị trên snapshot đã khóa; không gọi LLM hay API bên ngoài.
  - text: 3 dataset / chương Checkpoint đã khóa Không train trên web
  - navigation "Chọn dataset":
    - link "01 Y khoa · MedQuAD":
      - /url: /rag?dataset=ch5_medquad_diabetes&family=kg_rag&section=run
    - link "02 Tài chính · FinQA":
      - /url: /rag?dataset=ch5_finqa&family=kg_rag&section=run
    - link "03 Đồ thị · Wikidata":
      - /url: /rag?dataset=ch5_wikidata_subgraphs&family=kg_rag&section=run
  - heading "Đồ thị · Wikidata" [level=2]
  - navigation "Nội dung dataset":
    - link "Dữ liệu":
      - /url: /rag?dataset=ch5_wikidata_subgraphs&family=kg_rag&section=data
    - link "Hợp hàm & lý thuyết":
      - /url: /rag?dataset=ch5_wikidata_subgraphs&family=kg_rag&section=theory
    - link "Chạy so sánh":
      - /url: /rag?dataset=ch5_wikidata_subgraphs&family=kg_rag&section=run
    - link "Kết quả đã lưu":
      - /url: /rag?dataset=ch5_wikidata_subgraphs&family=kg_rag&section=results
    - link "Triển khai":
      - /url: /rag?dataset=ch5_wikidata_subgraphs&family=kg_rag&section=deployment
  - status: Đang đọc artifact đã khóa…
  - strong: Học thuật, không lời khuyên chuyên môn.
  - paragraph: Không nhập bệnh án hoặc secret. Dự đoán trên snapshot không dùng để chẩn đoán, định giá hiện tại hay đầu tư. TEST đã niêm phong không được chạy lại từ giao diện.
- contentinfo: MODEL LAB / AI TERM PAPER V3 React UI · Python API · provenance first
```

# Test source

```ts
  1   | import { expect, test, type Page } from "@playwright/test";
  2   | import AxeBuilder from "@axe-core/playwright";
  3   | import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
  4   | import { createHash } from "node:crypto";
  5   | import { chapters } from "../../src/v3/catalog";
  6   | import type { Job } from "../../src/v3/types";
  7   | const base = "../../artifacts/manifests/phase33";
  8   | const evidence = process.env.PHASE33_EVIDENCE ?? "development-e2e";
  9   | const shots = `${base}/${evidence}-screenshots`;
  10  | mkdirSync(shots, { recursive: true });
  11  | const reference = JSON.parse(
  12  |   readFileSync("../../artifacts/manifests/phase32/http_cpu_v2.json", "utf8"),
  13  | );
  14  | const checksName = process.env.PHASE33_CHECKS;
  15  | if (checksName && !/^[a-z0-9_-]+$/.test(checksName))
  16  |   throw new Error("Invalid checks receipt");
  17  | const checksPath = checksName ? `${base}/${checksName}_checks.json` : null;
  18  | const checks = checksPath ? JSON.parse(readFileSync(checksPath, "utf8")) : null;
  19  | test.beforeAll(async ({ request }) => {
  20  |   if (!checks) return;
  21  |   for (const row of checks.source)
  22  |     expect(
  23  |       createHash("sha256")
  24  |         .update(readFileSync(`../../${row.path}`))
  25  |         .digest("hex"),
  26  |     ).toBe(row.sha256);
  27  |   const served = [];
  28  |   for (const row of checks.build_outputs) {
  29  |     const name = row.path.split(`/web-preview-${checksName}/`)[1];
  30  |     const response = await request.get(`/${name}`);
  31  |     expect(response.ok()).toBeTruthy();
  32  |     expect(
  33  |       createHash("sha256")
  34  |         .update(await response.body())
  35  |         .digest("hex"),
  36  |     ).toBe(row.sha256);
  37  |     served.push({ path: name, sha256: row.sha256 });
  38  |   }
  39  |   writeFileSync(
  40  |     `${base}/${evidence}-served_build.json`,
  41  |     JSON.stringify(
  42  |       {
  43  |         status: "PASS",
  44  |         source_sha256: checks.source_sha256,
  45  |         checks_sha256: createHash("sha256")
  46  |           .update(readFileSync(checksPath!))
  47  |           .digest("hex"),
  48  |         served,
  49  |         model_inference_executed: false,
  50  |       },
  51  |       null,
  52  |       2,
  53  |     ),
  54  |     { flag: "wx" },
  55  |   );
  56  | });
  57  | 
  58  | class LabPage {
  59  |   constructor(readonly page: Page) {}
  60  |   async open(route: string) {
  61  |     await this.page.goto(route);
> 62  |     await expect(this.page.getByTestId("model-runner")).toBeVisible();
      |                                                         ^ Error: expect(locator).toBeVisible() failed
  63  |   }
  64  |   async run(count: number) {
  65  |     let job: Job | null = null;
  66  |     this.page.on("response", async (response) => {
  67  |       if (
  68  |         /\/api\/v3\/jobs\/job_[a-f0-9]+$/.test(response.url()) &&
  69  |         response.ok()
  70  |       )
  71  |         job = await response.json();
  72  |     });
  73  |     await this.page
  74  |       .getByRole("button", { name: /Chạy cả 3 mô hình|Chạy B0–B4|So sánh A0/ })
  75  |       .click();
  76  |     await expect
  77  |       .poll(() => job?.status, { timeout: 95_000 })
  78  |       .toMatch(/succeeded|failed|partial/);
  79  |     await expect(this.page.getByTestId("model-result")).toHaveCount(count);
  80  |     return job! as Job;
  81  |   }
  82  | }
  83  | 
  84  | for (const chapter of chapters.filter((c) => c.chapter > 1)) {
  85  |   for (const dataset of chapter.datasets) {
  86  |     for (const family of chapter.chapter === 4
  87  |       ? ["rnn", "lstm"]
  88  |       : [chapter.family]) {
  89  |       test(`live TRAIN comparison ${dataset}/${family}`, async ({ page }) => {
  90  |         const errors: string[] = [];
  91  |         page.on("pageerror", (error) => errors.push(error.message));
  92  |         const lab = new LabPage(page);
  93  |         await lab.open(
  94  |           `${chapter.route}?dataset=${dataset}&family=${family}&section=run`,
  95  |         );
  96  |         const job = await lab.run(chapter.chapter === 5 ? 5 : 3);
  97  |         const old = reference.results.find(
  98  |           (row: { dataset_id: string; family: string }) =>
  99  |             row.dataset_id === dataset && row.family === family,
  100 |         );
  101 |         expect(job.results.map((row) => row.implementation)).toEqual(
  102 |           old.job.results.map(
  103 |             (row: { implementation: string }) => row.implementation,
  104 |           ),
  105 |         );
  106 |         if (dataset.includes("wikidata")) {
  107 |           expect(
  108 |             job.results.every((row) => row.status === "unavailable"),
  109 |           ).toBeTruthy();
  110 |           await expect(
  111 |             page.getByText("Wikidata · structural browser, không QA benchmark"),
  112 |           ).toBeVisible();
  113 |         } else {
  114 |           expect(job.status).toBe("succeeded");
  115 |           expect(
  116 |             job.results.every(
  117 |               (row) =>
  118 |                 row.actual_backend === "numpy" && row.actual_device === "cpu",
  119 |             ),
  120 |           ).toBeTruthy();
  121 |         }
  122 |         if (chapter.chapter < 5)
  123 |           job.results.forEach((slot, n) => {
  124 |             expect(slot.artifact_sha256).toBe(
  125 |               old.job.results[n].artifact_sha256,
  126 |             );
  127 |             expect(slot.prediction).toEqual(old.job.results[n].prediction);
  128 |           });
  129 |         if (chapter.chapter === 6)
  130 |           await expect(page.getByTestId("agent-trace")).toBeVisible();
  131 |         expect(errors).toEqual([]);
  132 |         writeFileSync(
  133 |           `${base}/${evidence}-${dataset}-${family}.json`,
  134 |           JSON.stringify(
  135 |             {
  136 |               scope: "TRAIN-only UI serving smoke; not historical TEST",
  137 |               job,
  138 |               input_split: old.input_split,
  139 |               models_retrained: 0,
  140 |               source_sha256: checks?.source_sha256 ?? null,
  141 |               historical_test_evaluation_executed: false,
  142 |             },
  143 |             null,
  144 |             2,
  145 |           ),
  146 |           { flag: "wx" },
  147 |         );
  148 |         if (
  149 |           [
  150 |             "ch3_idrid",
  151 |             "ch4_gold_pink_sheet",
  152 |             "ch5_medquad_diabetes",
  153 |             "ch6_diabetes_tasks",
  154 |           ].includes(dataset)
  155 |         ) {
  156 |           await page.screenshot({
  157 |             path: `${shots}/${dataset}-${family}.png`,
  158 |             fullPage: true,
  159 |           });
  160 |         }
  161 |       });
  162 |     }
```