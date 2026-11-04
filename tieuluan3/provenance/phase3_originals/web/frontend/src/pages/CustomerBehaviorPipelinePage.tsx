import { ChangeEvent, FormEvent, useState } from "react";
import {
  AaplResult,
  CustomerResult,
  getDemo,
  predictAapl,
  predictCustomer,
  SequenceInput,
} from "../api/predictionApi";
import { formatSequence, parseSequenceText } from "../api/sequence";
import ErrorMessage from "../components/ErrorMessage";
import InfoBox from "../components/InfoBox";
import LoadingState from "../components/LoadingState";
import ProbabilityBar from "../components/ProbabilityBar";
import ResultCard from "../components/ResultCard";

type Mode = "customer" | "aapl";
type SequenceResult = CustomerResult | AaplResult;

const modeContent: Record<
  Mode,
  {
    title: string;
    subtitle: string;
    rows: number;
    columns: string[];
    inputNote: string;
  }
> = {
  customer: {
    title: "Khách hàng mua tuần kế tiếp",
    subtitle:
      "RNN đọc tám tuần hành vi gần nhất và ước lượng xác suất phát sinh giao dịch.",
    rows: 8,
    columns: [
      "transaction_count",
      "quantity_sum",
      "amount_sum",
      "recency_days",
      "active_flag",
    ],
    inputNote: "8 hàng × 5 cột, active_flag chỉ nhận 0 hoặc 1.",
  },
  aapl: {
    title: "Giá đóng cửa AAPL kế tiếp",
    subtitle:
      "RNN đọc 30 phiên OHLCV và được đặt cạnh baseline naive last-Close.",
    rows: 30,
    columns: ["Open", "High", "Low", "Close", "Volume"],
    inputNote: "30 hàng × 5 cột theo thứ tự Open, High, Low, Close, Volume.",
  },
};

function readTextFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Không thể đọc tệp CSV."));
    reader.onload = () => {
      if (typeof reader.result !== "string") {
        reject(new Error("Không thể đọc tệp CSV."));
        return;
      }
      resolve(reader.result);
    };
    reader.readAsText(file);
  });
}

