import type { Model } from "./types";
import { ApiClient } from "./client";
import { useResource } from "./hooks";
import { DataTable, ErrorPanel, Hash, JsonView, Loading, Note } from "./ui";
export default function Deployment({
  api,
  models,
}: {
  api: ApiClient;
  models: Model[];
}) {
  const ready = useResource(api.base + "/deployment-ready", (signal) =>
    api.get<{ status: string; components: unknown[] }>("/ready", signal),
  );
  return (
    <section className="v3-surface" data-testid="deployment">
      <span className="v3-kicker">TRIỂN KHAI · MỤC NGẮN CUỐI CHƯƠNG</span>
      <h2>Từ checkpoint đến API</h2>
      <p>
        API: <code>{api.base}</code>
      </p>
      {ready.loading && <Loading />}
      {ready.error && <ErrorPanel error={ready.error} retry={ready.retry} />}
      {ready.value && (
        <p className="v3-badge success">Readiness: {ready.value.status}</p>
      )}
      <DataTable
        rows={models.map((row) => ({
          implementation: row.implementation,
          serving_backend: row.backend,
          status: row.status,
          reason: row.reason,
        }))}
      />
      <Note>
        CPU deploy dùng NumPy portable để phục vụ3weights huấn luyện độc lập.
        Local GPU native được cấu hình ở server, không phải nút đổi backend từ
        trình duyệt. Scratch luôn CPU. Cold-start không phải benchmark tốc độ
        framework.
      </Note>
      <p>
        Inference-only, không train trên Render. Một worker, job tuần tự,
        TTL30phút. Mất job sau redeploy là giới hạn đã khai báo. Không có gói
        cloud nào được tạo từ giao diện này.
      </p>
      <p>
        Giới hạn local CPU448MiB/60s, GPU4GiB/300s; monitor PSS lấy mẫu không
        gồm OS/master/VRAM và không bảo đảm Render free-tier luôn đủ. Không dùng
        cho chẩn đoán hoặc tư vấn đầu tư.
      </p>
      {models.map((row) => (
        <div className="v3-artifact-link" key={row.model_id}>
          <strong>{row.model_id}</strong>
          <Hash value={row.contract.sha256} />
        </div>
      ))}
      <a
        href={`${api.base}/api/v3/openapi.json`}
        target="_blank"
        rel="noreferrer"
      >
        OpenAPI V3 · hợp đồng đang phục vụ ↗
      </a>
      <JsonView value={ready.value} label="Component readiness chi tiết" />
    </section>
  );
}
