import { FormEvent, useEffect, useRef, useState } from "react";
import {
  HouseRequest,
  HouseCompareResponse,
  HouseResponse,
  ModelOption,
  compareHouseModels,
  getModelOptions,
  predictHouse,
} from "../api/predictionApi";
import ErrorMessage from "../components/ErrorMessage";
import FormField from "../components/FormField";
import InfoBox from "../components/InfoBox";
import LoadingState from "../components/LoadingState";
import ResultCard from "../components/ResultCard";
import SelectField from "../components/SelectField";

type HouseField = Exclude<keyof HouseRequest, "model">;

const fields: Array<{ name: HouseField; label: string }> = [
  { name: "Area", label: "Diện tích" },
  { name: "Frontage", label: "Mặt tiền" },
  { name: "Access Road", label: "Đường vào" },
  { name: "Floors", label: "Số tầng" },
  { name: "Bedrooms", label: "Phòng ngủ" },
  { name: "Bathrooms", label: "Phòng tắm" },
];

const initialForm: Record<HouseField, string> = {
  Area: "70",
  Frontage: "5",
  "Access Road": "6",
  Floors: "4",
  Bedrooms: "4",
  Bathrooms: "3",
};

const fallbackModelOptions: ModelOption[] = [
  { id: "linear_regression", name: "Linear Regression", recommended: false },
  { id: "knn_regressor", name: "KNN Regressor", recommended: false },
  {
    id: "decision_tree_regressor",
    name: "Decision Tree Regressor",
    recommended: false,
  },
  {
    id: "random_forest_regressor",
    name: "Random Forest Regressor",
    recommended: false,
  },
  {
    id: "gradient_boosting_regressor",
    name: "Gradient Boosting Regressor",
    recommended: true,
  },
];

const COMPARE_ALL_MODELS_ID = "__compare_all_models__";

const vndFormatter = new Intl.NumberFormat("vi-VN", {
  maximumFractionDigits: 0,
});

function formatBillionPriceAsVnd(priceInBillions: number) {
  const roundedBillions = Math.round(priceInBillions * 100) / 100;
  return `${vndFormatter.format(Math.round(roundedBillions * 1_000_000_000))} VNĐ`;
}

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

