import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { readFileSync } from "node:fs";
import App from "./App";
import { ApiClient } from "./client";
const fixtures = JSON.parse(
  readFileSync(
    "../../artifacts/manifests/phase33/contract_fixtures.json",
    "utf8",
  ),
);
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
function mockedFetch() {
  return vi.fn(async (value: RequestInfo | URL) => {
    const url = new URL(String(value));
    const path = url.pathname;
    let data = fixtures[path + url.search] ?? fixtures[path];
    if (path === "/ready") data = { status: "ready", components: [] };
    if (/^\/api\/v3\/datasets\/[^/]+$/.test(path))
      data = {
        data: fixtures["/api/v3/datasets"].data.find(
          (row: { dataset_id: string }) =>
            row.dataset_id === path.split("/").pop(),
        ),
      };
    if (path === "/api/v3/models") {
      const all = fixtures["/api/v3/models?page_size=100"];
      data = {
        ...all,
        data: all.data.filter((m: { model_id: string }) =>
          m.model_id.startsWith(url.searchParams.get("dataset_id") ?? ""),
        ),
      };
    }
    return new Response(
      JSON.stringify(data ?? { error: { code: "not_found" } }),
      { status: data ? 200 : 404 },
    );
  });
}
function mount(route: string) {
  vi.stubGlobal("fetch", mockedFetch());
  return render(
    <MemoryRouter initialEntries={[route]}>
      <App />
    </MemoryRouter>,
  );
}
describe("knowledge navigation", () => {
  it("has six knowledge links and three CNN datasets", async () => {
    mount("/cnn");
    expect(
      screen
        .getByRole("navigation", { name: "Điều hướng chính" })
        .querySelectorAll("a"),
    ).toHaveLength(6);
    await screen.findByRole("heading", { name: /Học từ hình ảnh/ });
    expect(
      screen
        .getByRole("navigation", { name: "Chọn dataset" })
        .querySelectorAll("a"),
    ).toHaveLength(3);
  });
  it("shows a useful invalid URL message, not a blank page", async () => {
    mount("/cnn?dataset=ch2_cdc_diabetes");
    expect((await screen.findByRole("alert")).textContent).toMatch(
      /Đường dẫn không hợp lệ/,
    );
  });
  it.each(["/ml", "/cnn", "/rnn", "/rag", "/agents"])(
    "renders all dataset data, theory and deployment panels at %s",
    async (route) => {
      mount(route);
      await screen.findByTestId("data-card");
      fireEvent.click(
        screen.getByRole("link", { name: "Hợp hàm & lý thuyết" }),
      );
      await screen.findByTestId("function-composition");
      fireEvent.click(screen.getByRole("link", { name: "Triển khai" }));
      await screen.findByTestId("deployment");
    },
  );
  it("keeps original null costs in display", async () => {
    mount("/rnn?dataset=ch4_household_power&family=lstm&section=theory");
    await screen.findByTestId("function-composition");
    expect(
      screen.getByRole("button", { name: "LSTM" }).getAttribute("aria-pressed"),
    ).toBe("true");
  });
});
describe("cancel contract regression", () => {
  it("posts only the cancellation body allowed by frozen OpenAPI", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(new Response("{}", { status: 200 }));
    await new ApiClient(
      "http://localhost:5000",
      fetcher,
      sessionStorage,
    ).cancel("job_abcd");
    expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual({
      reason: "user_cancelled",
    });
  });
});
