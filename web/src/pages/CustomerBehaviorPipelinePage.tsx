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
import InputAccordion from "../components/InputAccordion";
import LoadingState from "../components/LoadingState";
import ResultCard from "../components/ResultCard";
import SelectField from "../components/SelectField";

type CustomerField = Exclude<keyof CustomerBehaviorRequest, "model">;
type Group = "Hồ sơ" | "Giao dịch" | "Phiên truy cập" | "Review" | "Chi tiêu theo category";
type NumericField = { name: CustomerField; label: string; group: Group; min?: number };
type ChoiceField = { name: CustomerField; label: string; options: string[] };

const numericFields: NumericField[] = [
  { name: "age", label: "Tuổi", group: "Hồ sơ", min: 0 },
  { name: "email_opt_in", label: "Nhận email (0/1)", group: "Hồ sơ", min: 0 },
  { name: "has_app", label: "Có dùng app (0/1)", group: "Hồ sơ", min: 0 },
  { name: "customer_tenure_days", label: "Ngày từ lúc đăng ký", group: "Hồ sơ", min: 0 },
  { name: "total_transactions", label: "Tổng giao dịch", group: "Giao dịch", min: 0 },
  { name: "total_quantity", label: "Tổng số lượng", group: "Giao dịch", min: 0 },
  { name: "avg_discount", label: "Discount trung bình", group: "Giao dịch", min: 0 },
  { name: "avg_shipping_cost", label: "Phí ship trung bình", group: "Giao dịch", min: 0 },
  { name: "completed_orders", label: "Đơn hoàn tất", group: "Giao dịch", min: 0 },
  { name: "total_spent", label: "Tổng chi tiêu", group: "Giao dịch", min: 0 },
  { name: "avg_order_value", label: "Giá trị đơn TB", group: "Giao dịch", min: 0 },
  { name: "category_diversity", label: "Số category đã mua", group: "Giao dịch", min: 0 },
  { name: "brand_diversity", label: "Số brand đã mua", group: "Giao dịch", min: 0 },
  { name: "cancelled_transactions", label: "Giao dịch bị hủy", group: "Giao dịch", min: 0 },
  { name: "completed_transactions", label: "Giao dịch hoàn tất", group: "Giao dịch", min: 0 },
  { name: "pending_transactions", label: "Giao dịch pending", group: "Giao dịch", min: 0 },
  { name: "refunded_transactions", label: "Giao dịch refund", group: "Giao dịch", min: 0 },
  { name: "days_since_last_transaction", label: "Ngày từ giao dịch cuối", group: "Giao dịch", min: 0 },
  { name: "session_count", label: "Số phiên", group: "Phiên truy cập", min: 0 },
  { name: "avg_session_duration", label: "Thời lượng phiên TB", group: "Phiên truy cập", min: 0 },
  { name: "total_pages_viewed", label: "Tổng page views", group: "Phiên truy cập", min: 0 },
  { name: "avg_pages_viewed", label: "Page views TB", group: "Phiên truy cập", min: 0 },
  { name: "conversion_rate", label: "Tỷ lệ chuyển đổi", group: "Phiên truy cập", min: 0 },
  { name: "bounce_rate", label: "Tỷ lệ thoát", group: "Phiên truy cập", min: 0 },
  { name: "cart_additions_total", label: "Tổng add-to-cart", group: "Phiên truy cập", min: 0 },
  { name: "cart_additions_avg", label: "Add-to-cart TB", group: "Phiên truy cập", min: 0 },
  { name: "device_diversity", label: "Số loại thiết bị", group: "Phiên truy cập", min: 0 },
  { name: "channel_diversity", label: "Số kênh truy cập", group: "Phiên truy cập", min: 0 },
  { name: "days_since_last_session", label: "Ngày từ phiên cuối", group: "Phiên truy cập", min: 0 },
  { name: "review_count", label: "Số review", group: "Review", min: 0 },
  { name: "avg_rating", label: "Rating TB", group: "Review", min: 0 },
  { name: "low_rating_share", label: "Tỷ lệ rating thấp", group: "Review", min: 0 },
  { name: "verified_review_share", label: "Tỷ lệ verified review", group: "Review", min: 0 },
  { name: "helpful_votes_total", label: "Tổng helpful votes", group: "Review", min: 0 },
  { name: "days_since_last_review", label: "Ngày từ review cuối", group: "Review", min: 0 },
  { name: "spend_category_clothing", label: "Clothing", group: "Chi tiêu theo category", min: 0 },
  { name: "spend_category_electronics", label: "Electronics", group: "Chi tiêu theo category", min: 0 },
  { name: "spend_category_food_grocery", label: "Food & Grocery", group: "Chi tiêu theo category", min: 0 },
  { name: "spend_category_health", label: "Health", group: "Chi tiêu theo category", min: 0 },
  { name: "spend_category_jewelry", label: "Jewelry", group: "Chi tiêu theo category", min: 0 },
  { name: "spend_category_office_supplies", label: "Office Supplies", group: "Chi tiêu theo category", min: 0 },
  { name: "spend_category_pet_supplies", label: "Pet Supplies", group: "Chi tiêu theo category", min: 0 },
  { name: "spend_category_sports", label: "Sports", group: "Chi tiêu theo category", min: 0 },
];

