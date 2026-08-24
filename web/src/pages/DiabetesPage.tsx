import { FormEvent, useEffect, useRef, useState } from "react";
import {
  DiabetesRequest,
  DiabetesCompareResponse,
  DiabetesResponse,
  ModelOption,
  compareDiabetesModels,
  getModelOptions,
  predictDiabetes,
} from "../api/predictionApi";
import ErrorMessage from "../components/ErrorMessage";
import FormField from "../components/FormField";
import InfoBox from "../components/InfoBox";
import LoadingState from "../components/LoadingState";
import ResultCard from "../components/ResultCard";
import SelectField from "../components/SelectField";

type DiabetesField = Exclude<keyof DiabetesRequest, "model">;

const fields: Array<{ name: DiabetesField; label: string }> = [
  { name: "Glucose", label: "Glucose" },
  { name: "BMI", label: "BMI" },
  { name: "Age", label: "Tuổi" },
  { name: "Pregnancies", label: "Số lần mang thai" },
  { name: "BloodPressure", label: "Huyết áp" },
  {
    name: "DiabetesPedigreeFunction",
    label: "Chỉ số di truyền tiểu đường",
  },
];

const initialForm: Record<DiabetesField, string> = {
  Glucose: "125",
  BMI: "29.5",
  Age: "38",
  Pregnancies: "3",
  BloodPressure: "78",
  DiabetesPedigreeFunction: "0.55",
};

const fallbackModelOptions: ModelOption[] = [
  { id: "logistic_regression", name: "Logistic Regression", recommended: true },
  { id: "knn", name: "KNN", recommended: false },
  { id: "decision_tree", name: "Decision Tree", recommended: false },
  { id: "random_forest", name: "Random Forest", recommended: false },
  { id: "svm_rbf", name: "SVM (RBF)", recommended: false },
];

const COMPARE_ALL_MODELS_ID = "__compare_all_models__";

