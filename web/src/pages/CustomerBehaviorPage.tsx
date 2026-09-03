import { FormEvent, useEffect, useRef, useState } from "react";
import {
  CustomerBehaviorCompareResponse,
  CustomerBehaviorRequest,
  CustomerBehaviorResponse,
  ModelOption,
  compareCustomerBehaviorModels,
  getModelOptions,
  predictCustomerBehavior,
} from "../api/predictionApi";
import ErrorMessage from "../components/ErrorMessage";
import FormField from "../components/FormField";
import InfoBox from "../components/InfoBox";
import LoadingState from "../components/LoadingState";
import ResultCard from "../components/ResultCard";
import SelectField from "../components/SelectField";

type CustomerField = Exclude<keyof CustomerBehaviorRequest, "model">;
type NumericCustomerField = {
  name: CustomerField;
  label: string;
  section: "Hồ sơ" | "Giao dịch" | "Phiên truy cập" | "Đánh giá";
  min?: number;
};

const numericFields: NumericCustomerField[] = [
  { name: "age", label: "Tuổi", section: "Hồ sơ", min: 0 },
  {
    name: "email_opt_in",
    label: "Nhận email marketing (0/1)",
    section: "Hồ sơ",
    min: 0,
  },
  { name: "has_app", label: "Có dùng app (0/1)", section: "Hồ sơ", min: 0 },
  {
    name: "customer_tenure_days",
    label: "Số ngày từ lúc đăng ký",
    section: "Hồ sơ",
    min: 0,
  },
  {
    name: "transaction_count",
    label: "Số giao dịch",
    section: "Giao dịch",
    min: 0,
  },
  {
    name: "completed_count",
    label: "Số giao dịch hoàn tất",
    section: "Giao dịch",
    min: 0,
  },
  {
    name: "cancelled_rate",
    label: "Tỷ lệ hủy đơn",
    section: "Giao dịch",
    min: 0,
  },
  {
    name: "refunded_rate",
    label: "Tỷ lệ hoàn tiền",
    section: "Giao dịch",
    min: 0,
  },
  {
    name: "total_spent",
    label: "Tổng chi tiêu",
    section: "Giao dịch",
    min: 0,
  },
  {
    name: "avg_order_value",
    label: "Giá trị đơn trung bình",
    section: "Giao dịch",
    min: 0,
  },
  {
    name: "total_quantity",
    label: "Tổng số lượng sản phẩm",
    section: "Giao dịch",
    min: 0,
  },
  {
    name: "avg_discount",
    label: "Discount trung bình",
    section: "Giao dịch",
    min: 0,
  },
  {
    name: "avg_shipping_cost",
    label: "Phí ship trung bình",
    section: "Giao dịch",
    min: 0,
  },
  {
    name: "unique_products",
    label: "Số sản phẩm khác nhau",
    section: "Giao dịch",
    min: 0,
  },
  {
    name: "transaction_recency_days",
    label: "Số ngày từ giao dịch gần nhất",
    section: "Giao dịch",
    min: 0,
  },
  {
    name: "session_count",
    label: "Số phiên truy cập",
    section: "Phiên truy cập",
    min: 0,
  },
  {
    name: "avg_duration_seconds",
    label: "Thời lượng phiên trung bình",
    section: "Phiên truy cập",
    min: 0,
  },
  {
    name: "total_pages_viewed",
    label: "Tổng page views",
    section: "Phiên truy cập",
    min: 0,
  },
  {
    name: "avg_pages_viewed",
    label: "Page views trung bình",
    section: "Phiên truy cập",
    min: 0,
  },
  {
    name: "conversion_rate",
    label: "Conversion rate",
    section: "Phiên truy cập",
    min: 0,
  },
  {
    name: "bounce_rate",
    label: "Bounce rate",
    section: "Phiên truy cập",
    min: 0,
  },
  {
    name: "cart_additions_sum",
    label: "Tổng lượt thêm giỏ hàng",
    section: "Phiên truy cập",
    min: 0,
  },
  {
    name: "avg_cart_additions",
    label: "Thêm giỏ hàng trung bình",
    section: "Phiên truy cập",
    min: 0,
  },
  {
    name: "session_recency_days",
    label: "Số ngày từ phiên gần nhất",
    section: "Phiên truy cập",
    min: 0,
  },
  {
    name: "review_count",
    label: "Số review",
    section: "Đánh giá",
    min: 0,
  },
  {
    name: "avg_rating",
    label: "Rating trung bình",
    section: "Đánh giá",
    min: 0,
  },
  {
    name: "low_rating_share",
    label: "Tỷ lệ rating thấp",
    section: "Đánh giá",
    min: 0,
  },
  {
    name: "helpful_votes_total",
    label: "Tổng helpful votes",
    section: "Đánh giá",
    min: 0,
  },
  {
    name: "verified_review_rate",
    label: "Tỷ lệ verified review",
    section: "Đánh giá",
    min: 0,
  },
];

