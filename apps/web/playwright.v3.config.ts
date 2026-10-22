import { defineConfig } from "@playwright/test";
const evidence = process.env.PHASE33_EVIDENCE ?? "development-e2e";
export default defineConfig({
  testDir: "./tests/v3",
  workers: 1,
  fullyParallel: false,
  retries: 0,
  forbidOnly: true,
  timeout: 120_000,
  expect: { timeout: 25_000 },
  outputDir: `../../artifacts/manifests/phase33/${evidence}-artifacts`,
  reporter: [
    ["line"],
    [
      "junit",
      { outputFile: `../../artifacts/manifests/phase33/${evidence}.xml` },
    ],
    [
      "json",
      { outputFile: `../../artifacts/manifests/phase33/${evidence}.json` },
    ],
  ],
  use: {
    baseURL: "http://localhost:5173",
    headless: true,
    viewport: { width: 1440, height: 1000 },
    trace: "off",
    video: "off",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm run preview",
    url: "http://localhost:5173",
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