const groups: Group[] = ["Hồ sơ", "Giao dịch", "Phiên truy cập", "Review", "Chi tiêu theo category"];
const choiceFields: ChoiceField[] = [
  { name: "gender", label: "Giới tính", options: ["F", "M", "Non-binary", "Prefer not to say"] },
  { name: "country", label: "Quốc gia", options: ["AU", "BR", "CA", "DE", "FR", "IN", "JP", "MX", "UK", "US"] },
  { name: "segment", label: "Phân khúc", options: ["Budget Shopper", "Occasional Visitor", "Premium", "Regular", "VIP"] },
  { name: "top_category", label: "Top category", options: ["Automotive", "Beauty", "Books", "Clothing", "Electronics", "Food & Grocery", "Health", "Home & Garden", "Jewelry", "Music", "Office Supplies", "Pet Supplies", "Software", "Sports", "Toys"] },
  { name: "top_brand", label: "Top brand", options: ["AutoParts", "ClassicCo", "DigiTools", "EcoLiving", "FitGear", "FreshMarket", "GlowUp", "HomeEssentials", "NovaTech", "PetLife", "PlayTime", "PureBrand", "ReadMore", "ShineOn", "SoundWave", "StyleMax", "TechPro", "UrbanStyle", "WellBeing", "WorkSmart"] },
  { name: "top_device", label: "Top device", options: ["desktop", "mobile", "tablet"] },
  { name: "top_channel", label: "Top channel", options: ["direct", "email", "organic", "paid_search", "referral", "social"] },
];

const initialForm: Record<CustomerField, string> = {
  age: "28",
  email_opt_in: "0",
  has_app: "0",
  customer_tenure_days: "1692",
  total_transactions: "22",
  total_quantity: "29",
  avg_discount: "5.2272727272727275",
  avg_shipping_cost: "5.260454545454546",
  completed_orders: "15",
  total_spent: "649.36",
  avg_order_value: "43.29066666666667",
  category_diversity: "8",
  brand_diversity: "11",
  cancelled_transactions: "2",
  completed_transactions: "15",
  pending_transactions: "2",
  refunded_transactions: "3",
  session_count: "8",
  avg_session_duration: "696.875",
  total_pages_viewed: "86",
  avg_pages_viewed: "10.75",
  conversion_rate: "0.125",
  bounce_rate: "0.125",
  cart_additions_total: "5",
  cart_additions_avg: "0.625",
  device_diversity: "3",
  channel_diversity: "5",
  review_count: "0",
  avg_rating: "0",
  low_rating_share: "0",
  verified_review_share: "0",
  helpful_votes_total: "0",
  days_since_last_transaction: "4",
  days_since_last_session: "41",
  days_since_last_review: "670",
  spend_category_clothing: "55.96",
  spend_category_electronics: "218.44",
  spend_category_food_grocery: "16.42",
  spend_category_health: "29.17",
  spend_category_jewelry: "0",
  spend_category_office_supplies: "0",
  spend_category_pet_supplies: "0",
  spend_category_sports: "0",
  gender: "M",
  country: "BR",
  segment: "Premium",
  top_category: "Music",
  top_brand: "NovaTech",
  top_device: "mobile",
  top_channel: "social",
  review_text_all: "",
};

const fallbackModelOptions: ModelOption[] = [{ id: "improved_dnn", name: "Improved DNN", recommended: true }];
const COMPARE_ALL_MODELS_ID = "__compare_all_models__";

function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function customerLabel(prediction: number) {
  return prediction === 1 ? "Có nguy cơ churn" : "Đang gắn bó";
}

function TextAreaField({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <div className="form-field textarea-field full-width">
      <label htmlFor="review_text_all">Review text tổng hợp</label>
      <textarea id="review_text_all" name="review_text_all" rows={4} value={value} onChange={(event) => onChange(event.target.value)} />
      <p className="field-feedback"> </p>
    </div>
  );
}