export default function HousePricePage() {
  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [error, setError] = useState("");
  const [compareError, setCompareError] = useState("");
  const [scenarioError, setScenarioError] = useState("");
  const [result, setResult] = useState<HouseResponse | null>(null);
  const [compareResult, setCompareResult] =
    useState<HouseCompareResponse | null>(null);
  const [originalForm, setOriginalForm] =
    useState<Record<HouseField, string> | null>(null);
  const [scenarioForm, setScenarioForm] =
    useState<Record<HouseField, string> | null>(null);
  const [scenarioResult, setScenarioResult] = useState<HouseResponse | null>(
    null,
  );
  const [modelOptions, setModelOptions] = useState(fallbackModelOptions);
  const [selectedModel, setSelectedModel] = useState(
    "gradient_boosting_regressor",
  );
  const [predictionModelId, setPredictionModelId] = useState<string | null>(
    null,
  );
  const userSelectedModelRef = useRef(false);

  useEffect(() => {
    let ignore = false;

    getModelOptions()
      .then((data) => {
        if (ignore) return;

        setModelOptions(data.house.models);
        if (!userSelectedModelRef.current) {
          setSelectedModel(data.house.default_model);
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
    const payload = {} as HouseRequest;

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
        setCompareResult(await compareHouseModels(payload));
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
      const prediction = await predictHouse(payload);
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
      setScenarioResult(await predictHouse(payload));
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
        <p className="eyebrow">Ước tính giá nhà</p>
        <h2>Dự đoán giá nhà Việt Nam</h2>
        <p>
          Nhập thông tin căn nhà để hệ thống ước tính giá dựa trên dữ liệu đã
          học.
        </p>
      </div>

      <div className="tool-grid">
        <form className="form-panel" onSubmit={handleSubmit}>
          <div className="form-grid">
            <SelectField
              id="house-model"
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
            <button
              className="secondary-button"
              type="button"
              onClick={clearForm}
            >
              Nhập lại
            </button>
          </div>
        </form>

        <aside className="result-panel">
          {loading && <LoadingState />}
          {error && <ErrorMessage message={error} />}
          {compareError && <ErrorMessage message={compareError} />}
          {result && (
            <ResultCard title="Giá nhà ước tính">
              {result.model ? (
                <p className="model-used">Model đã chọn: {result.model.name}</p>
              ) : null}
              <p className="result-value house-price">
                {formatBillionPriceAsVnd(result.predicted_price)}
              </p>
              <p className="result-explanation">
                Đây là mức giá mà mô hình dự đoán dựa trên 6 đặc điểm của căn
                nhà bạn vừa nhập.
              </p>

              <InfoBox title="Lưu ý về kết quả" tone="warning">
                Đây là giá ước tính từ mô hình Machine Learning dựa trên các
                thuộc tính hiện có trong bộ dữ liệu. Giá thực tế có thể còn phụ
                thuộc vào các yếu tố khác không nằm trong đầu vào của mô hình.
              </InfoBox>
            </ResultCard>
          )}
          {compareResult && (
            <>
              <ResultCard title="So sánh kết quả">
                <div className="comparison-list">
                  {compareResult.results.map((item) => (
                    <div className="comparison-row" key={item.model_id}>
                      <div>
                        <strong>{item.model_name}</strong>
                        {item.recommended ? (
                          <span className="badge">Khuyến nghị</span>
                        ) : null}
                      </div>
                      <span>{formatBillionPriceAsVnd(item.predicted_price)}</span>
                    </div>
                  ))}
                </div>
              </ResultCard>

              <ResultCard title="Mức phân tán giữa các mô hình">
                <div className="spread-grid">
                  <div>
                    <span>Thấp nhất</span>
                    <strong>
                      {formatBillionPriceAsVnd(compareResult.spread.min)}
                    </strong>
                  </div>
                  <div>
                    <span>Trung vị</span>
                    <strong>
                      {formatBillionPriceAsVnd(compareResult.spread.median)}
                    </strong>
                  </div>
                  <div>
                    <span>Cao nhất</span>
                    <strong>
                      {formatBillionPriceAsVnd(compareResult.spread.max)}
                    </strong>
                  </div>
                  <div>
                    <span>Khoảng chênh lệch</span>
                    <strong>
                      {formatBillionPriceAsVnd(compareResult.spread.range)}
                    </strong>
                  </div>
                </div>
                <p className="helper-text">
                  Khoảng này chỉ thể hiện sự khác biệt giữa 5 mô hình, không
                  phải khoảng tin cậy thống kê.
                </p>
              </ResultCard>
            </>
          )}
        </aside>
      </div>

      {result && (
        <div className="scenario-card">
          <ResultCard title="Mô phỏng thay đổi thông tin">
            {!scenarioForm ? (
              <button
                className="secondary-button"
                type="button"
                onClick={startScenario}
              >
                Thử thay đổi thông tin
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
                {scenarioResult && (
                  <div className="what-if-result">
                    <div>
                      <span>Ban đầu</span>
                      <strong>
                        {formatBillionPriceAsVnd(result.predicted_price)}
                      </strong>
                    </div>
                    <div>
                      <span>Sau thay đổi</span>
                      <strong>
                        {formatBillionPriceAsVnd(
                          scenarioResult.predicted_price,
                        )}
                      </strong>
                    </div>
                    <div>
                      <span>Chênh lệch</span>
                      <strong>
                        {formatBillionPriceAsVnd(
                          scenarioResult.predicted_price -
                            result.predicted_price,
                        )}
                      </strong>
                    </div>
                  </div>
                )}
                <p className="helper-text">
                  Khi thay đổi đầu vào theo cấu hình trên, mô hình đưa ra kết
                  quả dự đoán khác như hiển thị. Đây không phải phát biểu nhân
                  quả.
                </p>
              </>
            )}
          </ResultCard>
        </div>
      )}
    </section>
  );
}
