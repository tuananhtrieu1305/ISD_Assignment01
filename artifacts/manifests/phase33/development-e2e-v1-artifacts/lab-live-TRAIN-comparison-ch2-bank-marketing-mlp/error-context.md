# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: lab.spec.ts >> live TRAIN comparison ch2_bank_marketing/mlp
- Location: tests\v3\lab.spec.ts:28:7

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
  - status: API chưa kết nối
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
  - paragraph: CHƯƠNG02 / PHÒNG THÍ NGHIỆM TƯƠNG TÁC
  - heading "Machine Learning" [level=1]
  - paragraph: Biến một bảng đặc trưng thành dự đoán. MLP học các tổ hợp từ đơn giản đến phức tạp; mô hình cổ điển là đối chứng trong kết quả đã lưu.
  - text: 3dataset / chương Checkpoint đã khóa Không train trên web
  - navigation "Chọn dataset":
    - link "01 Tiểu đường · CDC":
      - /url: /ml?dataset=ch2_cdc_diabetes&family=mlp&section=run
    - link "02 Giá nhà · Ames":
      - /url: /ml?dataset=ch2_ames_housing&family=mlp&section=run
    - link "03 Tiếp thị · Bank":
      - /url: /ml?dataset=ch2_bank_marketing&family=mlp&section=run
  - heading "Tiếp thị · Bank" [level=2]
  - navigation "Nội dung dataset":
    - link "Dữ liệu":
      - /url: /ml?dataset=ch2_bank_marketing&family=mlp&section=data
    - link "Hợp hàm & lý thuyết":
      - /url: /ml?dataset=ch2_bank_marketing&family=mlp&section=theory
    - link "Chạy so sánh":
      - /url: /ml?dataset=ch2_bank_marketing&family=mlp&section=run
    - link "Kết quả đã lưu":
      - /url: /ml?dataset=ch2_bank_marketing&family=mlp&section=results
    - link "Triển khai":
      - /url: /ml?dataset=ch2_bank_marketing&family=mlp&section=deployment
  - alert:
    - strong: Chưa thể tải nội dung
    - paragraph: Không thể xử lý yêu cầu (network_error).
    - button "Thử lại"
  - strong: Học thuật, không lời khuyên chuyên môn.
  - paragraph: Không nhập bệnh án hoặc secret. Dự đoán trên snapshot không dùng để chẩn đoán, định giá hiện tại hay đầu tư. TEST đã niêm phong không được chạy lại từ giao diện.
