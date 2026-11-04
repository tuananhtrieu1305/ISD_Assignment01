import { useState } from "react";
import type { Contract, Envelope, Model } from "./types";
import { ApiClient } from "./client";
import { useResource } from "./hooks";
import { displayValue } from "./presentation";
import {
  DataTable,
  Definition,
  ErrorPanel,
  Hash,
  JsonView,
  Loading,
  Note,
} from "./ui";
export default function FunctionComposition({
  api,
  models,
  family,
  intro,
}: {
  api: ApiClient;
  models: Model[];
  family: string;
  intro: string;
}) {
  const isNeural = ["mlp", "cnn", "rnn", "lstm"].includes(family);
  const available = models.filter((row) => row.family === family);
  const [selected, select] = useState("");
  const model =
    available.find((row) => row.model_id === selected) ?? available[0];
  const resource = useResource(
    api.base + "/contract/" + model?.model_id,
    async (signal) =>
      model
        ? (
            await api.get<Envelope<Contract>>(
              `/api/v3/models/${model.model_id}/contract`,
              signal,
            )
          ).data
        : null,
  );
  return (
    <section className="v3-surface" data-testid="function-composition">
      <span className="v3-kicker">HIỂU CÁCH MÔ HÌNH HOẠT ĐỘNG</span>
      <h2>Hợp hàm & giải thích từng bước</h2>
      <p className="v3-lead">{intro}</p>
      {!model ? (
        <Note>
          Không có checkpoint chạy ở chương lịch sử. Dữ liệu minh họa sự phát
          triển của AI, không phải thực nghiệm huấn luyện mới.
        </Note>
      ) : (
        <>
          <label className="v3-field">
            Implementation / pipeline
            <select
              value={model.model_id}
              onChange={(event) => select(event.target.value)}
            >
              {available.map((row) => (
                <option value={row.model_id} key={row.model_id}>
                  {row.implementation} · {row.backend}
                </option>
              ))}
            </select>
          </label>
          {resource.loading && <Loading />}
          {resource.error && (
            <ErrorPanel error={resource.error} retry={resource.retry} />
          )}
          {resource.value && (
            <>
              <p className="v3-flow">
                {resource.value.composition_plain ??
                  displayValue(resource.value.composition)}
              </p>
              <p>
                <code>F = f_L ∘ … ∘ f_1</code> — đọc từ đầu vào qua các bước ở
                trên để có đầu ra.{" "}
                {isNeural
                  ? "Không dùng activation/pooling để tăng số lớp học được."
                  : "Đây là pipeline phi thần kinh, không áp dụng cách đếm lớp mạng."}
              </p>
              <Definition
                values={{
                  "Backend huấn luyện (contract)": isNeural
                    ? resource.value.backend
                    : "Pipeline CPU phi thần kinh",
                  "Lớp học được": isNeural
                    ? (resource.value.layers?.filter(
                        (row) => row.parameter_count > 0,
                      ).length ?? null)
                    : "Không áp dụng",
                  "Tham số": isNeural
                    ? resource.value.parameter_count
                    : "Không áp dụng",
                }}
              />
              {resource.value.recurrent_unroll && (
                <JsonView
                  value={resource.value.recurrent_unroll}
                  label="Phép lặp theo thời gian / tầng"
                />
              )}
              <div className="v3-function-list">
                {resource.value.functions?.map((row, n) => (
                  <details key={row.id ?? n} open={n === 0}>
                    <summary>
                      <span className="v3-step-number">
                        {String(n + 1).padStart(2, "0")}
                      </span>
                      {row.role ?? row.name ?? row.id}
                    </summary>
                    <code>{row.signature}</code>
                    <Definition
                      values={{
                        "Đầu vào": row.input_shape ?? row.input,
                        "Đầu ra": row.output_shape ?? row.output,
                        "Tham số": row.parameters ?? null,
                        "Trường hợp biên": row.corner_case,
                      }}
                    />
                    {row.mapping && (
                      <DataTable
                        rows={Object.entries(row.mapping).map(
                          ([framework, call]) => ({ framework, call }),
                        )}
                      />
                    )}
                    {row.formula && (
                      <details>
                        <summary>Phép tính cốt lõi, giải thích & ví dụ</summary>
                        <p>
                          <code>{row.formula.expression}</code>
                        </p>
                        <p>{row.formula.plain_explanation}</p>
                        <p>{row.formula.example}</p>
                        <DataTable rows={row.formula.symbols} />
                      </details>
                    )}
                  </details>
                ))}
              </div>
              <p className="v3-muted">Contract đã khóa · hash</p>
              <Hash value={model.contract.sha256} />
              <JsonView
                value={resource.value}
                label="Contract nguyên bản và provenance"
              />
            </>
          )}
        </>
      )}
    </section>
  );
}
