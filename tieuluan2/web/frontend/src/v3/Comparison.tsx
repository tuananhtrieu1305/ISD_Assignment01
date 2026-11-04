import type { Doc, Job, Slot } from "./types";
import {
  displayValue,
  record,
  records,
  safeLink,
  probabilityWidth,
} from "./presentation";
import { Definition, Hash, JsonView, Note } from "./ui";
function Prediction({ slot }: { slot: Slot }) {
  const prediction = slot.prediction;
  if (!prediction)
    return (
      <Note>
        Chưa có dự đoán · {displayValue(slot.error?.code ?? slot.status)}
      </Note>
    );
  if (prediction.kind === "classification")
    return (
      <>
        <strong className="v3-output">{displayValue(prediction.label)}</strong>
        <p className="v3-muted">
          Xác suất mô hình, không phải độ chắc chắn y khoa
        </p>
        {records(prediction.probabilities).map((row, index) => (
          <div className="v3-probability" key={index}>
            <span>{displayValue(row.label ?? row.class)}</span>
            <strong>
              {Number(row.value).toLocaleString("vi-VN", {
                style: "percent",
                maximumFractionDigits: 2,
              })}
            </strong>
            <span className="v3-probability-track">
              <span style={{ width: probabilityWidth(Number(row.value)) }} />
            </span>
          </div>
        ))}
      </>
    );
  if (prediction.kind === "regression")
    return (
      <div className="v3-forecast">
        {(prediction.values as number[]).map((value, n) => (
          <div key={n}>
            <small>
              Horizon{displayValue((prediction.horizons as number[])[n])}
            </small>
            <strong>
              {displayValue(value)}{" "}
              <small>{displayValue(prediction.unit)}</small>
            </strong>
          </div>
        ))}
      </div>
    );
  return (
    <>
      <strong>
        {prediction.abstained
          ? "Từ chối có lý do"
          : "Câu trả lời dựa trên snapshot"}
      </strong>
      <p className="v3-answer">{displayValue(prediction.text)}</p>
      {records(prediction.citations).map((row, n) => (
        <div className="v3-citation" key={n}>
          <a
            href={safeLink(String(row.source_url))}
            target="_blank"
            rel="noreferrer"
          >
            Nguồn bằng chứng ↗
          </a>
          <p>{displayValue(row.locator)}</p>
          <Hash value={String(row.source_sha256)} />
        </div>
      ))}
    </>
  );
}
export default function Comparison({
  job,
  details,
}: {
  job: Job;
  details: Doc | null;
}) {
  return (
    <section className="v3-comparison" data-testid="comparison">
      <div className="v3-section-heading">
        <h2>Kết quả cùng một input</h2>
        <span
          className={`v3-badge ${job.status === "succeeded" ? "success" : ""}`}
        >
          {job.status}
        </span>
      </div>
      <Note>
        {job.comparison_valid
          ? "Cùng nhóm so sánh đã khóa; không xếp hạng chất lượng từ một mẫu demo."
          : "Chưa có so sánh hợp lệ. Không xếp hạng các slot thiếu hoặc khác nhóm."}{" "}
        {job.comparison_reason}
        {job.results.length > 0 &&
          job.results.every((slot) =>
            ["scratch", "keras", "pytorch"].includes(slot.implementation),
          ) &&
          job.results.every((slot) => slot.actual_backend === "numpy") && (
            <p>
              Tên cột chỉ cách huấn luyện weights. API hiện suy luận bằng
              NumPy/CPU; không phải phép đo tốc độ native Keras/PyTorch.
            </p>
          )}
        <p>
          Kết quả thuộc job <code>{job.job_id}</code> và input hash đã gửi. Khi
          chỉnh form hoặc khôi phục phiên, form có thể khác job trước; chỉ nút
          Chạy mới tạo kết quả cho input mới.
        </p>
      </Note>
      <div className="v3-result-grid">
        {job.results.map((slot) => (
          <article
            className="v3-result"
            key={slot.implementation}
            data-testid="model-result"
          >
            <div className="v3-section-heading">
              <h3>{slot.implementation}</h3>
              <span className="v3-muted">{slot.status}</span>
            </div>
            <p className="v3-runtime">
              {slot.actual_backend ?? "—"} / {slot.actual_device ?? "—"}
            </p>
            <Prediction slot={slot} />
            <p className="v3-muted">
              Forward batch1:{displayValue(slot.inference_ms)}ms · không phải
              benchmark accuracy
            </p>
            <details>
              <summary>Checkpoint / input / comparison hash</summary>
              <p>{slot.model_id}</p>
              <Hash value={slot.artifact_sha256} />
              <Hash value={slot.input_sha256} />
              <Hash value={slot.comparison_group_sha256} />
            </details>
          </article>
        ))}
      </div>
      {details && (
        <>
          <Definition values={record(details.serving_runtime)} />
          <JsonView
            value={details.serving_telemetry}
            label="Telemetry serving · phạm vi và budget thực"
          />
          {details.warning && <Note>{displayValue(details.warning)}</Note>}
          {details.evidence && (
            <JsonView
              value={details.evidence}
              label="Evidence retrieval theo pipeline"
            />
          )}
          {details.graph_paths && (
            <JsonView
              value={details.graph_paths}
              label="Đường nối trên knowledge graph"
            />
          )}
          {details.entity && (
            <>
              <h3>Wikidata · structural browser, không QA benchmark</h3>
              <JsonView
                value={details.entity}
                label="Entity / claims / revision / provenance"
              />
            </>
          )}
        </>
      )}
    </section>
  );
}