export default function CustomerBehaviorPipelinePage() {
  const [mode, setMode] = useState<Mode>("customer");
  const [sequenceText, setSequenceText] = useState("");
  const [sampleKey, setSampleKey] = useState("");
  const [result, setResult] = useState<SequenceResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const content = modeContent[mode];

  function chooseMode(nextMode: Mode) {
    setMode(nextMode);
    setSequenceText("");
    setSampleKey("");
    setResult(null);
    setError("");
  }

  async function loadSample() {
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const demo = await getDemo<SequenceInput>(mode);
      setSequenceText(formatSequence(demo.input.sequence));
      setSampleKey(demo.sample_key ?? `Mẫu kiểm thử ${mode}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể nạp mẫu.");
    } finally {
      setBusy(false);
    }
  }

  async function loadCsv(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (file.size > 1024 * 1024) {
      setError("Tệp CSV vượt quá giới hạn 1 MB.");
      return;
    }
    try {
      setSequenceText(await readTextFile(file));
      setSampleKey(file.name);
      setResult(null);
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể đọc CSV.");
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);

    let sequence: number[][];
    try {
      sequence = parseSequenceText(sequenceText, content.rows);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sequence không hợp lệ.");
      return;
    }

    setBusy(true);
    try {
      const nextResult =
        mode === "customer"
          ? await predictCustomer({ sequence })
          : await predictAapl({ sequence });
      setResult(nextResult);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể dự đoán.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <div className="page-intro compact">
        <p className="eyebrow">Chương 4 · Recurrent Neural Network</p>
        <h1>Dự đoán trên dữ liệu tuần tự</h1>
        <p>
          Chọn một use case, nạp chuỗi CSV đúng shape và so sánh đầu ra của
          RNN NumPy với ngưỡng phân loại hoặc baseline bắt buộc.
        </p>
      </div>

      <div className="mode-switch" role="tablist" aria-label="Chọn use case RNN">
        <button
          type="button"
          role="tab"
          aria-selected={mode === "customer"}
          className={mode === "customer" ? "active" : ""}
          onClick={() => chooseMode("customer")}
        >
          <span>Customer sequence</span>
          <strong>Hành vi tuần kế tiếp</strong>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "aapl"}
          className={mode === "aapl" ? "active" : ""}
          onClick={() => chooseMode("aapl")}
        >
          <span>AAPL sequence</span>
          <strong>Next Close</strong>
        </button>
      </div>

      <div className="tool-grid">
        <form className="form-panel" onSubmit={submit}>
          <div className="panel-heading">
            <div>
              <span className="step-label">Input / sequence</span>
              <h2>{content.title}</h2>
            </div>
            <button
              className="secondary-button"
              type="button"
              onClick={loadSample}
              disabled={busy}
            >
              Nạp mẫu kiểm thử
            </button>
          </div>

          <p className="panel-description">{content.subtitle}</p>

          <div className="column-legend" aria-label="Thứ tự cột">
            {content.columns.map((column, index) => (
              <span key={column}>
                <b>{index + 1}</b>
                {column}
              </span>
            ))}
          </div>

          <label className="sequence-field" htmlFor="sequence-input">
            <span>CSV sequence</span>
            <textarea
              id="sequence-input"
              value={sequenceText}
              onChange={(event) => setSequenceText(event.target.value)}
              placeholder={`Mỗi hàng gồm 5 số, phân tách bằng dấu phẩy.\nYêu cầu: ${content.inputNote}`}
              spellCheck={false}
            />
          </label>

          <div className="sequence-actions">
            <label className="file-button">
              Chọn tệp CSV
              <input type="file" accept=".csv,.txt,text/csv" onChange={loadCsv} />
            </label>
            <span>{sampleKey || content.inputNote}</span>
          </div>

          {error && <ErrorMessage message={error} />}

          <button className="primary-button submit-button" type="submit" disabled={busy}>
            {busy ? "Đang chạy RNN..." : "Chạy mô hình RNN"}
          </button>
        </form>

        <aside className="result-panel">
          {busy && <LoadingState />}
          {!busy && !result && !error && (
            <div className="empty-result">
              <span className="empty-icon" aria-hidden="true">03</span>
              <h2>Kết quả chuỗi sẽ xuất hiện ở đây</h2>
              <p>{content.inputNote}</p>
            </div>
          )}

          {!busy && result && "probability" in result && (
            <ResultCard title="Xác suất / RNN NumPy">
              <p className="probability-main">
                {(result.probability * 100).toFixed(1)}%
              </p>
              <ProbabilityBar
                label="Xác suất mua tuần kế tiếp"
                probability={result.probability}
                tone={result.predicted_class ? "positive" : "negative"}
              />
              <p className="threshold-note">
                Ngưỡng quyết định {(result.threshold * 100).toFixed(1)}%
              </p>
              <div className={`result-status ${result.predicted_class ? "success" : ""}`}>
                <span className="status-dot" aria-hidden="true" />
                <div>
                  <p className="result-label">{result.label}</p>
                  <p className="result-explanation">
                    Input shape {result.sequence_shape.join(" × ")}
                  </p>
                </div>
              </div>
              <p className="model-used">
                {result.provenance.version} · SHA{" "}
                {result.provenance.model_sha256.slice(0, 12)}…
              </p>
              <InfoBox title="Giới hạn diễn giải" tone="warning">
                {result.warning}
              </InfoBox>
            </ResultCard>
          )}

          {!busy && result && "rnn_prediction_usd" in result && (
            <ResultCard title="RNN so với baseline">
              <div className="price-comparison">
                <div>
                  <span>RNN dự đoán</span>
                  <strong>${result.rnn_prediction_usd.toFixed(2)}</strong>
                </div>
                <div>
                  <span>Naive last-Close</span>
                  <strong>${result.naive_last_close_usd.toFixed(2)}</strong>
                </div>
              </div>
              <div className="delta-card">
                <span>Chênh lệch RNN − baseline</span>
                <strong>
                  {result.delta_rnn_vs_naive_usd >= 0 ? "+" : ""}
                  ${result.delta_rnn_vs_naive_usd.toFixed(2)}
                </strong>
              </div>
              <p className="model-used">
                {result.provenance.version} · SHA{" "}
                {result.provenance.model_sha256.slice(0, 12)}…
              </p>
              <InfoBox title="Không phải khuyến nghị đầu tư" tone="warning">
                {result.warning}
              </InfoBox>
            </ResultCard>
          )}
        </aside>
      </div>
    </section>
  );
}
