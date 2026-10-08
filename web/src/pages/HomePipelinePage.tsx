import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getModelRegistry,
  ModelRegistryItem,
} from "../api/predictionApi";
import ErrorMessage from "../components/ErrorMessage";

const learningTracks = [
  {
    to: "/ml",
    chapter: "Chương 2 · Machine Learning",
    title: "Nguy cơ tiểu đường",
    description:
      "MLP NumPy xử lý 21 biến CDC/BRFSS và trả về xác suất cùng ngưỡng quyết định.",
    meta: "21 features · Binary classification",
  },
  {
    to: "/cnn",
    chapter: "Chương 3 · CNN",
    title: "Phân loại ảnh EuroSAT",
    description:
      "CNN NumPy nhận ảnh vệ tinh PNG/JPEG và xếp hạng ba lớp có xác suất cao nhất.",
    meta: "64 × 64 RGB · 10 classes",
  },
  {
    to: "/rnn",
    chapter: "Chương 4 · RNN",
    title: "Dữ liệu tuần tự",
    description:
      "Hai use case cho chuỗi hành vi khách hàng và giá đóng cửa AAPL kế tiếp.",
    meta: "8 × 5 / 30 × 5 sequences",
  },
];

function formatBytes(bytes: number) {
  return bytes < 1024
    ? `${bytes} B`
    : `${(bytes / 1024).toFixed(1)} KB`;
}

export default function HomePipelinePage() {
  const [models, setModels] = useState<Record<string, ModelRegistryItem>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;
    getModelRegistry()
      .then((response) => {
        if (!ignore) setModels(response.models);
      })
      .catch((reason: Error) => {
        if (!ignore) setError(reason.message);
      });
    return () => {
      ignore = true;
    };
  }, []);

  return (
    <section className="home-page">
      <div className="hero-panel">
        <div className="page-intro">
          <p className="eyebrow">Phòng thí nghiệm mô hình</p>
          <h1>Từ notebook đến một ứng dụng AI có thể kiểm chứng.</h1>
          <p>
            Chạy thử bốn artifact đã khóa từ Chương 2–4, xem xác suất,
            baseline và mã băm mô hình ngay trên một giao diện thống nhất.
          </p>
          <div className="hero-actions">
            <Link to="/ml" className="primary-link">Bắt đầu với ML</Link>
            <a href="#model-registry" className="secondary-link">Xem model registry</a>
          </div>
        </div>
        <aside className="hero-summary" aria-label="Tóm tắt hệ thống">
          <div><strong>04</strong><span>artifact đã xác minh</span></div>
          <div><strong>03</strong><span>chương thực nghiệm</span></div>
          <div><strong>01</strong><span>API triển khai</span></div>
        </aside>
      </div>

      <div className="section-heading">
        <div>
          <p className="eyebrow">Use cases</p>
          <h2>Chọn một luồng suy luận</h2>
        </div>
        <p>Mỗi kết quả đều kèm provenance và cảnh báo sử dụng phù hợp.</p>
      </div>

      <div className="system-grid">
        {learningTracks.map((track, index) => (
          <Link to={track.to} className="system-card" key={track.to}>
            <span className="card-number">0{index + 1}</span>
            <span className="card-kicker">{track.chapter}</span>
            <h3>{track.title}</h3>
            <p>{track.description}</p>
            <span className="card-meta">{track.meta}</span>
          </Link>
        ))}
      </div>

      <section className="registry-panel" id="model-registry">
        <div className="section-heading compact-heading">
          <div>
            <p className="eyebrow">Artifact integrity</p>
            <h2>Model registry</h2>
          </div>
          <span className="verified-badge">SHA-256 verified</span>
        </div>

        {error && <ErrorMessage message={error} />}

        {!error && Object.keys(models).length === 0 && (
          <p className="helper-text">Đang tải thông tin mô hình...</p>
        )}

        <div className="registry-list">
          {Object.entries(models).map(([id, model]) => (
            <article className="registry-row" key={id}>
              <div>
                <strong>{id}</strong>
                <span>Chương {model.chapter} · {formatBytes(model.model_bytes)}</span>
              </div>
              <code title={model.model_sha256}>
                {model.model_sha256.slice(0, 16)}…
              </code>
              <span className="verified-badge">
                {model.hash_verified ? "Đã xác minh" : "Chưa xác minh"}
              </span>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
