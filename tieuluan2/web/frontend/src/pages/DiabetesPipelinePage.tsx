import { FormEvent, useState } from "react";
import {
  DiabetesInput,
  DiabetesResult,
  getDemo,
  predictDiabetes,
} from "../api/predictionApi";
import ErrorMessage from "../components/ErrorMessage";
import InfoBox from "../components/InfoBox";
import LoadingState from "../components/LoadingState";
import ProbabilityBar from "../components/ProbabilityBar";
import ResultCard from "../components/ResultCard";

type FeatureName = keyof DiabetesInput;

type FeatureConfig = {
  name: FeatureName;
  label: string;
  hint: string;
  binary?: boolean;
  min?: number;
  max?: number;
};

type FeatureGroup = {
  title: string;
  description: string;
  features: FeatureConfig[];
};

const featureGroups: FeatureGroup[] = [
  {
    title: "Chỉ số sức khỏe",
    description: "Các chẩn đoán và tự đánh giá sức khỏe cơ bản.",
    features: [
      { name: "HighBP", label: "Huyết áp cao", hint: "Đã từng được chẩn đoán", binary: true },
      { name: "HighChol", label: "Cholesterol cao", hint: "Đã từng được chẩn đoán", binary: true },
      { name: "CholCheck", label: "Đã kiểm tra cholesterol", hint: "Trong 5 năm gần đây", binary: true },
      { name: "BMI", label: "BMI", hint: "Chỉ số khối cơ thể", min: 10, max: 100 },
      { name: "Stroke", label: "Tiền sử đột quỵ", hint: "Có hoặc không", binary: true },
      { name: "HeartDiseaseorAttack", label: "Bệnh tim / nhồi máu", hint: "Có hoặc không", binary: true },
      { name: "GenHlth", label: "Sức khỏe tổng quát", hint: "1 = rất tốt, 5 = kém", min: 1, max: 5 },
    ],
  },
  {
    title: "Thói quen và vận động",
    description: "Các biến hành vi trong bảng hỏi CDC/BRFSS.",
    features: [
      { name: "Smoker", label: "Từng hút thuốc", hint: "≥ 100 điếu trong đời", binary: true },
      { name: "PhysActivity", label: "Có vận động", hint: "Trong 30 ngày gần đây", binary: true },
      { name: "Fruits", label: "Ăn trái cây hằng ngày", hint: "Có hoặc không", binary: true },
      { name: "Veggies", label: "Ăn rau hằng ngày", hint: "Có hoặc không", binary: true },
      { name: "HvyAlcoholConsump", label: "Uống rượu mức cao", hint: "Theo ngưỡng của khảo sát", binary: true },
      { name: "MentHlth", label: "Ngày sức khỏe tinh thần kém", hint: "Trong 30 ngày", min: 0, max: 30 },
      { name: "PhysHlth", label: "Ngày sức khỏe thể chất kém", hint: "Trong 30 ngày", min: 0, max: 30 },
      { name: "DiffWalk", label: "Khó đi bộ", hint: "Có hoặc không", binary: true },
    ],
  },
  {
    title: "Tiếp cận y tế và nhân khẩu học",
    description: "Thông tin bảo hiểm, giới tính và nhóm phân loại.",
    features: [
      { name: "AnyHealthcare", label: "Có bảo hiểm y tế", hint: "Có hoặc không", binary: true },
      { name: "NoDocbcCost", label: "Không khám vì chi phí", hint: "Trong 12 tháng gần đây", binary: true },
      { name: "Sex", label: "Giới tính mã hóa", hint: "0 = nữ, 1 = nam", binary: true },
      { name: "Age", label: "Nhóm tuổi", hint: "Mã nhóm từ 1 đến 13", min: 1, max: 13 },
      { name: "Education", label: "Nhóm học vấn", hint: "Mã nhóm từ 1 đến 6", min: 1, max: 6 },
      { name: "Income", label: "Nhóm thu nhập", hint: "Mã nhóm từ 1 đến 8", min: 1, max: 8 },
    ],
  },
];

const allFeatures = featureGroups.flatMap((group) => group.features);

const emptyValues = Object.fromEntries(
  allFeatures.map((feature) => [feature.name, ""]),
) as Record<FeatureName, string>;

function provenanceLabel(result: DiabetesResult) {
  return `${result.provenance.version} · SHA ${result.provenance.model_sha256.slice(0, 12)}…`;
}

