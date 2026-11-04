import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { readFileSync } from "node:fs";
import { webcrypto } from "node:crypto";
import ModelRunner from "./ModelRunner";
import Comparison from "./Comparison";
import AgentTrace from "./AgentTrace";
import HistoricalResults from "./HistoricalResults";
import { ApiClient } from "./client";
import {
  Boundary,
  DataTable,
  ErrorPanel,
  Markdown,
  BarList,
  flatFields,
} from "./ui";
import type { Overview } from "./types";
const root = "../..";
const fixture = JSON.parse(
  readFileSync(
    `${root}/artifacts/manifests/phase33/contract_fixtures.json`,
    "utf8",
  ),
);
const old = JSON.parse(
  readFileSync(`${root}/artifacts/manifests/phase32/http_cpu_v2.json`, "utf8"),
);
const registry = JSON.parse(
  readFileSync(`${root}/artifacts/manifests/phase32/registry_v3.json`, "utf8"),
);
const snapshot = (dataset: string): Overview =>
  structuredClone(fixture[`/api/v3/datasets/${dataset}/overview`].data);
beforeEach(() => {
  vi.stubGlobal("crypto", webcrypto);
  sessionStorage.clear();
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
function jobFor(dataset: string, family?: string) {
  return structuredClone(
    old.results.find(
      (row: { dataset_id: string; family: string }) =>
        row.dataset_id === dataset && (!family || row.family === family),
    ),
  );
}
function runnerApi(dataset: string, family?: string) {
  const row = jobFor(dataset, family);
  let cancelled = false;
  const get = vi.fn(async (path: string) =>
    path.endsWith("/details")
      ? { data: row.details }
      : { ...row.job, status: cancelled ? "cancelled" : row.job.status },
  );
  return {
    base: "http://localhost:5000",
    get,
    submit: vi.fn(async () => ({ job_id: row.job.job_id })),
    cancel: vi.fn(async () => {
      cancelled = true;
      return {};
    }),
  };
}
describe("runner structured input and async lifecycle", () => {
  it.each([
    ["ch2_ames_housing", "mlp"],
    ["ch3_idrid", "cnn"],
    ["ch4_gold_pink_sheet", "rnn"],
    ["ch5_medquad_diabetes", "kg_rag"],
    ["ch6_diabetes_tasks", "multi_agent"],
    ["ch5_wikidata_subgraphs", "kg_rag"],
  ])("runs all slots and details from %s", async (dataset, family) => {
    const api = runnerApi(dataset, family);
    const overview = snapshot(dataset);
    render(
      <ModelRunner
        api={api as unknown as ApiClient}
        overview={overview}
        family={family}
      />,
    );
    if (overview.sample!.request.input.kind === "tabular")
      fireEvent.change(screen.getByLabelText("lot_area"), {
        target: { value: "10000" },
      });
    if (overview.sample!.request.input.kind === "question")
      fireEvent.change(screen.getByRole("textbox"), {
        target: { value: overview.sample!.request.input.text },
      });
    fireEvent.click(
      screen.getByRole("button", { name: /Chạy cả 3|Chạy B0|So sánh A0/ }),
    );
    await waitFor(() =>
      expect(screen.getAllByTestId("model-result")).toHaveLength(
        dataset.startsWith("ch5") ? 5 : 3,
      ),
    );
    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining("/details"),
        expect.anything(),
      ),
    );
    expect(api.submit.mock.calls).toHaveLength(1);
    fireEvent.click(
      screen.getByRole("button", { name: "Mẫu TRAIN", exact: true }),
    );
    if (dataset.startsWith("ch6")) await screen.findByTestId("agent-trace");
  });
  it("rejects malformed sequence JSON before submit", async () => {
    const api = runnerApi("ch4_gold_pink_sheet");
    render(
      <ModelRunner
        api={api as unknown as ApiClient}
        overview={snapshot("ch4_gold_pink_sheet")}
        family="rnn"
      />,
    );
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "not JSON" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Chạy cả 3/ }));
    expect((await screen.findByRole("alert")).textContent).toContain(
      "JSON hợp lệ",
    );
    expect(api.submit).not.toHaveBeenCalled();
  });
  it("rejects SVG/oversized upload and accepts PNG without HTML rendering", async () => {
    const api = runnerApi("ch3_idrid");
    render(
      <ModelRunner
        api={api as unknown as ApiClient}
        overview={snapshot("ch3_idrid")}
        family="cnn"
      />,
    );
    const field = screen.getByLabelText("Chọn ảnh PNG/JPEG");
    fireEvent.change(field, {
      target: {
        files: [new File(["<script/>"], "a.svg", { type: "image/svg+xml" })],
      },
    });
    expect((await screen.findByRole("alert")).textContent).toContain(
      "PNG/JPEG",
    );
    fireEvent.change(field, {
      target: { files: [new File(["x"], "a.png", { type: "image/png" })] },
    });
    await waitFor(() =>
      expect(
        screen
          .getByAltText("Ảnh sẽ dùng chung cho ba mô hình")
          .getAttribute("src"),
      ).toContain("eA=="),
    );
  });
  it("polls queued/running and cancels the owned job", async () => {
    const api = runnerApi("ch3_idrid");
    let cancel = false;
    api.get.mockImplementation(async (path) =>
      path.endsWith("/details")
        ? { data: {} }
        : {
            ...jobFor("ch3_idrid").job,
            status: cancel ? "cancelled" : "running",
            results: [],
          },
    );
    api.cancel.mockImplementation(async () => {
      cancel = true;
      return {};
    });
    render(
      <ModelRunner
        api={api as unknown as ApiClient}
        overview={snapshot("ch3_idrid")}
        family="cnn"
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Chạy cả 3/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Hủy job" }));
    await waitFor(() => expect(api.cancel).toHaveBeenCalled());
    await screen.findByText("cancelled");
  });
  it("resumes GET-only after refresh and recovers polling errors", async () => {
    const api = runnerApi("ch3_idrid");
    const row = jobFor("ch3_idrid");
    sessionStorage.setItem(
      "ai-lab-v3-job:http://localhost:5000:ch3_idrid:cnn",
      row.job.job_id,
    );
    api.get.mockRejectedValueOnce(new Error("worker unavailable"));
    render(
      <ModelRunner
        api={api as unknown as ApiClient}
        overview={snapshot("ch3_idrid")}
        family="cnn"
      />,
    );
    await screen.findByRole("alert");
    fireEvent.click(screen.getByRole("button", { name: "Thử lại" }));
    await screen.findByTestId("comparison");
    expect(api.submit).not.toHaveBeenCalled();
  });
  it("reports a missing demo or rejected submit", async () => {
    const api = runnerApi("ch3_idrid");
    const data = snapshot("ch3_idrid");
    data.sample = null;
    const view = render(
      <ModelRunner
        api={api as unknown as ApiClient}
        overview={data}
        family="cnn"
      />,
    );
    expect(screen.getByText(/chưa có input chạy/)).toBeTruthy();
    view.unmount();
    api.submit.mockRejectedValueOnce(new Error("queue full"));
    render(
      <ModelRunner
        api={api as unknown as ApiClient}
        overview={snapshot("ch3_idrid")}
        family="cnn"
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Chạy cả 3/ }));
    expect((await screen.findByRole("alert")).textContent).toContain(
      "queue full",
    );
  });
});
describe("comparison and trace truthfulness", () => {
  it("does not describe non-neural KG pipelines as trained neural weights", () => {
    const row = jobFor("ch5_finqa");
    render(<Comparison job={row.job} details={row.details} />);
    expect(
      screen.queryByText(/Tên cột chỉ cách huấn luyện weights/),
    ).toBeNull();
  });
  it.each([
    "ch2_ames_housing",
    "ch2_cdc_diabetes",
    "ch3_idrid",
    "ch5_finqa",
    "ch5_wikidata_subgraphs",
    "ch6_diabetes_tasks",
  ])("renders outputs/citations/status %s", (dataset) => {
    const row = jobFor(dataset);
    render(<Comparison job={row.job} details={row.details} />);
    expect(screen.getAllByTestId("model-result")).toHaveLength(
      row.job.results.length,
    );
  });
  it("shows unavailable slots and invalid group without pretending to rank", () => {
    const row = jobFor("ch3_idrid");
    row.job.comparison_valid = false;
    row.job.results[0].prediction = null;
    row.job.results[0].error = { code: "artifact_unavailable" };
    render(<Comparison job={row.job} details={null} />);
    expect(screen.getByText(/Không xếp hạng/)).toBeTruthy();
    expect(screen.getByText(/artifact_unavailable/)).toBeTruthy();
  });
  it("renders actual parent IDs, zero node instrumentation and switches variants", () => {
    const row = jobFor("ch6_diabetes_tasks");
    render(<AgentTrace details={row.details} />);
    expect(screen.getAllByText(/Chưa instrument riêng/)).toHaveLength(2);
    const select = screen.getByRole("combobox");
    fireEvent.change(select, {
      target: { value: Object.keys(row.details.traces)[0] },
    });
    expect(screen.getByTestId("agent-trace").textContent).toContain("A0");
  });
  it("handles an empty trace", () => {
    render(<AgentTrace details={{}} />);
    expect(screen.getByText(/Chưa có agent trace/)).toBeTruthy();
  });
});
describe("historical results keep original metrics and null cost", () => {
  function apiFor() {
    return new ApiClient(
      "http://localhost:5000",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = new URL(String(input));
        let value;
        if (url.pathname.endsWith("/results")) value = fixture[url.pathname];
        else if (url.pathname === "/api/v3/runs")
          value = {
            data: registry.runs
              .filter(
                (row: { dataset_id: string }) =>
                  row.dataset_id === url.searchParams.get("dataset_id"),
              )
              .map((row: { run_id: string }) => ({
                ...row,
                split: row.run_id.split("_").pop(),
              })),
          };
        else if (url.pathname.startsWith("/api/v3/runs/")) {
          const row = registry.runs.find(
            (r: { run_id: string }) =>
              r.run_id === url.pathname.split("/").pop(),
          );
          value = {
            data: JSON.parse(
              readFileSync(`${root}/${row.record.path}`, "utf8"),
            ),
          };
        } else if (url.pathname.startsWith("/api/v3/artifacts/")) {
          const id = url.pathname.split("/")[4];
          return new Response(
            readFileSync(`${root}/${registry.public_artifacts[id].path}`),
          );
        }
        return new Response(JSON.stringify(value), {
          status: value ? 200 : 404,
        });
      }) as typeof fetch,
      sessionStorage,
    );
  }
  it.each([
    ["ch2_cdc_diabetes", "mlp", 2],
    ["ch4_household_power", "rnn", 4],
    ["ch5_finqa", "kg_rag", 5],
    ["ch5_wikidata_subgraphs", "kg_rag", 5],
    ["ch6_gold_tasks", "multi_agent", 6],
  ] as const)("loads saved output %s", async (dataset, family, chapter) => {
    render(
      <HistoricalResults
        api={apiFor()}
        dataset={dataset}
        family={family}
        chapter={chapter}
      />,
    );
    await waitFor(() =>
      expect(screen.queryAllByRole("status")).toHaveLength(0),
    );
    expect(screen.queryByRole("alert")).toBeNull();
    const comboboxes = screen.getAllByRole("combobox");
    for (const field of comboboxes) {
      const options = field.querySelectorAll("option");
      if (options.length > 1) {
        fireEvent.change(field, {
          target: { value: (options[1] as HTMLOptionElement).value },
        });
      }
    }
    if (chapter < 5)
      await waitFor(() =>
        expect(screen.queryAllByRole("status")).toHaveLength(0),
      );
  });
});
describe("presentation boundaries", () => {
  it("groups fenced JSON into an expandable structured example", () => {
    render(<Markdown text={'```json\n{"known_output":"iris-setosa"}\n```'} />);
    expect(
      screen.getByText("Ví dụ có cấu trúc · json").closest("details"),
    ).not.toBeNull();
  });
  it("renders markdown as escaped text and only safe links, tables, details", () => {
    render(
      <Markdown
        text={
          "# Title\n<script>bad()</script>\n[a](https://example.org) **bold** `code`\n|a|b|\n|--|--|\n|1|2|\n- item"
        }
      />,
    );
    expect(document.querySelector("script")).toBeNull();
    expect(screen.getByRole("link").getAttribute("rel")).toBe("noreferrer");
  });
  it("handles empty and long tables, no-number chart, flat fields and safe errors", () => {
    const view = render(
      <>
        <DataTable rows={[]} />
        <BarList data={{ a: "none" }} label="empty" />
        <ErrorPanel error="failure" />
      </>,
    );
    expect(screen.getByRole("alert").textContent).toContain("failure");
    view.unmount();
    render(
      <DataTable
        rows={Array.from({ length: 61 }, (_, n) => ({ n, missing: null }))}
      />,
    );
    expect(screen.getByText(/Hiển thị60\/61/)).toBeTruthy();
    expect(flatFields({ a: null, b: [], c: 0 })).toEqual({ a: null, c: 0 });
  });
  it("catches render failure without echoing source stack", () => {
    const Throw = () => {
      throw new Error("fixture_only");
    };
    const log = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <Boundary>
        <Throw />
      </Boundary>,
    );
    expect(screen.getByRole("alert").textContent).not.toContain("fixture_only");
    log.mockRestore();
  });
});
