import { FormEvent, useEffect, useRef, useState } from "react";
import {
  DiabetesCompareResponse,
  DiabetesRequest,
  DiabetesResponse,
  ModelOption,
  compareDiabetesModels,
  getModelOptions,
  predictDiabetes,
} from "../api/predictionApi";
import ErrorMessage from "../components/ErrorMessage";
import FormField from "../components/FormField";
import InfoBox from "../components/InfoBox";
import InputAccordion from "../components/InputAccordion";
import LoadingState from "../components/LoadingState";
import ResultCard from "../components/ResultCard";
import SelectField from "../components/SelectField";

type DiabetesField = Exclude<keyof DiabetesRequest, "model">;
type Group = "Chỉ số sức khỏe" | "Thói quen và y tế" | "Đánh giá và nhân khẩu";
type Field = { name: DiabetesField; label: string; group: Group; binary?: boolean; min?: number };

const fields: Field[] = [
  { name: "HighBP", label: "Huyết áp cao", group: "Chỉ số sức khỏe", binary: true },
  { name: "HighChol", label: "Cholesterol cao", group: "Chỉ số sức khỏe", binary: true },
  { name: "CholCheck", label: "Đã kiểm tra cholesterol", group: "Chỉ số sức khỏe", binary: true },
  { name: "BMI", label: "BMI", group: "Chỉ số sức khỏe", min: 0 },
  { name: "Stroke", label: "Tiền sử đột quỵ", group: "Chỉ số sức khỏe", binary: true },
  { name: "HeartDiseaseorAttack", label: "Bệnh tim/heart attack", group: "Chỉ số sức khỏe", binary: true },
  { name: "Smoker", label: "Từng hút thuốc", group: "Thói quen và y tế", binary: true },
  { name: "PhysActivity", label: "Vận động thể chất", group: "Thói quen và y tế", binary: true },
  { name: "Fruits", label: "Ăn trái cây hằng ngày", group: "Thói quen và y tế", binary: true },
  { name: "Veggies", label: "Ăn rau hằng ngày", group: "Thói quen và y tế", binary: true },
  { name: "HvyAlcoholConsump", label: "Uống rượu nhiều", group: "Thói quen và y tế", binary: true },
  { name: "AnyHealthcare", label: "Có chăm sóc y tế", group: "Thói quen và y tế", binary: true },
  { name: "NoDocbcCost", label: "Không khám vì chi phí", group: "Thói quen và y tế", binary: true },
  { name: "GenHlth", label: "Sức khỏe tổng quát (1-5)", group: "Đánh giá và nhân khẩu", min: 1 },
  { name: "MentHlth", label: "Ngày sức khỏe tinh thần kém", group: "Đánh giá và nhân khẩu", min: 0 },
  { name: "PhysHlth", label: "Ngày sức khỏe thể chất kém", group: "Đánh giá và nhân khẩu", min: 0 },
  { name: "DiffWalk", label: "Khó đi bộ/leo cầu thang", group: "Đánh giá và nhân khẩu", binary: true },
  { name: "Sex", label: "Giới tính source code", group: "Đánh giá và nhân khẩu", binary: true },
  { name: "Age", label: "Nhóm tuổi (1-13)", group: "Đánh giá và nhân khẩu", min: 1 },
  { name: "Education", label: "Học vấn (1-6)", group: "Đánh giá và nhân khẩu", min: 1 },
  { name: "Income", label: "Thu nhập (1-8)", group: "Đánh giá và nhân khẩu", min: 1 },
];

const groups: Group[] = ["Chỉ số sức khỏe", "Thói quen và y tế", "Đánh giá và nhân khẩu"];
const initialForm: Record<DiabetesField, string> = {
  HighBP: "1",
  HighChol: "0",
  CholCheck: "1",
  BMI: "26",
  Smoker: "0",
  Stroke: "0",
  HeartDiseaseorAttack: "0",
  PhysActivity: "1",
  Fruits: "0",
  Veggies: "1",
  HvyAlcoholConsump: "0",
  AnyHealthcare: "1",
  NoDocbcCost: "0",
  GenHlth: "3",
  MentHlth: "5",
  PhysHlth: "30",
  DiffWalk: "0",
  Sex: "1",
  Age: "4",
  Education: "6",
  Income: "8",
};

const fallbackModelOptions: ModelOption[] = [{ id: "improved_dnn", name: "Improved DNN", recommended: true }];
const COMPARE_ALL_MODELS_ID = "__compare_all_models__";
const binaryOptions = [{ value: "0", label: "0 - Không" }, { value: "1", label: "1 - Có" }];

function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function labelFor(prediction: number) {
  return prediction === 1 ? "Dương tính" : "Âm tính";
}

