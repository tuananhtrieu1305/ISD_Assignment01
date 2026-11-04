import { useState } from "react";
import { ApiClient } from "./client";
import { useResource } from "./hooks";
import { csvRows, filteredRows, record, records } from "./presentation";
import type { Doc, Envelope, ResultIndex } from "./types";
import {
  BarList,
  DataTable,
  Definition,
  ErrorPanel,
  Hash,
  JsonView,
  Loading,
  Note,
} from "./ui";
type Run = {
  run_id: string;
  dataset_id: string;
  record: { path: string; sha256: string };
  split: string;
};
export default function HistoricalResults({
  api,
  dataset,
  family,
  chapter,
}: {
  api: ApiClient;
  dataset: string;
  family: string;
  chapter: number;
}) {
  const [split, setSplit] = useState("test");
  const [seed, setSeed] = useState("42");
  const [metricName, setMetric] = useState("");
  const [archiveIndex, setArchiveIndex] = useState(0);
  const index = useResource(
    `${api.base}/${dataset}/results`,
    async (signal) =>
      (
        await api.get<Envelope<ResultIndex>>(
          `/api/v3/datasets/${dataset}/results`,
          signal,
        )
      ).data,
  );
  const runs = useResource(
    `${api.base}/${dataset}/${family}/${split}/${seed}/metrics`,
    async (signal) => {
      if (chapter >= 5) return [];
      const list = await api.get<Envelope<Run[]>>(
        `/api/v3/runs?dataset_id=${dataset}&page_size=100`,
        signal,
      );
      const selected = list.data.filter(
        (row) =>
          row.split === split &&
          new RegExp(`_s${seed}(?:_|$)`).test(row.run_id) &&
          !["_mlp_", "_cnn_", "_rnn_", "_lstm_"].some(
            (name) => name !== `_${family}_` && row.run_id.includes(name),
          ) &&
          !row.run_id.includes("_fold"),
      );
      return Promise.all(
        selected.map(async (row) => ({
          descriptor: row,
          metric: (
            await api.get<Envelope<Doc>>(`/api/v3/runs/${row.run_id}`, signal)
          ).data,
        })),
      );
    },
  );
  const asset =
    index.value?.artifacts[archiveIndex] ?? index.value?.artifacts[0];
  const archive = useResource(
    `${api.base}/${chapter >= 5 ? asset?.sha256 : "no-archive"}`,
    async (signal) =>
      chapter >= 5 && asset ? api.artifact(asset.sha256, signal) : null,
  );
  const rows = runs.value ?? [];
  const available = [
    ...new Set(
      rows.flatMap((row) =>
        records(row.metric.metrics).map(
          (m) => `${m.name} | ${m.unit} | h=${m.horizon ?? "—"}`,
        ),
      ),
    ),
  ];
  const selectedMetric = available.includes(metricName)
    ? metricName
    : available[0];
  const comparison = rows.flatMap((row) =>
    records(row.metric.metrics)
      .filter(
        (m) =>
          `${m.name} | ${m.unit} | h=${m.horizon ?? "—"}` === selectedMetric,
      )
      .map((m) => ({
        model: row.descriptor.run_id,
        value: m.value,
        unit: m.unit,
        horizon: m.horizon,
        undefined_reason: m.undefined_reason,
      })),
  );
  return (
    <section className="v3-surface" data-testid="historical-results">
      <span className="v3-kicker">BENCHMARK ĐÃ LƯU · KHÔNG CHẠY LẠI TEST</span>
      <h2>Kết quả thực nghiệm</h2>
      <Note>
        Không phải kết quả của input vừa nhập. Các bảng này đến từ thực nghiệm
        offline đã khóa. Không gộp khác dataset, split, đơn vị hoặc horizon;
        không suy mô hình tốt hơn từ một lần demo.
      </Note>
      {index.error && <ErrorPanel error={index.error} retry={index.retry} />}
      {index.value && <p className="v3-muted">{index.value.scope}</p>}
      {chapter < 5 ? (
        <>
          <div className="v3-filter-row">
            <label className="v3-field">
              Tập đánh giá
              <select
                value={split}
                onChange={(event) => setSplit(event.target.value)}
              >
                <option value="test">TEST đã lưu</option>
                <option value="validation">Validation đã lưu</option>
              </select>
            </label>
            <label className="v3-field">
              Seed kết quả đã lưu
              <select
                value={seed}
                onChange={(event) => setSeed(event.target.value)}
              >
                <option value="42">42 · mặc định</option>
                <option value="17">17</option>
                <option value="73">73</option>
              </select>
            </label>
            <label className="v3-field">
              Metric / đơn vị / horizon
              <select
                value={selectedMetric ?? ""}
                onChange={(event) => setMetric(event.target.value)}
              >
                {available.map((name) => (
                  <option key={name}>{name}</option>
                ))}
              </select>
            </label>
          </div>
          <p>
            Bảng theo seed {seed}; deployment luôn dùng seed42 đã khóa, không
            đổi theo TEST. Baseline chỉ ở kết quả offline. Mean/std ba seed xem
            artifact gốc bên dưới.
          </p>
          {runs.loading && <Loading />}
          {runs.error && <ErrorPanel error={runs.error} retry={runs.retry} />}
          {!runs.loading && <DataTable rows={comparison} />}
          {comparison.some(
            (row) => typeof row.value === "number" && row.value < 0,
          ) ? (
            <Note>
              Metric có giá trị âm; dùng bảng đầy đủ, không vẽ trục0 làm mất các
              giá trị này.
            </Note>
          ) : (
            <BarList
              data={Object.fromEntries(
                comparison
                  .filter(
                    (row) =>
                      typeof row.value === "number" &&
                      Number.isFinite(row.value),
                  )
                  .map((row) => [
                    row.model.replace(dataset + "_", ""),
                    row.value,
                  ]),
              )}
              label={`${selectedMetric ?? "Metric"} · ${split} · seed${seed} · không gộp đơn vị/horizon`}
            />
          )}
          <h3>Chi phí train và benchmark offline · tách biệt serving</h3>
          <DataTable
            rows={rows.map((row) => ({
              model: row.descriptor.run_id,
              ...record(row.metric.efficiency),
            }))}
          />
          <Note>
            Null là không có số đo, không thay bằng0. Power/RNN/PyTorch/seed17
            phục hồi giữ nguyên chi phí train/RAM/VRAM=null; nhóm chất lượngn3,
            chi phín2. Không so CPU portable với timing native framework.
          </Note>
          {rows.map((row) => (
            <details key={row.descriptor.run_id}>
              <summary>Provenance · {row.descriptor.run_id}</summary>
              <Hash value={row.descriptor.record.sha256} />
              <JsonView
                value={row.metric}
                label="Metric + config/split/code/env/device gốc"
              />
            </details>
          ))}
        </>
      ) : (
        <>
          {index.value?.live_demo_equivalent_to_historical_benchmark ===
            false && (
            <Note>
              Demo hỏi tự do/compact không tương đương benchmark
              candidate-per-split lịch sử. Wikidata chỉ structural statistics,
              không QA scorecard.
            </Note>
          )}
          {asset && (
            <label className="v3-field">
              Bảng kết quả đã khóa
              <select
                value={archiveIndex}
                onChange={(event) =>
                  setArchiveIndex(Number(event.target.value))
                }
              >
                {index.value?.artifacts.map((item, n) => (
                  <option value={n} key={item.path}>
                    {item.path.split("/").pop()}
                  </option>
                ))}
              </select>
            </label>
          )}
          {archive.loading && <Loading />}
          {archive.error && (
            <ErrorPanel error={archive.error} retry={archive.retry} />
          )}
          {archive.value &&
            asset &&
            (asset.path.endsWith(".csv") ? (
              <DataTable
                rows={filteredRows(
                  csvRows(archive.value),
                  dataset,
                  family,
                  index.value?.row_filter_hint ?? {},
                )}
              />
            ) : (
              <JsonView
                value={JSON.parse(archive.value)}
                label="Bảng JSON gốc · giữ scope/domain/unit trong cấu trúc"
              />
            ))}
        </>
      )}
      <details>
        <summary>Tải artifact gốc, hash & phạm vi bảng chung</summary>
        <p>{index.value?.cost_scope}</p>
        {index.value?.artifacts.map((item) => (
          <div className="v3-artifact-link" key={item.path}>
            <a
              href={api.artifactUrl(item.sha256)}
              target="_blank"
              rel="noreferrer"
            >
              {item.path.split("/").pop()} ↗
            </a>
            <Hash value={item.sha256} />
          </div>
        ))}
        <Definition values={index.value?.row_filter_hint ?? {}} />
      </details>
    </section>
  );
}