const sections = ["Hồ sơ", "Giao dịch", "Phiên truy cập", "Đánh giá"] as const;

const selectFields = [
  {
    name: "gender",
    label: "Giới tính",
    options: ["F", "M", "Non-binary", "Prefer not to say"],
  },
  {
    name: "country",
    label: "Quốc gia",
    options: ["AU", "BR", "CA", "DE", "FR", "IN", "JP", "MX", "UK", "US"],
  },
  {
    name: "segment",
    label: "Segment",
    options: ["Budget Shopper", "Occasional Visitor", "Premium", "Regular", "VIP"],
  },
  {
    name: "favorite_payment_method",
    label: "Phương thức thanh toán",
    options: [
      "apple_pay",
      "bank_transfer",
      "credit_card",
      "debit_card",
      "google_pay",
      "paypal",
    ],
  },
  {
    name: "top_category",
    label: "Category quan tâm nhất",
    options: [
      "Automotive",
      "Beauty",
      "Books",
      "Clothing",
      "Electronics",
      "Food & Grocery",
      "Health",
      "Home & Garden",
      "Jewelry",
      "Music",
      "Office Supplies",
      "Pet Supplies",
      "Software",
      "Sports",
      "Toys",
    ],
  },
  {
    name: "top_brand",
    label: "Brand quan tâm nhất",
    options: [
      "AutoParts",
      "ClassicCo",
      "DigiTools",
      "EcoLiving",
      "FitGear",
      "FreshMarket",
      "GlowUp",
      "HomeEssentials",
      "NovaTech",
      "PetLife",
      "PlayTime",
      "PureBrand",
      "ReadMore",
      "ShineOn",
      "SoundWave",
      "StyleMax",
      "TechPro",
      "UrbanStyle",
      "WellBeing",
      "WorkSmart",
    ],
  },
  {
    name: "most_used_device",
    label: "Thiết bị dùng nhiều nhất",
    options: ["desktop", "mobile", "tablet"],
  },
  {
    name: "top_channel",
    label: "Kênh truy cập chính",
    options: ["direct", "email", "organic", "paid_search", "referral", "social"],
  },
] satisfies Array<{
  name: CustomerField;
  label: string;
  options: string[];
}>;

const initialForm: Record<CustomerField, string> = {
  age: "36",
  email_opt_in: "1",
  has_app: "1",
  customer_tenure_days: "820",
  transaction_count: "8",
  completed_count: "7",
  cancelled_rate: "0.05",
  refunded_rate: "0.02",
  total_spent: "520",
  avg_order_value: "65",
  total_quantity: "14",
  avg_discount: "0.08",
  avg_shipping_cost: "7.5",
  unique_products: "6",
  transaction_recency_days: "42",
  session_count: "18",
  avg_duration_seconds: "230",
  total_pages_viewed: "86",
  avg_pages_viewed: "4.8",
  conversion_rate: "0.28",
  bounce_rate: "0.18",
  cart_additions_sum: "12",
  avg_cart_additions: "0.7",
  session_recency_days: "12",
  review_count: "3",
  avg_rating: "4.2",
  low_rating_share: "0",
  helpful_votes_total: "5",
  verified_review_rate: "1",
  gender: "F",
  country: "US",
  segment: "Regular",
  favorite_payment_method: "credit_card",
  top_category: "Electronics",
  top_brand: "TechPro",
  most_used_device: "mobile",
  top_channel: "email",
  review_text_clean: "great product highly recommend fast delivery",
};

const fallbackModelOptions: ModelOption[] = [
  { id: "linear_svm_tabular", name: "Linear SVM (tabular)", recommended: true },
  {
    id: "logistic_regression_tabular",
    name: "Logistic Regression (tabular)",
    recommended: false,
  },
  { id: "decision_tree_tabular", name: "Decision Tree (tabular)", recommended: false },
  { id: "random_forest_tabular", name: "Random Forest (tabular)", recommended: false },
  {
    id: "gradient_boosting_tabular",
    name: "Gradient Boosting (tabular)",
    recommended: false,
  },
  {
    id: "text_tabular_logistic_regression",
    name: "Text + Tabular Logistic Regression",
    recommended: false,
  },
];

const COMPARE_ALL_MODELS_ID = "__compare_all_models__";

function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function customerLabel(prediction: number) {
  return prediction === 1 ? "Có nguy cơ rời bỏ" : "Đang gắn bó";
}