export default function DiabetesPipelinePage() {
  const [values, setValues] = useState<Record<FeatureName, string>>(emptyValues);
  const [result, setResult] = useState<DiabetesResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [sampleKey, setSampleKey] = useState("");

  function updateValue(name: FeatureName, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  async function loadSample() {
    setBusy(true);
    setError("");
    try {
      const demo = await getDemo<DiabetesInput>("diabetes");
      setValues(
        Object.fromEntries(
          Object.entries(demo.input).map(([key, value]) => [key, String(value)]),
        ) as Record<FeatureName, string>,
      );
      setSampleKey(demo.sample_key ?? "Mẫu kiểm thử CDC/BRFSS");
      setResult(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể nạp mẫu.");
    } finally {
      setBusy(false);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (Object.values(values).some((value) => value === "")) {
      setError("Vui lòng điền đủ 21 trường hoặc sử dụng nút nạp mẫu.");
      return;
    }

    const payload = Object.fromEntries(
      allFeatures.map((feature) => [feature.name, Number(values[feature.name])]),
    ) as DiabetesInput;

    setBusy(true);
    try {
      setResult(await predictDiabetes(payload));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể dự đoán.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <div className="page-intro compact">
        <p className="eyebrow">Chương 2 · Machine Learning</p>
        <h1>Dự đoán nguy cơ tiểu đường</h1>
        <p>
          MLP viết bằng NumPy xử lý đúng 21 biến đầu vào của tập CDC/BRFSS.
          Kết quả là xác suất của lớp dương và ngưỡng quyết định đã khóa.
        </p>
      </div>

      <div className="tool-grid wide-form">
        <form className="form-panel" onSubmit={submit}>
          <div className="panel-heading">
            <div>
              <span className="step-label">Input / 21 features</span>
              <h2>Thông tin đầu vào</h2>
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

          {sampleKey && <p className="sample-note">Đã nạp: {sampleKey}</p>}

          {featureGroups.map((group) => (
            <fieldset className="feature-group" key={group.title}>
              <legend>{group.title}</legend>
              <p>{group.description}</p>
              <div className="form-grid">
                {group.features.map((feature) => (
                  <div className="form-field" key={feature.name}>
                    <label htmlFor={feature.name}>
                      {feature.label}
                      <span>{feature.name}</span>
                    </label>
                    {feature.binary ? (
                      <select
                        id={feature.name}
                        value={values[feature.name]}
                        required
                        onChange={(event) =>
                          updateValue(feature.name, event.target.value)
                        }
                      >
                        <option value="">Chọn giá trị</option>
                        <option value="0">0 — Không</option>
                        <option value="1">1 — Có</option>
                      </select>
                    ) : (
                      <input
                        id={feature.name}
                        type="number"
                        min={feature.min}
                        max={feature.max}
                        step="1"
                        value={values[feature.name]}
                        required
                        onChange={(event) =>
                          updateValue(feature.name, event.target.value)
                        }
                      />
                    )}
                    <small>{feature.hint}</small>
                  </div>
                ))}
              </div>
            </fieldset>
          ))}

          {error && <ErrorMessage message={error} />}

          <button className="primary-button submit-button" type="submit" disabled={busy}>
            {busy ? "Đang xử lý..." : "Chạy mô hình ML"}
          </button>
        </form>

        <aside className="result-panel sticky-result">
          {busy && <LoadingState />}
          {!busy && !result && !error && (
            <div className="empty-result">
              <span className="empty-icon" aria-hidden="true">01</span>
              <h2>Kết quả sẽ xuất hiện ở đây</h2>
              <p>Nạp mẫu hoặc điền đủ dữ liệu rồi chạy mô hình.</p>
            </div>
          )}
          {!busy && result && (
            <ResultCard title="Xác suất nguy cơ / MLP NumPy">
              <p className="probability-main">
                {(result.probability * 100).toFixed(1)}%
              </p>
              <ProbabilityBar
                label="Xác suất lớp dương"
                probability={result.probability}
                tone={result.predicted_class ? "positive" : "negative"}
              />
              <p className="threshold-note">
                Ngưỡng quyết định {(result.threshold * 100).toFixed(1)}%
              </p>
              <div className={`result-status ${result.predicted_class ? "warning" : "success"}`}>
                <span className="status-dot" aria-hidden="true" />
                <div>
                  <p className="result-label">{result.label}</p>
                  <p className="result-explanation">
                    Lớp dự đoán: {result.predicted_class}
                  </p>
                </div>
              </div>
              <p className="model-used">{provenanceLabel(result)}</p>
              <InfoBox title="Lưu ý sử dụng" tone="warning">
                {result.warning}
              </InfoBox>
            </ResultCard>
          )}
        </aside>
      </div>
    </section>
  );
}
