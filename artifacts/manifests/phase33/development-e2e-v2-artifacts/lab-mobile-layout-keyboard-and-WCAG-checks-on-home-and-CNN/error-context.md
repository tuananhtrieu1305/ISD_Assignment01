# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: lab.spec.ts >> mobile layout, keyboard and WCAG checks on home and CNN
- Location: tests\v3\lab.spec.ts:79:1

# Error details

```
Error: expect(received).toEqual(expected) // deep equality

- Expected  -   1
+ Received  + 128

- Array []
+ Array [
+   Object {
+     "description": "Ensure the contrast between foreground and background colors meets WCAG 2 AA minimum contrast ratio thresholds",
+     "help": "Elements must meet minimum color contrast ratio thresholds",
+     "helpUrl": "https://dequeuniversity.com/rules/axe/4.14/color-contrast?application=playwright",
+     "id": "color-contrast",
+     "impact": "serious",
+     "nodes": Array [
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#f0f5ff",
+               "contrastRatio": 3.43,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#577fe7",
+               "fontSize": "8.2pt (10.88px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.43 (foreground color: #577fe7, background color: #f0f5ff, font size: 8.2pt (10.88px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<a aria-current=\"page\" href=\"/?dataset=ch1_iris_history&amp;family=history&amp;section=data\" data-discover=\"true\"><span>01</span>Iris</a>",
+                 "target": Array [
+                   ".v3-dataset-nav > a[aria-current=\"page\"][data-discover=\"true\"]",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.43 (foreground color: #577fe7, background color: #f0f5ff, font size: 8.2pt (10.88px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<span>01</span>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".v3-dataset-nav > a[aria-current=\"page\"][data-discover=\"true\"] > span",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.45,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#7e8b9e",
+               "fontSize": "8.2pt (10.88px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.45 (foreground color: #7e8b9e, background color: #ffffff, font size: 8.2pt (10.88px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<a href=\"/?dataset=ch1_mnist_history&amp;family=history&amp;section=data\" data-discover=\"true\"><span>02</span>MNIST</a>",
+                 "target": Array [
+                   ".v3-dataset-nav > a[data-discover=\"true\"]:nth-child(2)",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.45 (foreground color: #7e8b9e, background color: #ffffff, font size: 8.2pt (10.88px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<span>02</span>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".v3-dataset-nav > a[data-discover=\"true\"]:nth-child(2) > span",
+         ],
+       },
+       Object {
+         "all": Array [],
+         "any": Array [
+           Object {
+             "data": Object {
+               "bgColor": "#ffffff",
+               "contrastRatio": 3.45,
+               "expectedContrastRatio": "4.5:1",
+               "fgColor": "#7e8b9e",
+               "fontSize": "8.2pt (10.88px)",
+               "fontWeight": "normal",
+               "messageKey": null,
+             },
+             "id": "color-contrast",
+             "impact": "serious",
+             "message": "Element has insufficient color contrast of 3.45 (foreground color: #7e8b9e, background color: #ffffff, font size: 8.2pt (10.88px), font weight: normal). Expected contrast ratio of 4.5:1",
+             "relatedNodes": Array [
+               Object {
+                 "html": "<a href=\"/?dataset=ch1_imagenet_history&amp;family=history&amp;section=data\" data-discover=\"true\"><span>03</span>ImageNet</a>",
+                 "target": Array [
+                   ".v3-dataset-nav > a[data-discover=\"true\"]:nth-child(3)",
+                 ],
+               },
+             ],
+           },
+         ],
+         "failureSummary": "Fix any of the following:
+   Element has insufficient color contrast of 3.45 (foreground color: #7e8b9e, background color: #ffffff, font size: 8.2pt (10.88px), font weight: normal). Expected contrast ratio of 4.5:1",
+         "html": "<span>03</span>",
+         "impact": "serious",
+         "none": Array [],
+         "target": Array [
+           ".v3-dataset-nav > a[data-discover=\"true\"]:nth-child(3) > span",
+         ],
+       },
+     ],
+     "tags": Array [
+       "cat.color",
+       "wcag2aa",
+       "wcag143",
+       "TTv5",
+       "TT13.c",
+       "EN-301-549",
+       "EN-9.1.4.3",
+       "ACT",
+       "RGAAv4",
+       "RGAA-3.2.1",
+     ],
+   },
+ ]
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - link "Đến nội dung chính" [ref=e4] [cursor=pointer]:
    - /url: "#lab-content"
  - banner [ref=e5]:
    - link "Model Lab — Tổng quan" [ref=e6] [cursor=pointer]:
      - /url: /
      - generic [aria-hidden] [ref=e7]:
        - text: M
        - generic [ref=e8]: ↗
      - generic [ref=e9]:
        - generic [ref=e10]: TIỂU LUẬN TRÍ TUỆ NHÂN TẠO
        - strong [ref=e11]: Model Lab/ 03
    - status [ref=e12]: API ready
  - navigation "Điều hướng chính" [ref=e14]:
    - link "Tổng quan" [ref=e15] [cursor=pointer]:
      - /url: /
    - link "ML" [ref=e16] [cursor=pointer]:
      - /url: /ml
    - link "CNN" [ref=e17] [cursor=pointer]:
      - /url: /cnn
    - link "RNN–LSTM" [ref=e18] [cursor=pointer]:
      - /url: /rnn
    - link "KG–RAG" [ref=e19] [cursor=pointer]:
      - /url: /rag
    - link "Multi-Agent" [ref=e20] [cursor=pointer]:
      - /url: /agents
  - main [ref=e21]:
    - generic [ref=e23]:
      - paragraph [ref=e24]: CHƯƠNG01 / PHÒNG THÍ NGHIỆM TƯƠNG TÁC
      - heading "Từ dữ liệu đến quyết định." [level=1] [ref=e25]
      - paragraph [ref=e26]: Từ các luật do con người viết đến mô hình học từ dữ liệu. Iris, MNIST và ImageNet minh họa ba bước chuyển; đây không phải chương huấn luyện.
      - generic [ref=e27]:
        - generic [ref=e28]: 3dataset / chương
        - generic [ref=e29]: Checkpoint đã khóa
        - generic [ref=e30]: Không train trên web
    - generic [ref=e31]:
      - paragraph [ref=e32]: MỘT HÀNH TRÌNH · SÁU CHƯƠNG
      - generic [ref=e33]:
        - link "02 ML 3dataset" [ref=e34] [cursor=pointer]:
          - /url: /ml
          - generic [ref=e35]: "02"
          - strong [ref=e36]: ML
          - generic [ref=e37]: 3dataset
          - generic [aria-hidden] [ref=e38]: ↗
        - link "03 CNN 3dataset" [ref=e39] [cursor=pointer]:
          - /url: /cnn
          - generic [ref=e40]: "03"
          - strong [ref=e41]: CNN
          - generic [ref=e42]: 3dataset
          - generic [aria-hidden] [ref=e43]: ↗
        - link "04 RNN–LSTM 3dataset" [ref=e44] [cursor=pointer]:
          - /url: /rnn
          - generic [ref=e45]: "04"
          - strong [ref=e46]: RNN–LSTM
          - generic [ref=e47]: 3dataset
          - generic [aria-hidden] [ref=e48]: ↗
        - link "05 KG–RAG 3dataset" [ref=e49] [cursor=pointer]:
          - /url: /rag
          - generic [ref=e50]: "05"
          - strong [ref=e51]: KG–RAG
          - generic [ref=e52]: 3dataset
          - generic [aria-hidden] [ref=e53]: ↗
        - link "06 Multi-Agent 3dataset" [ref=e54] [cursor=pointer]:
          - /url: /agents
          - generic [ref=e55]: "06"
          - strong [ref=e56]: Multi-Agent
          - generic [ref=e57]: 3dataset
          - generic [aria-hidden] [ref=e58]: ↗
      - paragraph [ref=e59]: Lịch sử AI qua ba case study bên dưới; các chương2–6 có dữ liệu, hợp hàm, demo và kết quả truy nguồn.
    - navigation "Chọn dataset" [ref=e60]:
      - link "01 Iris" [ref=e61] [cursor=pointer]:
        - /url: /?dataset=ch1_iris_history&family=history&section=data
        - generic [ref=e62]: "01"
        - text: Iris
      - link "02 MNIST" [ref=e63] [cursor=pointer]:
        - /url: /?dataset=ch1_mnist_history&family=history&section=data
        - generic [ref=e64]: "02"
        - text: MNIST
      - link "03 ImageNet" [ref=e65] [cursor=pointer]:
        - /url: /?dataset=ch1_imagenet_history&family=history&section=data
        - generic [ref=e66]: "03"
        - text: ImageNet
    - heading "Iris" [level=2] [ref=e68]
    - navigation "Nội dung dataset" [ref=e69]:
      - link "Dữ liệu" [ref=e70] [cursor=pointer]:
        - /url: /?dataset=ch1_iris_history&family=history&section=data
      - link "Hợp hàm & lý thuyết" [ref=e71] [cursor=pointer]:
        - /url: /?dataset=ch1_iris_history&family=history&section=theory
    - generic [ref=e73]:
      - generic [ref=e74]:
        - generic [ref=e75]:
          - text: DATASET CARD
          - heading "Dữ liệu & nguồn gốc" [level=2] [ref=e76]
        - link "Nguồn chính thức ↗" [ref=e77] [cursor=pointer]:
          - /url: https://archive.ics.uci.edu/static/public/53/iris.zip
      - generic [ref=e78]:
        - generic [ref=e79]:
          - generic [ref=e80]: Kích cỡ logic
          - strong [ref=e81]: "150"
        - generic [ref=e82]:
          - generic [ref=e83]: Dung lượng file nguồn
          - strong [ref=e84]: 3.738 byte
        - generic [ref=e85]:
          - generic [ref=e86]: Phạm vi
          - strong [ref=e87]: historical_case
      - paragraph [ref=e88]: Fisher, R. A. (1936). Iris. UCI Machine Learning Repository. DOI:10.24432/C56C76.
      - group [ref=e89]:
        - generic "Giấy phép, phiên bản & hash" [ref=e90] [cursor=pointer]
      - group [ref=e91]:
        - generic "Thẻ dữ liệu đầy đủ · mẫu/output, phân bố, nhận xét" [ref=e92] [cursor=pointer]
        - generic [ref=e93]:
          - heading "ch1_iris_history — dữ liệu và kiểm tra Phase 24" [level=3] [ref=e94]
          - paragraph [ref=e95]:
            - text: "Phạm vi:"
            - strong [ref=e96]: historical_case
            - text: . Không huấn luyện hay đánh giá TEST trong Phase 24.
          - heading "Nguồn, kích cỡ và cấu trúc" [level=3] [ref=e97]
          - paragraph [ref=e98]:
            - text: "Nguồn:"
            - link "Fisher, R. A. (1936). Iris. UCI Machine Learning Repository. DOI:10.24432/C56C76. ↗" [ref=e99] [cursor=pointer]:
              - /url: https://archive.ics.uci.edu/static/public/53/iris.zip
          - paragraph [ref=e100]: "Phiên bản: UCI 53 original Iris snapshot; sha256:d11fe30213d36434a0879aab7cb00ce3c812eb7ba2495874438abff7b7b762e9"
          - paragraph [ref=e101]: "Giấy phép/phạm vi: CC BY 4.0; attribution required. https://archive.ics.uci.edu/dataset/53/iris"
          - paragraph [ref=e102]: "Raw: 3,738 byte; 150 raw rows."
          - paragraph [ref=e103]: "Số đo và schema phần dùng trong V3:"
          - paragraph [ref=e104]:
            - code [ref=e105]: "``jso"
          - paragraph [ref=e106]: "{"
          - paragraph [ref=e107]: "\"records\": 150,"
          - paragraph [ref=e108]: "\"features\": 4,"
          - paragraph [ref=e109]: "\"unit\": \"raw rows\""
          - paragraph [ref=e110]: "}"
          - paragraph [ref=e111]:
            - code [ref=e112]: "`"
          - heading "Mẫu input/output" [level=3] [ref=e113]
          - paragraph [ref=e114]: Mẫu nguồn phục vụ lịch sử, không phải output của mô hình được train trong Phase24.
          - paragraph [ref=e115]:
            - code [ref=e116]: "``jso"
          - paragraph [ref=e117]: "["
          - paragraph [ref=e118]: "{"
          - paragraph [ref=e119]: "\"input\": ["
          - paragraph [ref=e120]: 5.1,
          - paragraph [ref=e121]: 3.5,
          - paragraph [ref=e122]: 1.4,
          - paragraph [ref=e123]: "0.2"
          - paragraph [ref=e124]: "],"
          - paragraph [ref=e125]: "\"known_output\": \"Iris-setosa\""
          - paragraph [ref=e126]: "},"
          - paragraph [ref=e127]: "{"
          - paragraph [ref=e128]: "\"input\": ["
          - paragraph [ref=e129]: 4.9,
          - paragraph [ref=e130]: 3.0,
          - paragraph [ref=e131]: 1.4,
          - paragraph [ref=e132]: "0.2"
          - paragraph [ref=e133]: "],"
          - paragraph [ref=e134]: "\"known_output\": \"Iris-setosa\""
          - paragraph [ref=e135]: "},"
          - paragraph [ref=e136]: "{"
          - paragraph [ref=e137]: "\"input\": ["
          - paragraph [ref=e138]: 4.7,
          - paragraph [ref=e139]: 3.2,
          - paragraph [ref=e140]: 1.3,
          - paragraph [ref=e141]: "0.2"
          - paragraph [ref=e142]: "],"
          - paragraph [ref=e143]: "\"known_output\": \"Iris-setosa\""
          - paragraph [ref=e144]: "}"
          - paragraph [ref=e145]: "]"
          - paragraph [ref=e146]:
            - code [ref=e147]: "`"
          - heading "Phân bố và chất lượng dữ liệu" [level=3] [ref=e148]
          - paragraph [ref=e149]:
            - code [ref=e150]: "``jso"
          - paragraph [ref=e151]: "{"
          - paragraph [ref=e152]: "\"Iris-setosa\": 50,"
          - paragraph [ref=e153]: "\"Iris-versicolor\": 50,"
          - paragraph [ref=e154]: "\"Iris-virginica\": 50"
          - paragraph [ref=e155]: "}"
          - paragraph [ref=e156]:
            - code [ref=e157]: "`"
          - heading "Cách chia tập và tiền xử lý" [level=3] [ref=e158]
          - paragraph [ref=e159]: Ch1 không huấn luyện. Giữ official split nếu có; không tạo TEST hay preprocessing fit cho chương lịch sử.
          - heading "Nhận xét và giới hạn" [level=3] [ref=e160]
          - paragraph [ref=e161]: "- Benchmark nhỏ, cân bằng; chỉ minh họa lịch sử phân loại, không có thí nghiệm V3 Ch1."
          - heading "Bằng chứng tái lập" [level=3] [ref=e162]
          - paragraph [ref=e163]:
            - text: "Chi tiết:"
            - code [ref=e164]: artifacts/manifests/phase24/ch1_iris_history/eda.json
            - text: .
          - paragraph [ref=e165]: Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.
          - paragraph [ref=e166]: "![ch1_iris_history](../../../../artifacts/figures/phase24/ch1_iris_history_distribution.png)"
      - group [ref=e167]:
        - 'generic "EDA gốc: size/schema, phân bố, missing và giới hạn" [ref=e168] [cursor=pointer]'
      - generic [ref=e169]: Không nhập bệnh án hoặc dữ liệu nhạy cảm. Nguồn là snapshot học thuật, không dữ liệu thị trường hiện tại.
    - generic [ref=e170]:
      - strong [ref=e171]: Học thuật, không lời khuyên chuyên môn.
      - paragraph [ref=e172]: Không nhập bệnh án hoặc secret. Dự đoán trên snapshot không dùng để chẩn đoán, định giá hiện tại hay đầu tư. TEST đã niêm phong không được chạy lại từ giao diện.
  - contentinfo [ref=e173]:
    - generic [ref=e174]: MODEL LAB / AI TERM PAPER V3
    - generic [ref=e175]: React UI · Python API · provenance first
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
  14 |   async open(route: string) { await this.page.goto(route); await expect(this.page.getByTestId('model-runner')).toBeVisible(); }
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
  58 |   test.setTimeout(360_000);
  59 |   for (const chapter of chapters) for (const dataset of chapter.datasets) {
  60 |     await page.goto(`${chapter.route}?dataset=${dataset}&family=${chapter.family}&section=data`);
  61 |     await expect(page.getByTestId('data-card')).toBeVisible();
  62 |     await expect(page.getByRole('navigation', { name: 'Chọn dataset' }).getByRole('link')).toHaveCount(3);
  63 |     await page.getByRole('link', { name: 'Hợp hàm & lý thuyết', exact: true }).click();
  64 |     await expect(page.getByTestId('function-composition')).toBeVisible();
  65 |     if (chapter.chapter > 1) {
  66 |       await page.getByRole('link', { name: 'Kết quả đã lưu', exact: true }).click(); await expect(page.getByTestId('historical-results')).toBeVisible();
  67 |       await expect(page.getByText('Không thể xử lý yêu cầu', { exact: false })).toHaveCount(0);
  68 |       await page.getByRole('link', { name: 'Triển khai', exact: true }).click(); await expect(page.getByTestId('deployment')).toBeVisible();
  69 |     }
  70 |   }
  71 | });
  72 | test('offline API and invalid deep link show recoverable errors', async ({ page }) => {
  73 |   await page.route('**/api/v3/datasets/**', route => route.abort());
  74 |   await page.goto('/cnn'); await expect(page.getByRole('alert')).toContainText('network_error');
  75 |   await page.unroute('**/api/v3/datasets/**'); await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
  76 |   await expect(page.getByTestId('data-card')).toBeVisible();
  77 |   await page.goto('/cnn?dataset=ch2_cdc_diabetes'); await expect(page.getByRole('alert')).toContainText('Đường dẫn không hợp lệ');
  78 | });
  79 | test('mobile layout, keyboard and WCAG checks on home and CNN', async ({ page }) => {
  80 |   for (const [route, name] of [['/', 'home'], ['/cnn?dataset=ch3_cifar10&family=cnn&section=run', 'cnn-mobile']]) {
  81 |     await page.setViewportSize({ width: 390, height: 844 }); await page.goto(route);
  82 |     await expect(page.getByTestId(name === 'home' ? 'data-card' : 'model-runner')).toBeVisible();
  83 |     expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBeTruthy();
  84 |     const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
> 85 |     expect(axe.violations).toEqual([]);
     |                            ^ Error: expect(received).toEqual(expected) // deep equality
  86 |     await page.keyboard.press('Tab'); await expect(page.locator(':focus')).toBeVisible();
  87 |     await page.screenshot({ path: `${shots}/${name}.png`, fullPage: true });
  88 |   }
  89 | });
  90 | 
```