function toFriendlyError(message: string) {
  if (message.includes("Missing required field")) {
    return "Vui lòng nhập đầy đủ các trường.";
  }

  if (message.includes("Invalid number")) {
    return "Giá trị numeric phải là số hợp lệ.";
  }

  if (message.includes("Invalid text")) {
    return "Giá trị categorical/text không hợp lệ.";
  }

  if (message.includes("Failed to fetch") || message.includes("NetworkError")) {
    return "Không thể kết nối tới hệ thống. Vui lòng thử lại.";
  }

  return "Không thể hoàn tất dự đoán. Vui lòng kiểm tra dữ liệu và thử lại.";
}

function TextAreaField({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="form-field textarea-field full-width">
      <label htmlFor={id}>{label}</label>
      <textarea
        id={id}
        name={id}
        rows={4}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
      <p className="field-feedback"> </p>
    </div>
  );
}

export default function CustomerBehaviorPage() {
  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [error, setError] = useState("");
  const [compareError, setCompareError] = useState("");
  const [scenarioError, setScenarioError] = useState("");
  const [result, setResult] = useState<CustomerBehaviorResponse | null>(null);
  const [compareResult, setCompareResult] =
    useState<CustomerBehaviorCompareResponse | null>(null);
  const [originalForm, setOriginalForm] =
    useState<Record<CustomerField, string> | null>(null);
  const [scenarioForm, setScenarioForm] =
    useState<Record<CustomerField, string> | null>(null);
  const [scenarioResult, setScenarioResult] =
    useState<CustomerBehaviorResponse | null>(null);
  const [modelOptions, setModelOptions] = useState(fallbackModelOptions);
  const [selectedModel, setSelectedModel] = useState("linear_svm_tabular");
  const [predictionModelId, setPredictionModelId] = useState<string | null>(null);
  const userSelectedModelRef = useRef(false);

  useEffect(() => {
    let ignore = false;

    getModelOptions()
      .then((data) => {
        if (ignore) return;

        setModelOptions(data.customer_behavior.models);
        if (!userSelectedModelRef.current) {
          setSelectedModel(data.customer_behavior.default_model);
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
    const payload = {} as CustomerBehaviorRequest;
    const writablePayload = payload as Record<CustomerField, number | string>;

    for (const field of numericFields) {
      const rawValue = source[field.name].trim();
      const number = Number(rawValue);

      if (rawValue === "") {
        errors[field.name] = `Vui lòng nhập ${field.label}.`;
      } else if (!Number.isFinite(number)) {
        errors[field.name] = `${field.label} phải là số hợp lệ.`;
      } else {
        writablePayload[field.name] = number;
      }
    }

    for (const field of selectFields) {
      const rawValue = source[field.name].trim();
      if (!rawValue) {
        errors[field.name] = `Vui lòng chọn ${field.label}.`;
      } else {
        writablePayload[field.name] = rawValue;
      }
    }

    payload.review_text_clean = source.review_text_clean.trim();

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
    setScenarioError("");
    setResult(null);
    setCompareResult(null);
    setScenarioResult(null);
    setPredictionModelId(null);

    if (selectedModel === COMPARE_ALL_MODELS_ID) {
      setCompareLoading(true);
      setOriginalForm(null);
      setScenarioForm(null);

      try {
        setCompareResult(await compareCustomerBehaviorModels(payload));
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
      const prediction = await predictCustomerBehavior(payload);
      setResult(prediction);
      setPredictionModelId(prediction.model?.id ?? payload.model ?? selectedModel);
      setOriginalForm({ ...form });
      setScenarioForm({ ...form });
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
      setScenarioError("Giá trị mô phỏng phải hợp lệ trước khi tính lại.");
      return;
    }

    setScenarioLoading(true);
    setScenarioError("");

    try {
      setScenarioResult(await predictCustomerBehavior(payload));
    } catch (requestError) {
      console.error(requestError);
      setScenarioError("Không thể tính kết quả mô phỏng. Vui lòng thử lại.");
    } finally {
      setScenarioLoading(false);
    }
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

  function startScenario() {
    setScenarioForm(originalForm ?? form);
    setScenarioResult(null);
    setScenarioError("");
  }

  function resetScenario() {
    setScenarioForm(originalForm ?? form);
    setScenarioResult(null);
    setScenarioError("");
  }

  return (
    <section className="tool-page">
      <div className="page-intro compact">
        <p className="eyebrow">Customer Behavior</p>
        <h2>Dự đoán hành vi khách hàng</h2>
        <p>
          Nhập dữ liệu hồ sơ, giao dịch, phiên truy cập và review để dự đoán
          nguy cơ churn của khách hàng.
        </p>
      </div>

      <div className="tool-grid">
        <form className="form-panel" onSubmit={handleSubmit}>
          <div className="form-grid">
            <SelectField
              id="customer-model"
              label="Chọn model dự đoán"
              value={selectedModel}
              options={[
                ...modelOptions.map((model) => ({
                  value: model.id,
                  label: `${model.name}${model.recommended ? " (khuyến nghị)" : ""}`,
                })),
                {
                  value: COMPARE_ALL_MODELS_ID,
                  label: "So sánh 6 mô hình",
                },
              ]}
              onChange={handleModelChange}
            />

            {sections.map((section) => (
              <div className="form-field-group" key={section}>
                <h3>{section}</h3>
                <div className="form-grid nested">
                  {numericFields
                    .filter((field) => field.section === section)
                    .map((field) => (
                      <FormField
                        key={field.name}
                        id={field.name}
                        label={field.label}
                        min={field.min}
                        value={form[field.name]}
                        error={fieldErrors[field.name]}
                        onChange={(value) =>
                          setForm((current) => ({
                            ...current,
                            [field.name]: value,
                          }))
                        }
                      />
                    ))}
                </div>
              </div>
            ))}

            <div className="form-field-group">
              <h3>Phân loại và sở thích</h3>
              <div className="form-grid nested">
                {selectFields.map((field) => (
                  <SelectField
                    key={field.name}
                    id={field.name}
                    label={field.label}
                    value={form[field.name]}
                    options={field.options.map((option) => ({
                      value: option,
                      label: option,
                    }))}
                    onChange={(value) =>
                      setForm((current) => ({
                        ...current,
                        [field.name]: value,
                      }))
                    }
                  />
                ))}
              </div>
            </div>

            <TextAreaField
              id="review_text_clean"
              label="Review text đã clean"
              value={form.review_text_clean}
              onChange={(value) =>
                setForm((current) => ({
                  ...current,
                  review_text_clean: value,
                }))
              }
            />
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
            <button className="secondary-button" type="button" onClick={clearForm}>
              Nhập lại
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
                  <p className="result-label">{customerLabel(result.prediction)}</p>
                  <p className="helper-text">{result.interpretation}</p>
                </div>
              </div>

              {typeof result.churn_score === "number" ? (
                <section className="result-section">
                  <h3>Churn score</h3>
                  <p className="probability-main">
                    {formatPercent(result.churn_score)}
                  </p>
                  <p className="helper-text">
                    Với Linear SVM, score này được quy đổi từ decision function
                    để dễ đọc, không phải calibrated probability.
                  </p>
                </section>
              ) : null}

              <InfoBox title="Lưu ý" tone="warning">
                Kết quả này chỉ phục vụ mục đích học tập và minh họa Machine
                Learning. Đây không phải kết luận chắc chắn về hành vi khách hàng.
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
                      <span>{customerLabel(item.prediction)}</span>
                      <span>
                        {typeof item.churn_score === "number"
                          ? formatPercent(item.churn_score)
                          : "Không có score"}
                      </span>
                    </div>
                  ))}
                </div>
              </ResultCard>

              <ResultCard title="Mức đồng thuận giữa các mô hình">
                <p className="probability-main">
                  {formatPercent(compareResult.consensus.agreement_ratio)}
                </p>
                <p className="helper-text">
                  {compareResult.consensus.agreeing_models}/
                  {compareResult.consensus.total_models} mô hình đưa ra cùng
                  kết luận:{" "}
                  {customerLabel(compareResult.consensus.majority_prediction)}.
                </p>
              </ResultCard>
            </>
          )}
        </aside>
      </div>

      {result && (
        <div className="scenario-card">
          <ResultCard title="Mô phỏng thay đổi hành vi">
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
                  {numericFields.map((field) => (
                    <FormField
                      key={field.name}
                      id={`scenario-${field.name}`}
                      label={field.label}
                      min={field.min}
                      value={scenarioForm[field.name]}
                      onChange={(value) =>
                        setScenarioForm((current) =>
                          current ? { ...current, [field.name]: value } : current,
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
                {scenarioResult ? (
                  <div className="what-if-result">
                    <div>
                      <span>Ban đầu</span>
                      <strong>
                        {customerLabel(result.prediction)}
                        {typeof result.churn_score === "number"
                          ? ` - ${formatPercent(result.churn_score)}`
                          : ""}
                      </strong>
                    </div>
                    <div>
                      <span>Sau thay đổi</span>
                      <strong>
                        {customerLabel(scenarioResult.prediction)}
                        {typeof scenarioResult.churn_score === "number"
                          ? ` - ${formatPercent(scenarioResult.churn_score)}`
                          : ""}
                      </strong>
                    </div>
                  </div>
                ) : null}
                <p className="helper-text">
                  Mô phỏng chỉ thay đổi numeric features; categorical và review
                  text giữ nguyên so với input ban đầu.
                </p>
              </>
            )}
          </ResultCard>
        </div>
      )}
    </section>
  );
}