- contentinfo: MODEL LAB / AI TERM PAPER V3 React UI · Python API · provenance first
```

# Test source

```ts
  1  | import { expect, test, type Page } from '@playwright/test';
  2  | import AxeBuilder from '@axe-core/playwright';
  3  | import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
  4  | import { chapters } from '../../src/v3/catalog';
  5  | import type { Job } from '../../src/v3/types';
  6  | const base = '../../artifacts/manifests/phase33';
  7  | const evidence = process.env.PHASE33_EVIDENCE ?? 'development-e2e';
  8  | const shots = `${base}/${evidence}-screenshots`;
  9  | mkdirSync(shots, { recursive: true });
  10 | const reference = JSON.parse(readFileSync('../../artifacts/manifests/phase32/http_cpu_v2.json', 'utf8'));
  11 | 
  12 | class LabPage {
  13 |   constructor(readonly page: Page) {}
> 14 |   async open(route: string) { await this.page.goto(route); await expect(this.page.getByTestId('model-runner')).toBeVisible(); }
     |                                                                                                                ^ Error: expect(locator).toBeVisible() failed
  15 |   async run(count: number) {
  16 |     let job: Job | null = null;
  17 |     this.page.on('response', async response => { if (/\/api\/v3\/jobs\/job_[a-f0-9]+$/.test(response.url()) && response.ok()) job = await response.json(); });
  18 |     await this.page.getByRole('button', { name: /Chạy cả 3 mô hình|Chạy B0–B4|So sánh A0/ }).click();
  19 |     await expect.poll(() => job?.status, { timeout: 95_000 }).toMatch(/succeeded|failed|partial/);
  20 |     await expect(this.page.getByTestId('model-result')).toHaveCount(count);
  21 |     return job! as Job;
  22 |   }
  23 | }
  24 | 
  25 | for (const chapter of chapters.filter(c => c.chapter > 1)) {
  26 |   for (const dataset of chapter.datasets) {
  27 |     for (const family of chapter.chapter === 4 ? ['rnn', 'lstm'] : [chapter.family]) {
  28 |       test(`live TRAIN comparison ${dataset}/${family}`, async ({ page }) => {
  29 |         const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
  30 |         const lab = new LabPage(page); await lab.open(`${chapter.route}?dataset=${dataset}&family=${family}&section=run`);
  31 |         const job = await lab.run(chapter.chapter === 5 ? 5 : 3);
  32 |         const old = reference.results.find((row: { dataset_id: string; family: string }) => row.dataset_id === dataset && row.family === family);
  33 |         expect(job.results.map(row => row.implementation)).toEqual(old.job.results.map((row: { implementation: string }) => row.implementation));
  34 |         if (dataset.includes('wikidata')) { expect(job.results.every(row => row.status === 'unavailable')).toBeTruthy(); await expect(page.getByText('Wikidata · structural browser, không QA benchmark')).toBeVisible(); }
  35 |         else { expect(job.status).toBe('succeeded'); expect(job.results.every(row => row.actual_backend === 'numpy' && row.actual_device === 'cpu')).toBeTruthy(); }
  36 |         if (chapter.chapter < 5) job.results.forEach((slot, n) => { expect(slot.artifact_sha256).toBe(old.job.results[n].artifact_sha256); expect(slot.prediction).toEqual(old.job.results[n].prediction); });
  37 |         if (chapter.chapter === 6) await expect(page.getByTestId('agent-trace')).toBeVisible();
  38 |         expect(errors).toEqual([]);
  39 |         writeFileSync(`${base}/${evidence}-${dataset}-${family}.json`, JSON.stringify({ scope: 'TRAIN-only UI serving smoke; not historical TEST', job, input_split: old.input_split, models_retrained: 0 }, null, 2), { flag: 'wx' });
  40 |         if (['ch3_idrid', 'ch4_gold_pink_sheet', 'ch5_medquad_diabetes', 'ch6_diabetes_tasks'].includes(dataset)) {
  41 |           await page.screenshot({ path: `${shots}/${dataset}-${family}.png`, fullPage: true });
  42 |         }
  43 |       });
  44 |     }
  45 |   }
  46 | }
  47 | 
  48 | test('deep link, back/forward, RNN toggle and refresh keep selections', async ({ page }) => {
  49 |   await page.goto('/rnn?dataset=ch4_bis_house_prices&family=lstm&section=theory');
  50 |   await expect(page.getByTestId('function-composition')).toBeVisible();
  51 |   await expect(page.getByRole('button', { name: 'LSTM', exact: true })).toHaveAttribute('aria-pressed', 'true');
  52 |   await page.reload(); await expect(page.getByTestId('function-composition')).toBeVisible();
  53 |   await page.getByRole('button', { name: 'RNN', exact: true }).click(); await expect(page).toHaveURL(/family=rnn/);
  54 |   await page.goBack(); await expect(page).toHaveURL(/family=lstm/);
  55 |   await page.goForward(); await expect(page).toHaveURL(/family=rnn/);
  56 | });
  57 | test('all18dataset cards, function contracts, historical panels and deployment load', async ({ page }) => {
  58 |   for (const chapter of chapters) for (const dataset of chapter.datasets) {
  59 |     await page.goto(`${chapter.route}?dataset=${dataset}&family=${chapter.family}&section=data`);
  60 |     await expect(page.getByTestId('data-card')).toBeVisible();
  61 |     await expect(page.getByRole('navigation', { name: 'Chọn dataset' }).getByRole('link')).toHaveCount(3);
  62 |     await page.getByRole('link', { name: 'Hợp hàm & lý thuyết', exact: true }).click();
  63 |     await expect(page.getByTestId('function-composition')).toBeVisible();
  64 |     if (chapter.chapter > 1) {
  65 |       await page.getByRole('link', { name: 'Kết quả đã lưu', exact: true }).click(); await expect(page.getByTestId('historical-results')).toBeVisible();
  66 |       await expect(page.getByText('Không thể xử lý yêu cầu', { exact: false })).toHaveCount(0);
  67 |       await page.getByRole('link', { name: 'Triển khai', exact: true }).click(); await expect(page.getByTestId('deployment')).toBeVisible();
  68 |     }
  69 |   }
  70 | });
  71 | test('offline API and invalid deep link show recoverable errors', async ({ page }) => {
  72 |   await page.route('**/api/v3/datasets/**', route => route.abort());
  73 |   await page.goto('/cnn'); await expect(page.getByRole('alert')).toContainText('network_error');
  74 |   await page.unroute('**/api/v3/datasets/**'); await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
  75 |   await expect(page.getByTestId('data-card')).toBeVisible();
  76 |   await page.goto('/cnn?dataset=ch2_cdc_diabetes'); await expect(page.getByRole('alert')).toContainText('Đường dẫn không hợp lệ');
  77 | });
  78 | test('mobile layout, keyboard and WCAG checks on home and CNN', async ({ page }) => {
  79 |   for (const [route, name] of [['/', 'home'], ['/cnn?dataset=ch3_cifar10&family=cnn&section=run', 'cnn-mobile']]) {
  80 |     await page.setViewportSize({ width: 390, height: 844 }); await page.goto(route);
  81 |     await expect(page.getByTestId(name === 'home' ? 'data-card' : 'model-runner')).toBeVisible();
  82 |     expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBeTruthy();
  83 |     const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
  84 |     expect(axe.violations).toEqual([]);
  85 |     await page.keyboard.press('Tab'); await expect(page.locator(':focus')).toBeVisible();
  86 |     await page.screenshot({ path: `${shots}/${name}.png`, fullPage: true });
  87 |   }
  88 | });
  89 | 
```