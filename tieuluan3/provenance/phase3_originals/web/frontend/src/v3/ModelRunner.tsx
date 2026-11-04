import { useEffect, useRef, useState } from "react";
import { ApiClient, randomKey } from "./client";
import type {
  ComparisonRequest,
  Doc,
  Envelope,
  Job,
  Overview,
  RequestInput,
} from "./types";
import { ErrorPanel, JsonView, Loading, Note } from "./ui";
import Comparison from "./Comparison";
import AgentTrace from "./AgentTrace";

export default function ModelRunner({
  api,
  overview,
  family,
}: {
  api: ApiClient;
  overview: Overview;
  family: string;
}) {
  const sample = overview.sample;
  const initial = sample?.request.input;
  const [input, setInput] = useState<RequestInput | null>(
    initial ? structuredClone(initial) : null,
  );
  const [sequence, setSequence] = useState(
    JSON.stringify(initial?.values ?? [], null, 2),
  );
  const [error, setError] = useState<unknown>(null);
  const [submitting, setSubmitting] = useState(false);
  const storageKey = `ai-lab-v3-job:${api.base}:${overview.dataset_id}:${family}`;
  const [jobId, setJobId] = useState(
    () => sessionStorage.getItem(storageKey) ?? "",
  );
  const [job, setJob] = useState<Job | null>(null);
  const [details, setDetails] = useState<Doc | null>(null);
  const [pollRevision, retryPoll] = useState(0);
  const alive = useRef(true);
  const locked = useRef(false);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  useEffect(() => {
    if (!jobId) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    const poll = async () => {
      try {
        const next = await api.get<Job>(
          `/api/v3/jobs/${jobId}`,
          controller.signal,
        );
        if (!active) return;
        setJob(next);
        setError(null);
        if (["queued", "running"].includes(next.status))
          timer = setTimeout(poll, 1100);
        else {
          const extra = await api.get<Envelope<Doc>>(
            `/api/v3/jobs/${jobId}/details`,
            controller.signal,
          );
          if (active) setDetails(extra.data);
        }
      } catch (reason) {
        if (active) setError(reason);
      }
    };
    void poll();
    return () => {
      active = false;
      controller.abort();
      clearTimeout(timer);
    };
  }, [api, jobId, pollRevision]);
  const running =
    submitting ||
    (!!jobId && (!job || ["queued", "running"].includes(job.status)) && !error);
  async function submit() {
    if (!sample || !input || locked.current) return;
    locked.current = true;
    setError(null);
    setSubmitting(true);
    try {
      const next = { ...input };
      if (next.kind === "sequence") next.values = JSON.parse(sequence);
      const request: ComparisonRequest = {
        ...sample.request,
        family,
        input: next,
      };
      const accepted = await api.submit<{ job_id: string }>(
        request,
        randomKey(),
      );
      if (alive.current) {
        sessionStorage.setItem(storageKey, accepted.job_id);
        setJob(null);
        setDetails(null);
        setJobId(accepted.job_id);
      }
    } catch (reason) {
      if (alive.current)
        setError(
          reason instanceof SyntaxError
            ? new Error("Chuỗi cần JSON hợp lệ. Không có job nào được gửi.")
            : reason,
        );
    } finally {
      locked.current = false;
      if (alive.current) setSubmitting(false);
    }
  }
  async function upload(file: File | undefined) {
    if (!file || !input) return;
    if (
      !["image/png", "image/jpeg"].includes(file.type) ||
      !/\.(png|jpe?g)$/i.test(file.name) ||
      file.size > 4_500_000
    ) {
      setError(new Error("Chỉ nhận PNG/JPEG tối đa4,5MB."));
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      if (alive.current)
        setInput({
          ...input,
          data: String(reader.result).split(",")[1],
          media_type: file.type,
          encoding: "base64",
        });
    };
    reader.readAsDataURL(file);
  }
  if (!input || !sample)
    return <Note>Dataset này chưa có input chạy. Không tạo dự đoán giả.</Note>;
  return (
    <section className="v3-runner" data-testid="model-runner">
      <div className="v3-input-panel v3-surface">
        <span className="v3-kicker">01 / CHUẨN BỊ INPUT</span>
        <h2>Chạy cùng một đầu vào</h2>
        <p>
          Mẫu {sample.input_split}: <code>{sample.sample_id}</code>
        </p>
        <Note>
          {overview.chapter < 5
            ? "Chỉ inference. Seed42 đã chọn trước; "
            : "Chỉ demo trên pipeline/config đã khóa; "}
          các implementation chạy tuần tự trong cùng job để tiết kiệm RAM. Không
          train trên web.
        </Note>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void submit();
          }}
        >
          {input.kind === "tabular" && (
            <details open className="v3-feature-fields">
              <summary>
                {Object.keys(input.features ?? {}).length}đặc trưng · có thể
                chỉnh sửa
              </summary>
              {Object.entries(input.features ?? {}).map(([name, value]) => (
                <label className="v3-field" key={name}>
                  {name}
                  <input
                    type={typeof value === "number" ? "number" : "text"}
                    step="any"
                    value={value ?? ""}
                    onChange={(event) =>
                      setInput({
                        ...input,
                        features: {
                          ...input.features,
                          [name]:
                            event.target.value === ""
                              ? null
                              : typeof value === "number"
                                ? Number(event.target.value)
                                : event.target.value,
                        },
                      })
                    }
                  />
                </label>
              ))}
            </details>
          )}
          {input.kind === "image" && (
            <>
              <img
                className="v3-upload-preview"
                src={`data:${String(input.media_type)};base64,${String(input.data)}`}
                alt="Ảnh sẽ dùng chung cho ba mô hình"
              />
              <label className="v3-field">
                Chọn ảnh PNG/JPEG
                <input
                  type="file"
                  accept="image/png,image/jpeg"
                  onChange={(event) => void upload(event.target.files?.[0])}
                />
              </label>
              <p className="v3-muted">
                Server áp dụng đúng preprocessing đã khóa. IDRiD quality thấp,
                không dùng chẩn đoán.
              </p>
            </>
          )}
          {input.kind === "sequence" && (
            <>
              <label className="v3-field">
                Cửa sổ chuỗi · JSON hàng×đặc trưng
                <textarea
                  rows={10}
                  value={sequence}
                  onChange={(event) => setSequence(event.target.value)}
                  spellCheck={false}
                />
              </label>
              <p className="v3-muted">
                Giữ đúng số bước/cột và thứ tự từ mẫu. Không trộn quốc gia BIS;
                không thêm thông tin tương lai.
              </p>
              <JsonView value={input.as_of} label="Mốc as_of đã khóa" />
            </>
          )}
          {input.kind === "question" && (
            <>
              <label className="v3-field">
                {overview.chapter === 6
                  ? "Tác vụ có record ID (giữ ID của mẫu)"
                  : overview.dataset_id.includes("wikidata")
                    ? "Entity ID từ snapshot, ví dụ Q12206"
                    : "Câu hỏi (dữ liệu nguồn tiếng Anh)"}
                <textarea
                  rows={4}
                  maxLength={500}
                  value={input.text ?? ""}
                  onChange={(event) =>
                    setInput({ ...input, text: event.target.value })
                  }
                />
              </label>
              <p className="v3-muted">
                {overview.chapter === 6
                  ? "So sánh A0/A1/A2 xác định, không hỏi đáp tự do."
                  : "Demo compact khác benchmark QA lịch sử; Wikidata chỉ duyệt đồ thị."}
              </p>
            </>
          )}
          <div className="v3-actions">
            <button className="v3-button" disabled={running} type="submit">
              {running
                ? "Đang xử lý…"
                : overview.chapter === 5
                  ? "Chạy B0–B4"
                  : overview.chapter === 6
                    ? "So sánh A0 / A1 / A2"
                    : "Chạy cả 3 mô hình"}{" "}
              <span aria-hidden="true">↗</span>
            </button>
            <button
              type="button"
              className="v3-button secondary"
              disabled={running}
              onClick={() => {
                setInput(structuredClone(sample.request.input));
                setSequence(
                  JSON.stringify(sample.request.input.values ?? [], null, 2),
                );
                setError(null);
              }}
            >
              Mẫu TRAIN
            </button>
          </div>
        </form>
        <JsonView value={input} label="Kiểm tra request input" />
      </div>
      <div className="v3-output-panel">
        <span className="v3-kicker">02 / QUAN SÁT KẾT QUẢ</span>
        {!!error && (
          <ErrorPanel error={error} retry={() => retryPoll((n) => n + 1)} />
        )}
        {running && (
          <>
            <Loading
              text={
                job?.status === "queued"
                  ? "Job đang chờ worker…"
                  : "Đang chạy inference; có thể mất thời gian khi cold-start…"
              }
            />
            {jobId && (
              <button
                className="v3-button secondary"
                onClick={async () => {
                  try {
                    await api.cancel(jobId);
                    retryPoll((n) => n + 1);
                  } catch (reason) {
                    setError(reason);
                  }
                }}
              >
                Hủy job
              </button>
            )}
          </>
        )}
        {!job && !running && !error && (
          <div className="v3-empty">
            <span aria-hidden="true">↗</span>
            <h3>Một input. Nhiều cách hiện thực.</h3>
            <p>
              Chọn mẫu hoặc chỉnh đầu vào, rồi chạy toàn bộ pipeline để xem khác
              biệt.
            </p>
          </div>
        )}
        {job && <Comparison job={job} details={details} />}
        {details && overview.chapter === 6 && <AgentTrace details={details} />}
        <p className="v3-muted">
          Job và quyền đọc chỉ giữ trong phiên trình duyệt. API TTL30phút;
          redeploy không bảo toàn job.
        </p>
      </div>
    </section>
  );
}
