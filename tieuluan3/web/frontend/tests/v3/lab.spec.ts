import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { chapters } from "../../src/v3/catalog";
import type { Job } from "../../src/v3/types";
const base = "../../artifacts/manifests/phase33";
const evidence = process.env.PHASE33_EVIDENCE ?? "development-e2e";
const shots = `${base}/${evidence}-screenshots`;
mkdirSync(shots, { recursive: true });
const reference = JSON.parse(
  readFileSync("../../artifacts/manifests/phase32/http_cpu_v2.json", "utf8"),
);
const checksName = process.env.PHASE33_CHECKS;
if (checksName && !/^[a-z0-9_-]+$/.test(checksName))
  throw new Error("Invalid checks receipt");
const checksPath = checksName ? `${base}/${checksName}_checks.json` : null;
const checks = checksPath ? JSON.parse(readFileSync(checksPath, "utf8")) : null;
test.beforeAll(async ({ request }) => {
  if (!checks) return;
  for (const row of checks.source)
    expect(
      createHash("sha256")
        .update(readFileSync(`../../${row.path}`))
        .digest("hex"),
    ).toBe(row.sha256);
  const served = [];
  for (const row of checks.build_outputs) {
    const name = row.path.split(`/web-preview-${checksName}/`)[1];
    const response = await request.get(`/${name}`);
    expect(response.ok()).toBeTruthy();
    expect(
      createHash("sha256")
        .update(await response.body())
        .digest("hex"),
    ).toBe(row.sha256);
    served.push({ path: name, sha256: row.sha256 });
  }
  writeFileSync(
    `${base}/${evidence}-served_build.json`,
    JSON.stringify(
      {
        status: "PASS",
        source_sha256: checks.source_sha256,
        checks_sha256: createHash("sha256")
          .update(readFileSync(checksPath!))
          .digest("hex"),
        served,
        model_inference_executed: false,
      },
      null,
      2,
    ),
    { flag: "wx" },
  );
});

class LabPage {
  constructor(readonly page: Page) {}
  async open(route: string) {
    await this.page.goto(route);
    await expect(this.page.getByTestId("model-runner")).toBeVisible();
  }
  async run(count: number) {
    let job: Job | null = null;
    this.page.on("response", async (response) => {
      if (
        /\/api\/v3\/jobs\/job_[a-f0-9]+$/.test(response.url()) &&
        response.ok()
      )
        job = await response.json();
    });
    await this.page
      .getByRole("button", { name: /Chạy cả 3 mô hình|Chạy B0–B4|So sánh A0/ })
      .click();
    await expect
      .poll(() => job?.status, { timeout: 95_000 })
      .toMatch(/succeeded|failed|partial/);
    await expect(this.page.getByTestId("model-result")).toHaveCount(count);
    return job! as Job;
  }
}

for (const chapter of chapters.filter((c) => c.chapter > 1)) {
  for (const dataset of chapter.datasets) {
    for (const family of chapter.chapter === 4
      ? ["rnn", "lstm"]
      : [chapter.family]) {
      test(`live TRAIN comparison ${dataset}/${family}`, async ({ page }) => {
        const errors: string[] = [];
        page.on("pageerror", (error) => errors.push(error.message));
        const lab = new LabPage(page);
        await lab.open(
          `${chapter.route}?dataset=${dataset}&family=${family}&section=run`,
        );
        const job = await lab.run(chapter.chapter === 5 ? 5 : 3);
        const old = reference.results.find(
          (row: { dataset_id: string; family: string }) =>
            row.dataset_id === dataset && row.family === family,
        );
        expect(job.results.map((row) => row.implementation)).toEqual(
          old.job.results.map(
            (row: { implementation: string }) => row.implementation,
          ),
        );
        if (dataset.includes("wikidata")) {
          expect(
            job.results.every((row) => row.status === "unavailable"),
          ).toBeTruthy();
          await expect(
            page.getByText("Wikidata · structural browser, không QA benchmark"),
          ).toBeVisible();
        } else {
          expect(job.status).toBe("succeeded");
          expect(
            job.results.every(
              (row) =>
                row.actual_backend === "numpy" && row.actual_device === "cpu",
            ),
          ).toBeTruthy();
        }
        if (chapter.chapter < 5)
          job.results.forEach((slot, n) => {
            expect(slot.artifact_sha256).toBe(
              old.job.results[n].artifact_sha256,
            );
            expect(slot.prediction).toEqual(old.job.results[n].prediction);
          });
        if (chapter.chapter === 6)
          await expect(page.getByTestId("agent-trace")).toBeVisible();
        expect(errors).toEqual([]);
        writeFileSync(
          `${base}/${evidence}-${dataset}-${family}.json`,
          JSON.stringify(
            {
              scope: "TRAIN-only UI serving smoke; not historical TEST",
              job,
              input_split: old.input_split,
              models_retrained: 0,
              source_sha256: checks?.source_sha256 ?? null,
              historical_test_evaluation_executed: false,
            },
            null,
            2,
          ),
          { flag: "wx" },
        );
        if (
          [
            "ch3_idrid",
            "ch4_gold_pink_sheet",
            "ch5_medquad_diabetes",
            "ch6_diabetes_tasks",
          ].includes(dataset)
        ) {
          await page.screenshot({
            path: `${shots}/${dataset}-${family}.png`,
            fullPage: true,
          });
        }
      });
    }
  }
}

