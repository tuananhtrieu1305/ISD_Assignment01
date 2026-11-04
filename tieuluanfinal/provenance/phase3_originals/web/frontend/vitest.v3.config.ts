import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  test: {
    reporters: ["default", "junit"],
    outputFile: `../../artifacts/manifests/phase33/${process.env.PHASE33_EVIDENCE ?? "development-unit"}.xml`,
    include: ["src/v3/**/*.test.{ts,tsx}"],
    environment: "jsdom",
    restoreMocks: true,
    clearMocks: true,
    coverage: {
      provider: "v8",
      include: ["src/v3/**/*.{ts,tsx}"],
      exclude: ["src/v3/**/*.test.*", "src/v3/types.ts"],
      reportsDirectory: `../../artifacts/manifests/phase33/${process.env.PHASE33_EVIDENCE ?? "development-unit"}-coverage`,
      reporter: ["text", "json", "json-summary"],
      thresholds: { statements: 80, branches: 80, functions: 80, lines: 80 },
    },
  },
});
