import { afterEach, describe, expect, it, vi } from "vitest";
import { webcrypto } from "node:crypto";
import { readFileSync } from "node:fs";
import { chapters } from "./catalog";
import { resolveSelection, selectionUrl, sections } from "./routing";
import { ApiClient, ApiError, clientToken, validateBase } from "./client";
import {
  displayValue,
  csvRows,
  filteredRows,
  probabilityWidth,
  safeLink,
} from "./presentation";
afterEach(() => vi.unstubAllGlobals());

describe("URL contract", () => {
  it("matches all18dataset IDs and six chapters from the frozen serving registry", () => {
    const registry = JSON.parse(
      readFileSync(
        "../../artifacts/manifests/phase32/registry_v3.json",
        "utf8",
      ),
    );
    expect(
      chapters.map((c) => ({
        chapter: c.chapter,
        dataset_ids: [...c.datasets].sort(),
      })),
    ).toEqual(
      registry.chapters.map(
        (c: { chapter: number; dataset_ids: string[] }) => ({
          chapter: c.chapter,
          dataset_ids: c.dataset_ids.sort(),
        }),
      ),
    );
  });
  it.each(["/ml", "/cnn", "/rnn", "/rag", "/agents"])(
    "keeps dataset and section for %s",
    (route) => {
      const a = resolveSelection(route, new URLSearchParams());
      expect(a.error).toBeNull();
      for (const section of sections) {
        const b = resolveSelection(
          route,
          new URLSearchParams(selectionUrl(a, { section }).split("?")[1]),
        );
        expect(b.section).toBe(section);
        expect(b.dataset).toBe(a.dataset);
      }
    },
  );
  it("keeps RNN/LSTM and rejects cross-chapter datasets instead of silent fallback", () => {
    expect(
      resolveSelection("/rnn", new URLSearchParams("family=lstm")).family,
    ).toBe("lstm");
    expect(
      resolveSelection("/cnn", new URLSearchParams("dataset=ch2_cdc_diabetes"))
        .error,
    ).toBeTruthy();
    expect(
      resolveSelection("/rnn", new URLSearchParams("family=gru")).error,
    ).toBeTruthy();
    expect(
      resolveSelection("/cnn", new URLSearchParams("section=bogus")).error,
    ).toBeTruthy();
    expect(
      resolveSelection("/unknown", new URLSearchParams()).error,
    ).toBeTruthy();
    expect(
      resolveSelection("/cnn", new URLSearchParams("section=data&section=run"))
        .error,
    ).toBeTruthy();
  });
});
describe("safe presentation and comparable historical rows", () => {
  it("preserves missing cost, zero, arrays and text without invented metrics", () => {
    expect(displayValue(null)).toBe("Không có số đo");
    expect(displayValue(0)).toBe("0");
    expect(displayValue(true)).toBe("Có");
    expect(displayValue(["a", "b"])).toContain("a");
    expect(displayValue({ x: 1 })).toContain("x");
    expect(displayValue(undefined)).toBe("Không có số đo");
  });
  it("parses quoted CSV and filters before comparing", () => {
    const rows = csvRows(
      'dataset_id,family,unit,note\r\na,cnn,USD,"one,two"\r\nb,cnn,kW,"say ""hi"""\r\n',
    );
    expect(rows[0].note).toBe("one,two");
    expect(rows[1].note).toBe('say "hi"');
    expect(filteredRows(rows, "a", "cnn", {})).toHaveLength(1);
    expect(filteredRows(rows, "a", "rnn", {})).toHaveLength(0);
    expect(
      filteredRows(
        [{ domain: "finance" }, { domain: "medical" }],
        "ch5_finqa",
        "kg_rag",
        { domain: "finance" },
      ),
    ).toHaveLength(1);
  });
  it("does not accept javascript URLs or probability bars over 100 percent", () => {
    expect(safeLink("javascript:alert(1)")).toBeUndefined();
    expect(safeLink("https://example.org")).toBeTruthy();
    expect(probabilityWidth(1.4)).toBe("100%");
    expect(probabilityWidth(-1)).toBe("0%");
    expect(probabilityWidth(Number.NaN)).toBe("0%");
    expect(safeLink("not a URL")).toBeUndefined();
    expect(safeLink("https://user:pass@example.org")).toBeUndefined();
    expect(displayValue(Number.NaN)).toBe("Không có số đo");
    expect(() => csvRows('a\n"unfinished')).toThrow();
  });
});
describe("capability-bound API client", () => {
  it("verifies downloaded artifact SHA and rejects mismatched bytes/non-public artifacts", async () => {
    vi.stubGlobal("crypto", webcrypto);
    const text = '{"a":1}';
    const hash = Array.from(
      new Uint8Array(
        await webcrypto.subtle.digest(
          "SHA-256",
          new TextEncoder().encode(text),
        ),
      ),
      (n) => n.toString(16).padStart(2, "0"),
    ).join("");
    const client = new ApiClient(
      "http://localhost:5000",
      vi.fn().mockImplementation(async () => new Response(text)),
      sessionStorage,
    );
    expect(await client.artifact(hash)).toBe(text);
    await expect(client.artifact("0".repeat(64))).rejects.toMatchObject({
      code: "artifact_hash_mismatch",
    });
    expect(() => client.artifactUrl("../escape")).toThrow();
    const missing = new ApiClient(
      "http://localhost:5000",
      vi.fn().mockResolvedValue(new Response("", { status: 404 })),
      sessionStorage,
    );
    await expect(missing.artifact(hash)).rejects.toMatchObject({
      code: "artifact_unavailable",
    });
    const huge = new ApiClient(
      "http://localhost:5000",
      vi
        .fn()
        .mockResolvedValue(new Response(new Uint8Array(4 * 1024 ** 2 + 1))),
      sessionStorage,
    );
    await expect(huge.artifact(hash)).rejects.toMatchObject({
      code: "artifact_too_large",
    });
  });
  it("handles invalid JSON, generic HTTP errors, abort and malformed IDs", async () => {
    const bad = new ApiClient(
      "http://localhost:5000",
      vi.fn().mockResolvedValue(new Response("not JSON")),
      sessionStorage,
    );
    await expect(bad.get("/health")).rejects.toMatchObject({
      code: "invalid_response",
    });
    const http = new ApiClient(
      "http://localhost:5000",
      vi.fn().mockResolvedValue(new Response("{}", { status: 404 })),
      sessionStorage,
    );
    await expect(http.get("/health")).rejects.toMatchObject({
      code: "http_error",
      retryable: false,
    });
    const abort = new ApiClient(
      "http://localhost:5000",
      vi.fn().mockRejectedValue(new DOMException("aborted", "AbortError")),
      sessionStorage,
    );
    await expect(abort.get("/health")).rejects.toMatchObject({
      name: "AbortError",
    });
    await expect(abort.cancel("../bad")).rejects.toThrow();
  });
  it("calls fetch with the global receiver required by native Window.fetch", async () => {
    const nativeLike = vi.fn(function (this: unknown) {
      if (this !== globalThis) throw new TypeError("Illegal invocation");
      return Promise.resolve(new Response("{}"));
    });
    await expect(
      new ApiClient("http://localhost:5000", nativeLike, sessionStorage).get(
        "/health",
      ),
    ).resolves.toEqual({});
  });
  it("matches cancel schema and hashes public artifact bytes", async () => {
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
  it("normalizes only http/https API origins without embedded credentials", () => {
    expect(validateBase("http://localhost:5000/")).toBe(
      "http://localhost:5000",
    );
    for (const value of [
      "javascript:alert(1)",
      "https://secret@example.com",
      "https://x.test/path",
      "https://x.test/?secret=x",
    ])
      expect(() => validateBase(value)).toThrow();
  });
  it("stores 24 random bytes in session storage only and isolates API origins", () => {
    sessionStorage.clear();
    const a = clientToken(sessionStorage, "http://localhost:5000");
    expect(a).toMatch(/^[a-f0-9]{48}$/);
    expect(clientToken(sessionStorage, "http://localhost:5000")).toBe(a);
    expect(clientToken(sessionStorage, "http://localhost:5001")).not.toBe(a);
  });
  it("uses owner and idempotency headers without leaking tokens in the URL", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ job_id: "job_fixture" }), {
        status: 202,
      }),
    );
    const client = new ApiClient(
      "http://localhost:5000",
      fetcher,
      sessionStorage,
    );
    await client.submit({ dataset_id: "fixture" }, "idem_fixture");
    const [url, init] = fetcher.mock.calls[0];
    expect(url).toBe("http://localhost:5000/api/v3/comparisons");
    expect(new Headers(init.headers).get("X-Client-Token")).toHaveLength(48);
    expect(new Headers(init.headers).get("Idempotency-Key")).toBe(
      "idem_fixture",
    );
    expect(init.credentials).toBe("omit");
    await expect(client.get("/evil?X-Client-Token=secret")).rejects.toThrow();
  });
  it("keeps structured retryable errors and refuses external polling", async () => {
    const client = new ApiClient(
      "http://localhost:5000",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: { code: "worker_unavailable", retryable: true },
            request_id: "req_fixture",
          }),
          { status: 503 },
        ),
      ),
      sessionStorage,
    );
    await expect(client.get("/ready")).rejects.toMatchObject({
      code: "worker_unavailable",
      status: 503,
      retryable: true,
    });
    await expect(client.get("https://other.test/job")).rejects.toThrow();
    expect(new ApiError("network_error", 0).message).toBeTruthy();
  });
});