test("deep link, back/forward, RNN toggle and refresh keep selections", async ({
  page,
}) => {
  await page.goto(
    "/rnn?dataset=ch4_bis_house_prices&family=lstm&section=theory",
  );
  await expect(page.getByTestId("function-composition")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "LSTM", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.reload();
  await expect(page.getByTestId("function-composition")).toBeVisible();
  await page.getByRole("button", { name: "RNN", exact: true }).click();
  await expect(page).toHaveURL(/family=rnn/);
  await page.goBack();
  await expect(page).toHaveURL(/family=lstm/);
  await page.goForward();
  await expect(page).toHaveURL(/family=rnn/);
});
test("all18dataset cards, function contracts, historical panels and deployment load", async ({
  page,
}) => {
  test.setTimeout(360_000);
  for (const chapter of chapters)
    for (const dataset of chapter.datasets) {
      await page.goto(
        `${chapter.route}?dataset=${dataset}&family=${chapter.family}&section=data`,
      );
      await expect(page.getByTestId("data-card")).toBeVisible();
      await expect(
        page
          .getByRole("navigation", { name: "Chọn dataset" })
          .getByRole("link"),
      ).toHaveCount(3);
      await page
        .getByRole("link", { name: "Hợp hàm & lý thuyết", exact: true })
        .click();
      await expect(page.getByTestId("function-composition")).toBeVisible();
      if (chapter.chapter > 1)
        await expect(page.locator(".v3-flow")).toBeVisible();
      if (chapter.chapter > 1) {
        await page
          .getByRole("link", { name: "Kết quả đã lưu", exact: true })
          .click();
        await expect(page.getByTestId("historical-results")).toBeVisible();
        await expect(
          page.getByTestId("historical-results").locator(".v3-loading"),
        ).toHaveCount(0);
        await expect(
          page.getByText("Không thể xử lý yêu cầu", { exact: false }),
        ).toHaveCount(0);
        await page
          .getByRole("link", { name: "Triển khai", exact: true })
          .click();
        await expect(page.getByTestId("deployment")).toBeVisible();
      }
    }
});
test("desktop accessibility on each chapter", async ({ page }) => {
  test.setTimeout(180_000);
  for (const chapter of chapters) {
    await page.goto(
      `${chapter.route}?section=${chapter.chapter === 1 ? "data" : "run"}`,
    );
    await expect(
      page.getByTestId(chapter.chapter === 1 ? "data-card" : "model-runner"),
    ).toBeVisible();
    const axe = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(axe.violations).toEqual([]);
  }
});
test("offline API and invalid deep link show recoverable errors", async ({
  page,
}) => {
  await page.route("**/api/v3/datasets/**", (route) => route.abort());
  await page.goto("/cnn");
  await expect(page.getByRole("alert")).toContainText("network_error");
  await page.unroute("**/api/v3/datasets/**");
  await page.getByRole("button", { name: "Thử lại", exact: true }).click();
  await expect(page.getByTestId("data-card")).toBeVisible();
  await page.goto("/cnn?dataset=ch2_cdc_diabetes");
  await expect(page.getByRole("alert")).toContainText("Đường dẫn không hợp lệ");
});
test("mobile layout, keyboard and WCAG checks on home and CNN", async ({
  page,
}) => {
  for (const [route, name] of [
    ["/", "home"],
    ["/cnn?dataset=ch3_cifar10&family=cnn&section=run", "cnn-mobile"],
  ]) {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(route);
    await expect(
      page.getByTestId(name === "home" ? "data-card" : "model-runner"),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBeTruthy();
    const axe = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(axe.violations).toEqual([]);
    await expect(
      page
        .getByRole("navigation", { name: "Chọn dataset" })
        .locator('[aria-current="page"]'),
    ).toBeInViewport();
    await page.screenshot({ path: `${shots}/${name}.png`, fullPage: true });
    await page.keyboard.press("Tab");
    await expect(page.locator(":focus")).toBeVisible();
  }
});
