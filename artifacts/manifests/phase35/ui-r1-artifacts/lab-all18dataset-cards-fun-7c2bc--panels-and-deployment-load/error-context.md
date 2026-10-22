# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: lab.spec.ts >> all18dataset cards, function contracts, historical panels and deployment load
- Location: tests\v3\lab.spec.ts:185:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByTestId('data-card')
Expected: visible
Timeout: 25000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByTestId('data-card') with timeout 25000ms
  - waiting for getByTestId('data-card')

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
  - paragraph: CHƯƠNG 04 / PHÒNG THÍ NGHIỆM TƯƠNG TÁC
  - heading "Học từ chuỗi thời gian" [level=1]
  - paragraph: Đọc dữ liệu theo thứ tự thời gian. RNN truyền trạng thái qua từng bước; LSTM thêm các cổng để giữ hoặc quên thông tin. Dự báo không được nhìn tương lai.
  - text: 3 dataset / chương Checkpoint đã khóa Không train trên web
  - navigation "Chọn dataset":
    - link "01 Giá vàng · World Bank":
      - /url: /rnn?dataset=ch4_gold_pink_sheet&family=rnn&section=data
    - link "02 Giá nhà · BIS":
      - /url: /rnn?dataset=ch4_bis_house_prices&family=rnn&section=data
    - link "03 Điện năng · Household":
      - /url: /rnn?dataset=ch4_household_power&family=rnn&section=data
  - heading "Giá nhà · BIS" [level=2]
  - group "Họ mô hình":
    - button "RNN" [pressed]
    - button "LSTM"
  - navigation "Nội dung dataset":
    - link "Dữ liệu":
      - /url: /rnn?dataset=ch4_bis_house_prices&family=rnn&section=data
    - link "Hợp hàm & lý thuyết":
      - /url: /rnn?dataset=ch4_bis_house_prices&family=rnn&section=theory
    - link "Chạy so sánh":
      - /url: /rnn?dataset=ch4_bis_house_prices&family=rnn&section=run
    - link "Kết quả đã lưu":
      - /url: /rnn?dataset=ch4_bis_house_prices&family=rnn&section=results
    - link "Triển khai":
      - /url: /rnn?dataset=ch4_bis_house_prices&family=rnn&section=deployment
  - status: Đang đọc artifact đã khóa…
  - strong: Học thuật, không lời khuyên chuyên môn.
  - paragraph: Không nhập bệnh án hoặc secret. Dự đoán trên snapshot không dùng để chẩn đoán, định giá hiện tại hay đầu tư. TEST đã niêm phong không được chạy lại từ giao diện.