export default function CustomerBehaviorPipelinePage() {
  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<CustomerBehaviorResponse | null>(null);
  const [compareResult, setCompareResult] = useState<CustomerBehaviorCompareResponse | null>(null);
  const [modelOptions, setModelOptions] = useState(fallbackModelOptions);
  const [selectedModel, setSelectedModel] = useState("improved_dnn");
  const userSelectedModelRef = useRef(false);

  useEffect(() => {
    let ignore = false;
    getModelOptions()
      .then((data) => {
        if (ignore) return;
        setModelOptions(data.customer_behavior.models);
        if (!userSelectedModelRef.current) setSelectedModel(data.customer_behavior.default_model);
      })
      .catch(console.error);
    return () => {
      ignore = true;
    };
  }, []);

  function buildPayload() {
    const errors: Record<string, string> = {};
    const payload = {} as CustomerBehaviorRequest;
    const writablePayload = payload as Record<CustomerField, number | string>;

    for (const field of numericFields) {
      const rawValue = form[field.name].trim();
      const number = Number(rawValue);
      if (!rawValue) errors[field.name] = `Vui lòng nhập ${field.label}.`;
      else if (!Number.isFinite(number)) errors[field.name] = `${field.label} phải là số.`;
      else writablePayload[field.name] = number;
    }

    for (const field of choiceFields) {
      const rawValue = form[field.name].trim();
      if (!rawValue) errors[field.name] = `Vui lòng chọn ${field.label}.`;
      else writablePayload[field.name] = rawValue;
    }

    writablePayload.review_text_all = form.review_text_all.trim();
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
      if (selectedModel === COMPARE_ALL_MODELS_ID) setCompareResult(await compareCustomerBehaviorModels(payload));
      else setResult(await predictCustomerBehavior(payload));
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
        <p className="eyebrow">Customer behavior</p>
        <h2>Dự đoán churn</h2>
        <p>Schema mới có 51 feature cấp customer, chia theo hồ sơ, giao dịch, phiên truy cập, review và chi tiêu.</p>
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
                { value: COMPARE_ALL_MODELS_ID, label: "So sánh model đang triển khai" },
              ]}
              onChange={(value) => {
                userSelectedModelRef.current = true;
                setSelectedModel(value);
              }}
            />

            <InputAccordion title="Phân loại và sở thích" defaultOpen>
              <div className="form-grid nested">
                {choiceFields.map((field) => (
                  <SelectField
                    key={field.name}
                    id={field.name}
                    label={field.label}
                    value={form[field.name]}
                    options={field.options.map((option) => ({ value: option, label: option }))}
                    fullWidth={false}
                    onChange={(value) => setForm((current) => ({ ...current, [field.name]: value }))}
                  />
                ))}
              </div>
            </InputAccordion>

            {groups.map((group) => (
              <InputAccordion title={group} key={group}>
                <div className="form-grid nested">
                  {numericFields.filter((field) => field.group === group).map((field) => (
                    <FormField
                      key={field.name}
                      id={field.name}
                      label={field.label}
                      min={field.min}
                      value={form[field.name]}
                      error={fieldErrors[field.name]}
                      onChange={(value) => setForm((current) => ({ ...current, [field.name]: value }))}
                    />
                  ))}
                </div>
              </InputAccordion>
            ))}

            <TextAreaField value={form.review_text_all} onChange={(value) => setForm((current) => ({ ...current, review_text_all: value }))} />
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
                <div>
                  <p className="result-label">{customerLabel(result.prediction)}</p>
                  <p className="helper-text">{result.interpretation}</p>
                </div>
              </div>
              {typeof result.churn_score === "number" ? (
                <section className="result-section">
                  <h3>Churn score</h3>
                  <p className="probability-main">{formatPercent(result.churn_score)}</p>
                </section>
              ) : null}
              <InfoBox title="Lưu ý" tone="warning">
                Kết quả chỉ phục vụ học tập và minh họa Machine Learning.
              </InfoBox>
            </ResultCard>
          )}
          {compareResult && (
            <ResultCard title="So sánh kết quả">
              <div className="comparison-list">
                {compareResult.results.map((item) => (
                  <div className="comparison-row" key={item.model_id}>
                    <strong>{item.model_name}</strong>
                    <span>{customerLabel(item.prediction)}</span>
                    <span>{typeof item.churn_score === "number" ? formatPercent(item.churn_score) : "N/A"}</span>
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
