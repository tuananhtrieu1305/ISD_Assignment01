export class ApiError extends Error {
  constructor(
    public code: string,
    public status: number,
    public retryable = false,
    public requestId = "",
  ) {
    super(`Không thể xử lý yêu cầu (${code}).`);
  }
}
export function validateBase(value: string): string {
  const url = new URL(value);
  if (
    !["http:", "https:"].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    url.pathname !== "/"
  )
    throw new Error(
      "API cần một origin HTTP/HTTPS không chứa path, token hoặc mật khẩu.",
    );
  return url.origin;
}
export function randomKey(): string {
  return Array.from(crypto.getRandomValues(new Uint8Array(24)), (n) =>
    n.toString(16).padStart(2, "0"),
  ).join("");
}
export function clientToken(storage: Storage, base: string): string {
  const key = `ai-lab-v3-owner:${base}`;
  const saved = storage.getItem(key);
  if (saved && /^[a-f0-9]{48}$/.test(saved)) return saved;
  const token = randomKey();
  storage.setItem(key, token);
  return token;
}
export class ApiClient {
  readonly base: string;
  constructor(
    base: string,
    private fetcher: typeof fetch = fetch,
    private storage: Storage = sessionStorage,
  ) {
    this.base = validateBase(base);
    this.fetcher = fetcher.bind(globalThis);
  }
  async get<T>(path: string, signal?: AbortSignal): Promise<T> {
    return this.request(path, { signal });
  }
  async submit<T>(body: unknown, key: string): Promise<T> {
    return this.request("/api/v3/comparisons", {
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Idempotency-Key": key },
    });
  }
  async cancel<T>(id: string): Promise<T> {
    if (!/^job_[a-f0-9]+$/.test(id)) throw new Error("Job ID không hợp lệ");
    return this.request(`/api/v3/jobs/${id}/cancellations`, {
      method: "POST",
      body: JSON.stringify({ reason: "user_cancelled" }),
    });
  }
  artifactUrl(hash: string): string {
    if (!/^[a-f0-9]{64}$/.test(hash))
      throw new Error("Hash artifact không hợp lệ");
    return `${this.base}/api/v3/artifacts/asset_${hash.slice(0, 24)}/content`;
  }
  async artifact(hash: string, signal?: AbortSignal): Promise<string> {
    const response = await this.fetcher(this.artifactUrl(hash), {
      credentials: "omit",
      cache: "no-store",
      signal,
    });
    if (!response.ok)
      throw new ApiError("artifact_unavailable", response.status);
    const buffer = await response.arrayBuffer();
    if (buffer.byteLength > 4 * 1024 ** 2)
      throw new ApiError("artifact_too_large", 413);
    const actual = Array.from(
      new Uint8Array(await crypto.subtle.digest("SHA-256", buffer)),
      (n) => n.toString(16).padStart(2, "0"),
    ).join("");
    if (actual !== hash) throw new ApiError("artifact_hash_mismatch", 503);
    return new TextDecoder().decode(buffer);
  }
  private async request<T>(path: string, init: RequestInit): Promise<T> {
    if (
      !/^\/(health|ready)$|^\/api\/v3\/[a-zA-Z0-9_/?=&.-]+$/.test(path) ||
      path.includes("..") ||
      /token|secret/i.test(path)
    )
      throw new Error("Đường dẫn API không hợp lệ");
    const headers = new Headers(init.headers);
    headers.set("Content-Type", "application/json");
    if (
      path.includes("/jobs/") ||
      path.includes("/agent-traces/") ||
      init.method === "POST"
    )
      headers.set("X-Client-Token", clientToken(this.storage, this.base));
    let response: Response;
    try {
      response = await this.fetcher(this.base + path, {
        ...init,
        headers,
        credentials: "omit",
        cache: "no-store",
      });
    } catch (error) {
      if (
        error &&
        typeof error === "object" &&
        "name" in error &&
        error.name === "AbortError"
      )
        throw error;
      throw new ApiError("network_error", 0, true);
    }
    let value;
    try {
      value = await response.json();
    } catch {
      throw new ApiError("invalid_response", response.status);
    }
    if (!response.ok)
      throw new ApiError(
        value.error?.code ?? "http_error",
        response.status,
        value.error?.retryable ?? false,
        value.request_id ?? "",
      );
    return value as T;
  }
}