- contentinfo: MODEL LAB / AI TERM PAPER V3 React UI · Python API · provenance first
```

# Test source

```ts
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
  163 |   }
  164 | }
  165 | 
  166 | test("deep link, back/forward, RNN toggle and refresh keep selections", async ({
  167 |   page,
  168 | }) => {
  169 |   await page.goto(
  170 |     "/rnn?dataset=ch4_bis_house_prices&family=lstm&section=theory",
  171 |   );
  172 |   await expect(page.getByTestId("function-composition")).toBeVisible();
  173 |   await expect(
  174 |     page.getByRole("button", { name: "LSTM", exact: true }),
  175 |   ).toHaveAttribute("aria-pressed", "true");
  176 |   await page.reload();
  177 |   await expect(page.getByTestId("function-composition")).toBeVisible();
  178 |   await page.getByRole("button", { name: "RNN", exact: true }).click();
  179 |   await expect(page).toHaveURL(/family=rnn/);
  180 |   await page.goBack();
  181 |   await expect(page).toHaveURL(/family=lstm/);
  182 |   await page.goForward();
  183 |   await expect(page).toHaveURL(/family=rnn/);
  184 | });
  185 | test("all18dataset cards, function contracts, historical panels and deployment load", async ({
  186 |   page,
  187 | }) => {
  188 |   test.setTimeout(360_000);
  189 |   for (const chapter of chapters)
  190 |     for (const dataset of chapter.datasets) {
  191 |       await page.goto(
  192 |         `${chapter.route}?dataset=${dataset}&family=${chapter.family}&section=data`,
  193 |       );
> 194 |       await expect(page.getByTestId("data-card")).toBeVisible();
      |                                                   ^ Error: expect(locator).toBeVisible() failed
  195 |       await expect(
  196 |         page
  197 |           .getByRole("navigation", { name: "Chọn dataset" })
  198 |           .getByRole("link"),
  199 |       ).toHaveCount(3);
  200 |       await page
  201 |         .getByRole("link", { name: "Hợp hàm & lý thuyết", exact: true })
  202 |         .click();
  203 |       await expect(page.getByTestId("function-composition")).toBeVisible();
  204 |       if (chapter.chapter > 1)
  205 |         await expect(page.locator(".v3-flow")).toBeVisible();
  206 |       if (chapter.chapter > 1) {
  207 |         await page
  208 |           .getByRole("link", { name: "Kết quả đã lưu", exact: true })
  209 |           .click();
  210 |         await expect(page.getByTestId("historical-results")).toBeVisible();
  211 |         await expect(
  212 |           page.getByTestId("historical-results").locator(".v3-loading"),
  213 |         ).toHaveCount(0);
  214 |         await expect(
  215 |           page.getByText("Không thể xử lý yêu cầu", { exact: false }),
  216 |         ).toHaveCount(0);
  217 |         await page
  218 |           .getByRole("link", { name: "Triển khai", exact: true })
  219 |           .click();
  220 |         await expect(page.getByTestId("deployment")).toBeVisible();
  221 |       }
  222 |     }
  223 | });
  224 | test("desktop accessibility on each chapter", async ({ page }) => {
  225 |   test.setTimeout(180_000);
  226 |   for (const chapter of chapters) {
  227 |     await page.goto(
  228 |       `${chapter.route}?section=${chapter.chapter === 1 ? "data" : "run"}`,
  229 |     );
  230 |     await expect(
  231 |       page.getByTestId(chapter.chapter === 1 ? "data-card" : "model-runner"),
  232 |     ).toBeVisible();
  233 |     const axe = await new AxeBuilder({ page })
  234 |       .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
  235 |       .analyze();
  236 |     expect(axe.violations).toEqual([]);
  237 |   }
  238 | });
  239 | test("offline API and invalid deep link show recoverable errors", async ({
  240 |   page,
  241 | }) => {
  242 |   await page.route("**/api/v3/datasets/**", (route) => route.abort());
  243 |   await page.goto("/cnn");
  244 |   await expect(page.getByRole("alert")).toContainText("network_error");
  245 |   await page.unroute("**/api/v3/datasets/**");
  246 |   await page.getByRole("button", { name: "Thử lại", exact: true }).click();
  247 |   await expect(page.getByTestId("data-card")).toBeVisible();
  248 |   await page.goto("/cnn?dataset=ch2_cdc_diabetes");
  249 |   await expect(page.getByRole("alert")).toContainText("Đường dẫn không hợp lệ");
  250 | });
  251 | test("mobile layout, keyboard and WCAG checks on home and CNN", async ({
  252 |   page,
  253 | }) => {
  254 |   for (const [route, name] of [
  255 |     ["/", "home"],
  256 |     ["/cnn?dataset=ch3_cifar10&family=cnn&section=run", "cnn-mobile"],
  257 |   ]) {
  258 |     await page.setViewportSize({ width: 390, height: 844 });
  259 |     await page.goto(route);
  260 |     await expect(
  261 |       page.getByTestId(name === "home" ? "data-card" : "model-runner"),
  262 |     ).toBeVisible();
  263 |     expect(
  264 |       await page.evaluate(
  265 |         () => document.documentElement.scrollWidth <= innerWidth + 1,
  266 |       ),
  267 |     ).toBeTruthy();
  268 |     const axe = await new AxeBuilder({ page })
  269 |       .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
  270 |       .analyze();
  271 |     expect(axe.violations).toEqual([]);
  272 |     await expect(
  273 |       page
  274 |         .getByRole("navigation", { name: "Chọn dataset" })
  275 |         .locator('[aria-current="page"]'),
  276 |     ).toBeInViewport();
  277 |     await page.screenshot({ path: `${shots}/${name}.png`, fullPage: true });
  278 |     await page.keyboard.press("Tab");
  279 |     await expect(page.locator(":focus")).toBeVisible();
  280 |   }
  281 | });
  282 | 
```