function toFriendlyError(message: string) {
  if (message.includes("Missing required field")) {
    return "Vui lòng nhập đầy đủ các trường.";
  }

  if (message.includes("Invalid number")) {
    return "Giá trị nhập vào phải là số hợp lệ.";
  }

  if (message.includes("Failed to fetch") || message.includes("NetworkError")) {
    return "Không thể kết nối tới hệ thống. Vui lòng thử lại.";
  }

  return "Không thể hoàn tất dự đoán. Vui lòng kiểm tra dữ liệu và thử lại.";
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function getDominantProbability(positiveProbability: number) {
  const safePositive = Math.min(Math.max(positiveProbability, 0), 1);
  const negativeProbability = 1 - safePositive;
  const positiveIsHigher = safePositive >= negativeProbability;

  return {
    label: positiveIsHigher
      ? "Nhóm dương tính theo mô hình"
      : "Nhóm âm tính theo mô hình",
    probability: positiveIsHigher ? safePositive : negativeProbability,
    tone: positiveIsHigher ? "positive" : "negative",
    detail: positiveIsHigher
      ? `Tỷ lệ dương tính đang cao hơn tỷ lệ âm tính (${formatPercent(
          safePositive,
        )} so với ${formatPercent(negativeProbability)}).`
      : `Tỷ lệ âm tính đang cao hơn tỷ lệ dương tính (${formatPercent(
          negativeProbability,
        )} so với ${formatPercent(safePositive)}).`,
  } as const;
}

function diabetesLabel(prediction: number) {
  return prediction === 1 ? "Dương tính" : "Âm tính";
}

function diabetesGroupLabel(prediction: number) {
  return prediction === 1 ? "Dương tính" : "Âm tính";
}

export default function DiabetesPage() {
  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [error, setError] = useState("");
  const [compareError, setCompareError] = useState("");
  const [scenarioError, setScenarioError] = useState("");
  const [result, setResult] = useState<DiabetesResponse | null>(null);
  const [compareResult, setCompareResult] =
    useState<DiabetesCompareResponse | null>(null);
  const [originalForm, setOriginalForm] = useState<Record<
    DiabetesField,
    string
  > | null>(null);
  const [scenarioForm, setScenarioForm] = useState<Record<
    DiabetesField,
    string
  > | null>(null);
  const [scenarioResult, setScenarioResult] = useState<DiabetesResponse | null>(
    null,
  );
  const [modelOptions, setModelOptions] = useState(fallbackModelOptions);
  const [selectedModel, setSelectedModel] = useState("logistic_regression");
  const [predictionModelId, setPredictionModelId] = useState<string | null>(
    null,
  );
  const userSelectedModelRef = useRef(false);

  useEffect(() => {
    let ignore = false;

    getModelOptions()
      .then((data) => {
        if (ignore) return;

        setModelOptions(data.diabetes.models);
        if (!userSelectedModelRef.current) {
          setSelectedModel(data.diabetes.default_model);
        }
      })
      .catch((requestError) => {
        console.error(requestError);
      });

    return () => {
      ignore = true;
    };
  }, []);

  function buildPayload(
    source = form,
    updateErrors = true,
    modelId = selectedModel,
  ) {
    const errors: Record<string, string> = {};
    const payload = {} as DiabetesRequest;

    for (const field of fields) {
      const rawValue = source[field.name].trim();
      const number = Number(rawValue);

      if (rawValue === "") {
        errors[field.name] = `Vui lòng nhập ${field.label}.`;
      } else if (!Number.isFinite(number)) {
        errors[field.name] = `${field.label} phải là số hợp lệ.`;
      } else {
        payload[field.name] = number;
      }
    }

    if (updateErrors) {
      setFieldErrors(errors);
    }

    payload.model = modelId;
    return Object.keys(errors).length === 0 ? payload : null;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = buildPayload();

    if (!payload) return;

    setError("");
    setCompareError("");
    setResult(null);

    if (selectedModel === COMPARE_ALL_MODELS_ID) {
      setCompareLoading(true);
      setCompareResult(null);
      setOriginalForm(null);
      setScenarioForm(null);
      setScenarioResult(null);
      setPredictionModelId(null);

      try {
        setCompareResult(await compareDiabetesModels(payload));
      } catch (requestError) {
        console.error(requestError);
        setCompareError("Không thể lấy kết quả so sánh. Vui lòng thử lại.");
      } finally {
        setCompareLoading(false);
      }

      return;
    }

    setLoading(true);

    try {
      const prediction = await predictDiabetes(payload);
      setResult(prediction);
      setPredictionModelId(
        prediction.model?.id ?? payload.model ?? selectedModel,
      );
      setOriginalForm({ ...form });
      setScenarioForm({ ...form });
      setScenarioResult(null);
      setCompareResult(null);
    } catch (requestError) {
      console.error(requestError);
      setError(
        requestError instanceof Error
          ? toFriendlyError(requestError.message)
          : "Không thể hoàn tất dự đoán. Vui lòng thử lại.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleScenarioPredict() {
    if (!scenarioForm) return;
    const payload = buildPayload(
      scenarioForm,
      false,
      predictionModelId ?? result?.model?.id ?? selectedModel,
    );

    if (!payload) {
      setScenarioError("Giá trị mô phỏng phải là số hợp lệ.");
      return;
    }

    setScenarioLoading(true);
    setScenarioError("");

    try {
      setScenarioResult(await predictDiabetes(payload));
    } catch (requestError) {
      console.error(requestError);
      setScenarioError("Không thể tính kết quả mô phỏng. Vui lòng thử lại.");
    } finally {
      setScenarioLoading(false);
    }
  }

  function startScenario() {
    setScenarioForm({ ...form });
    setScenarioResult(null);
    setScenarioError("");
  }

  function resetScenario() {
    if (originalForm) {
      setScenarioForm({ ...originalForm });
    }
    setScenarioResult(null);
    setScenarioError("");
  }

  function clearForm() {
    setForm(initialForm);
    setFieldErrors({});
    setError("");
    setCompareError("");
    setScenarioError("");
    setResult(null);
    setCompareResult(null);
    setOriginalForm(null);
    setScenarioForm(null);
    setScenarioResult(null);
    setPredictionModelId(null);
  }

  function handleModelChange(modelId: string) {
    userSelectedModelRef.current = true;
    setSelectedModel(modelId);
    setResult(null);
    setCompareResult(null);
    setOriginalForm(null);
    setScenarioForm(null);
    setScenarioResult(null);
    setPredictionModelId(null);
    setError("");
    setCompareError("");
    setScenarioError("");
  }

  return (
    <section className="tool-page">
      <div className="page-intro compact">
        <p className="eyebrow">Dự đoán sức khỏe</p>
        <h2>Dự đoán tiểu đường</h2>
        <p>
          Nhập các thông tin sức khỏe bên dưới để nhận kết quả dự đoán từ mô
          hình.
        </p>
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
                {
                  value: COMPARE_ALL_MODELS_ID,
                  label: "So sánh 5 mô hình",
                },
              ]}
              onChange={handleModelChange}
            />
            {fields.map((field) => (
              <FormField
                key={field.name}
                id={field.name}
                label={field.label}
                value={form[field.name]}
                error={fieldErrors[field.name]}
                onChange={(value) =>
                  setForm((current) => ({ ...current, [field.name]: value }))
                }
              />
            ))}
          </div>
          <div className="button-row">
            <button
              className="primary-button"
              type="submit"
              disabled={loading || compareLoading}
            >
              {compareLoading
                ? "Đang so sánh..."
                : loading
                  ? "Đang dự đoán..."
                  : "Dự đoán"}
            </button>
          </div>
        </form>

        <aside className="result-panel">
          {loading && <LoadingState />}
          {error && <ErrorMessage message={error} />}
          {compareError && <ErrorMessage message={compareError} />}
          {result && (
            <ResultCard title="Kết quả dự đoán">
              {result.model ? (
                <p className="model-used">Model đã chọn: {result.model.name}</p>
              ) : null}
              <div
                className={`result-status ${
                  result.prediction === 1 ? "warning" : "success"
                }`}
              >
                <span className="status-dot" aria-hidden="true" />
                <div>
                  <p className="result-label">
                    {result.prediction === 1 ? "Dương tính" : "Âm tính"}
                  </p>
                </div>
              </div>

              {typeof result.probability === "number"
                ? (() => {
                    const dominant = getDominantProbability(result.probability);

                    return (
                      <section className="result-section">
                        <h3>
                          Tỉ lệ{" "}
                          {result.prediction === 1 ? "Dương tính" : "Âm tính"}{" "}
                          của bạn là:
                        </h3>
                        <p className="probability-main">
                          {formatPercent(dominant.probability)}
                        </p>
                        <p className="helper-text">
                          {dominant.detail} Đây chỉ là tỉ lệ dự đoán của mô
                          hình, không phải xác suất y khoa khẳng định bạn mắc
                          bệnh.
                        </p>
                      </section>
                    );
                  })()
                : null}

              <InfoBox title="Lưu ý" tone="warning">
                Kết quả này chỉ phục vụ mục đích học tập và minh họa Machine
                Learning. Đây không phải chẩn đoán y khoa và không thay thế tư
                vấn của bác sĩ.
              </InfoBox>
            </ResultCard>
          )}
          {compareResult && (
            <>
              <ResultCard title="So sánh kết quả">
                <div className="comparison-list">
                  {compareResult.results.map((item) => {
                    const dominant =
                      typeof item.probability === "number"
                        ? getDominantProbability(item.probability)
                        : null;
                    return (
                      <div className="comparison-row" key={item.model_id}>
                        <div>
                          <strong>{item.model_name}</strong>
                          {item.recommended ? (
                            <span className="badge">Khuyến nghị</span>
                          ) : null}
                        </div>
                        <span>{diabetesGroupLabel(item.prediction)}</span>
                        <span>
                          {typeof item.probability === "number"
                            ? formatPercent(dominant ? dominant.probability : 0)
                            : "Không có xác suất"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </ResultCard>

              <ResultCard title="Mức đồng thuận giữa các mô hình">
                <p className="probability-main">
                  {formatPercent(compareResult.consensus.agreement_ratio)}
                </p>
                <p className="helper-text">
                  {compareResult.consensus.agreeing_models}/
                  {compareResult.consensus.total_models} mô hình đưa ra cùng một
                  kết luận:{" "}
                  {diabetesGroupLabel(
                    compareResult.consensus.majority_prediction,
                  )}
                  . Đây là tỷ lệ các mô hình đồng ý với nhau, không phải độ tin
                  cậy y khoa.
                </p>
              </ResultCard>
            </>
          )}
        </aside>
      </div>

      {result && (
        <div className="scenario-card">
          <ResultCard title="Mô phỏng thay đổi thông số">
            {!scenarioForm ? (
              <button
                className="secondary-button"
                type="button"
                onClick={startScenario}
              >
                Thử thay đổi thông số
              </button>
            ) : (
              <>
                <div className="scenario-input-grid">
                  {fields.map((field) => (
                    <FormField
                      key={field.name}
                      id={`scenario-${field.name}`}
                      label={field.label}
                      value={scenarioForm[field.name]}
                      onChange={(value) =>
                        setScenarioForm((current) =>
                          current
                            ? { ...current, [field.name]: value }
                            : current,
                        )
                      }
                    />
                  ))}
                </div>
                <div className="button-row scenario-button-row">
                  <button
                    className="primary-button"
                    type="button"
                    disabled={scenarioLoading}
                    onClick={handleScenarioPredict}
                  >
                    {scenarioLoading ? "Đang tính..." : "Tính lại"}
                  </button>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={resetScenario}
                  >
                    Reset mô phỏng
                  </button>
                </div>
                {scenarioError && <ErrorMessage message={scenarioError} />}
                {scenarioResult && typeof result.probability === "number" ? (
                  <div className="what-if-result">
                    <div>
                      <span>Ban đầu</span>
                      <strong>
                        {diabetesLabel(result.prediction)} -{" "}
                        {formatPercent(
                          getDominantProbability(result.probability)
                            .probability,
                        )}
                      </strong>
                    </div>
                    <div>
                      <span>Sau thay đổi</span>
                      <strong>
                        {diabetesLabel(scenarioResult.prediction)} -{" "}
                        {typeof scenarioResult.probability === "number"
                          ? formatPercent(
                              getDominantProbability(scenarioResult.probability)
                                .probability,
                            )
                          : "Không có xác suất"}
                      </strong>
                    </div>
                    {typeof scenarioResult.probability === "number" ? (
                      result.prediction === scenarioResult.prediction ? (
                        <div>
                          <span>Thay đổi</span>
                          <strong>
                            {(
                              (getDominantProbability(scenarioResult.probability)
                                .probability -
                                getDominantProbability(result.probability)
                                  .probability) *
                              100
                            ).toFixed(2)}{" "}
                            điểm phần trăm
                          </strong>
                        </div>
                      ) : (
                        <div>
                          <span>Kết luận</span>
                          <strong>
                            Dự đoán đã đổi từ {diabetesLabel(result.prediction)}{" "}
                            sang {diabetesLabel(scenarioResult.prediction)}
                          </strong>
                        </div>
                      )
                    ) : null}
                  </div>
                ) : null}
                <p className="helper-text">
                  Đây chỉ là mô phỏng phản ứng của mô hình khi thay đổi dữ liệu
                  đầu vào, không phải khuyến nghị y tế.
                </p>
              </>
            )}
          </ResultCard>
        </div>
      )}
    </section>
  );
}
