import { ChangeEvent, DragEvent, FormEvent, useState } from "react";
import {
  EuroSatInput,
  EuroSatResult,
  getDemo,
  predictEuroSat,
} from "../api/predictionApi";
import ErrorMessage from "../components/ErrorMessage";
import InfoBox from "../components/InfoBox";
import LoadingState from "../components/LoadingState";
import ProbabilityBar from "../components/ProbabilityBar";
import ResultCard from "../components/ResultCard";

const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
const ACCEPTED_TYPES = new Set(["image/png", "image/jpeg"]);

function readImage(file: File): Promise<{ base64: string; preview: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Không thể đọc tệp ảnh."));
    reader.onload = () => {
      if (typeof reader.result !== "string") {
        reject(new Error("Không thể đọc tệp ảnh."));
        return;
      }
      const comma = reader.result.indexOf(",");
      resolve({
        base64: reader.result.slice(comma + 1),
        preview: reader.result,
      });
    };
    reader.readAsDataURL(file);
  });
}

export default function HousePricePipelinePage() {
  const [imageBase64, setImageBase64] = useState("");
  const [preview, setPreview] = useState("");
  const [fileLabel, setFileLabel] = useState("");
  const [result, setResult] = useState<EuroSatResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);

  async function useFile(file?: File) {
    if (!file) return;
    setError("");
    setResult(null);

    if (!ACCEPTED_TYPES.has(file.type)) {
      setError("Chỉ chấp nhận ảnh PNG hoặc JPEG.");
      return;
    }
    if (file.size > MAX_IMAGE_BYTES) {
      setError("Ảnh vượt quá giới hạn 5 MB.");
      return;
    }

    try {
      const image = await readImage(file);
      setImageBase64(image.base64);
      setPreview(image.preview);
      setFileLabel(`${file.name} · ${(file.size / 1024).toFixed(1)} KB`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể đọc ảnh.");
    }
  }

  async function loadSample() {
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const demo = await getDemo<EuroSatInput>("eurosat");
      setImageBase64(demo.input.image_base64);
      setPreview(`data:image/jpeg;base64,${demo.input.image_base64}`);
      setFileLabel(demo.sample_key ?? "Ảnh EuroSAT kiểm thử");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể nạp mẫu.");
    } finally {
      setBusy(false);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!imageBase64) {
      setError("Hãy chọn ảnh hoặc nạp mẫu kiểm thử.");
      return;
    }

    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(await predictEuroSat({ image_base64: imageBase64 }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể phân loại.");
    } finally {
      setBusy(false);
    }
  }

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragging(false);
    void useFile(event.dataTransfer.files[0]);
  }

  return (
    <section>
      <div className="page-intro compact">
        <p className="eyebrow">Chương 3 · Convolutional Neural Network</p>
        <h1>Phân loại ảnh vệ tinh EuroSAT</h1>
        <p>
          Tải một ảnh RGB để CNN NumPy dự đoán lớp phủ bề mặt. Ảnh được
          kiểm tra định dạng, giới hạn kích thước và resize về 64 × 64.
        </p>
      </div>

      <div className="tool-grid">
        <form className="form-panel" onSubmit={submit}>
          <div className="panel-heading">
            <div>
              <span className="step-label">Input / satellite image</span>
              <h2>Ảnh đầu vào</h2>
            </div>
            <button
              className="secondary-button"
              type="button"
              onClick={loadSample}
              disabled={busy}
            >
              Nạp ảnh mẫu
            </button>
          </div>

          <label
            className={`image-dropzone ${dragging ? "dragging" : ""} ${preview ? "has-image" : ""}`}
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept="image/png,image/jpeg"
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                void useFile(event.target.files?.[0])
              }
            />
            {preview ? (
              <>
                <img src={preview} alt="Ảnh vệ tinh đã chọn" />
                <span className="replace-image">Chọn ảnh khác</span>
              </>
            ) : (
              <span className="dropzone-copy">
                <strong>Kéo thả ảnh vào đây</strong>
                <span>hoặc nhấn để chọn tệp PNG/JPEG, tối đa 5 MB</span>
              </span>
            )}
          </label>

          {fileLabel && <p className="sample-note">{fileLabel}</p>}
          {error && <ErrorMessage message={error} />}

          <button className="primary-button submit-button" type="submit" disabled={busy}>
            {busy ? "Đang phân loại..." : "Chạy mô hình CNN"}
          </button>
        </form>

        <aside className="result-panel">
          {busy && <LoadingState />}
          {!busy && !result && !error && (
            <div className="empty-result">
              <span className="empty-icon" aria-hidden="true">02</span>
              <h2>Top-3 lớp sẽ hiển thị tại đây</h2>
              <p>Mô hình trả về phân bố xác suất trên 10 lớp EuroSAT.</p>
            </div>
          )}
          {!busy && result && (
            <ResultCard title="Top-3 / CNN NumPy">
              <p className="result-value">{result.predicted_class}</p>
              <div className="ranking-list">
                {result.top_classes.map((item, index) => (
                  <div className="ranking-row" key={item.class_index}>
                    <div className="rank-heading">
                      <span>0{index + 1}</span>
                      <strong>{item.class_name}</strong>
                      <b>{(item.confidence * 100).toFixed(1)}%</b>
                    </div>
                    <ProbabilityBar
                      label="Độ tin cậy"
                      probability={item.confidence}
                      tone={index === 0 ? "positive" : "negative"}
                    />
                  </div>
                ))}
              </div>
              <p className="model-used">
                {result.provenance.version} · SHA{" "}
                {result.provenance.model_sha256.slice(0, 12)}…
              </p>
              <InfoBox title="Phạm vi sử dụng" tone="warning">
                {result.warning}
              </InfoBox>
            </ResultCard>
          )}
        </aside>
      </div>

      <section className="explain-grid" aria-label="Thông tin mô hình">
        <article>
          <span className="step-label">Preprocess</span>
          <h3>64 × 64 RGB</h3>
          <p>Ảnh được chuyển RGB, resize bilinear và chuẩn hóa về [0, 1].</p>
        </article>
        <article>
          <span className="step-label">Output</span>
          <h3>10 lớp phủ bề mặt</h3>
          <p>Từ AnnualCrop, Forest đến Residential, River và SeaLake.</p>
        </article>
        <article>
          <span className="step-label">Integrity</span>
          <h3>Hash-verified artifact</h3>
          <p>API từ chối khởi động nếu SHA-256 của model không khớp registry.</p>
        </article>
      </section>
    </section>
  );
}