export default function DiabetesPipelinePage() {
  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<DiabetesResponse | null>(null);
  const [compareResult, setCompareResult] = useState<DiabetesCompareResponse | null>(null);
  const [modelOptions, setModelOptions] = useState(fallbackModelOptions);
  const [selectedModel, setSelectedModel] = useState("improved_dnn");
  const userSelectedModelRef = useRef(false);

  useEffect(() => {
    let ignore = false;
    getModelOptions()
      .then((data) => {
        if (ignore) return;
        setModelOptions(data.diabetes.models);
        if (!userSelectedModelRef.current) setSelectedModel(data.diabetes.default_model);
      })
      .catch(console.error);
    return () => {
      ignore = true;
    };
  }, []);

  function buildPayload() {
    const errors: Record<string, string> = {};
    const payload = {} as DiabetesRequest;
    const writablePayload = payload as Record<DiabetesField, number>;

    for (const field of fields) {
      const rawValue = form[field.name].trim();
      const number = Number(rawValue);
      if (!rawValue) errors[field.name] = `Vui lòng nhập ${field.label}.`;
      else if (!Number.isFinite(number)) errors[field.name] = `${field.label} phải là số.`;
      else writablePayload[field.name] = number;
    }

    setFieldErrors(errors);
    payload.model = selectedModel;
    return Object.keys(errors).length ? null : payload;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = buildPayload();
    if (!payload) return;

    setLoading(selectedModel !== COMPARE_ALL_MODELS_ID);
    setCompareLoading(selectedModel === COMPARE_ALL_MODELS_ID);
    setError("");
    setResult(null);
    setCompareResult(null);

    try {
      if (selectedModel === COMPARE_ALL_MODELS_ID) setCompareResult(await compareDiabetesModels(payload));
      else setResult(await predictDiabetes(payload));
    } catch (requestError) {
      console.error(requestError);
      setError("Không thể hoàn tất dự đoán. Vui lòng kiểm tra API và dữ liệu.");
    } finally {
      setLoading(false);
      setCompareLoading(false);
    }
  }

  return (
    <section className="tool-page">
      <div className="page-intro compact">
        <p className="eyebrow">CDC/BRFSS health indicators</p>
        <h2>Dự đoán tiểu đường</h2>
        <p>Theo dõi 21 feature CDC/BRFSS theo ba nhóm sức khỏe, thói quen và nhân khẩu.</p>
      </div>

      <div className="tool-grid">
        <form className="form-panel" onSubmit={handleSubmit}>
          <div className="form-grid">
            <SelectField
              id="diabetes-model"
              label="Chọn model dự đoán"
              value={selectedModel}
              options={[
                ...modelOptions.map((model) => ({
                  value: model.id,
                  label: `${model.name}${model.recommended ? " (khuyến nghị)" : ""}`,
                })),
                { value: COMPARE_ALL_MODELS_ID, label: "So sánh model đang triển khai" },
              ]}
              onChange={(value) => {
                userSelectedModelRef.current = true;
                setSelectedModel(value);
              }}
            />
            {groups.map((group, index) => (
              <InputAccordion title={group} defaultOpen={index === 0} key={group}>
                <div className="form-grid nested">
                  {fields.filter((field) => field.group === group).map((field) =>
                    field.binary ? (
                      <SelectField
                        key={field.name}
                        id={field.name}
                        label={field.label}
                        value={form[field.name]}
                        options={binaryOptions}
                        fullWidth={false}
                        onChange={(value) => setForm((current) => ({ ...current, [field.name]: value }))}
                      />
                    ) : (
                      <FormField
                        key={field.name}
                        id={field.name}
                        label={field.label}
                        min={field.min}
                        value={form[field.name]}
                        error={fieldErrors[field.name]}
                        onChange={(value) => setForm((current) => ({ ...current, [field.name]: value }))}
                      />
                    ),
                  )}
                </div>
              </InputAccordion>
            ))}
          </div>
          <div className="button-row">
            <button className="primary-button" type="submit" disabled={loading || compareLoading}>
              {compareLoading ? "Đang so sánh..." : loading ? "Đang dự đoán..." : "Dự đoán"}
            </button>
            <button className="secondary-button" type="button" onClick={() => setForm(initialForm)}>
              Demo input
            </button>
          </div>
        </form>

        <aside className="result-panel">
          {loading && <LoadingState />}
          {error && <ErrorMessage message={error} />}
          {result && (
            <ResultCard title="Kết quả dự đoán">
              <p className="model-used">Model đã chọn: {result.model?.name ?? selectedModel}</p>
              <div className={`result-status ${result.prediction === 1 ? "warning" : "success"}`}>
                <span className="status-dot" aria-hidden="true" />
                <p className="result-label">{labelFor(result.prediction)}</p>
              </div>
              {typeof result.probability === "number" ? (
                <section className="result-section">
                  <h3>Xác suất class 1</h3>
                  <p className="probability-main">{formatPercent(result.probability)}</p>
                </section>
              ) : null}
              <InfoBox title="Lưu ý" tone="warning">
                Kết quả chỉ phục vụ học tập, không phải chẩn đoán y khoa.
              </InfoBox>
            </ResultCard>
          )}
          {compareResult && (
            <ResultCard title="So sánh kết quả">
              <div className="comparison-list">
                {compareResult.results.map((item) => (
                  <div className="comparison-row" key={item.model_id}>
                    <strong>{item.model_name}</strong>
                    <span>{labelFor(item.prediction)}</span>
                    <span>{typeof item.probability === "number" ? formatPercent(item.probability) : "N/A"}</span>
                  </div>
                ))}
              </div>
            </ResultCard>
          )}
        </aside>
      </div>
    </section>
  );
}
