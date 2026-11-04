import { defineConfig } from "../../apps/web/node_modules/@playwright/test/index.mjs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = fileURLToPath(new URL("../../", import.meta.url));
const evidence = path.join(root, "artifacts/manifests/render_v3_r1/ui");
export default defineConfig({
  testDir: fileURLToPath(new URL("./", import.meta.url)),
  testMatch: "render-v3-r1.spec.mjs",
  workers: 1, fullyParallel: false, retries: 0, forbidOnly: true,
  timeout: 120_000, expect: { timeout: 25_000 },
  outputDir: evidence + "-artifacts",
  reporter: [["line"], ["junit", { outputFile: evidence + ".xml" }], ["json", { outputFile: evidence + ".json" }]],
  use: { baseURL: "http://localhost:5173", headless: true, viewport: { width: 1440, height: 1000 }, trace: "off", video: "off", screenshot: "off" },
  webServer: {
    cwd: path.join(root, "apps/web"),
    command: `"${path.join(root, ".local/node-v22.23.4-win-x64/node.exe")}" node_modules/vite/bin/vite.js preview --outDir "${path.join(root, "report/build/render-v3-r1/web-local")}" --host localhost --port 5173 --strictPort`,
    url: "http://localhost:5173", reuseExistingServer: false, timeout: 30_000,
  },
});
