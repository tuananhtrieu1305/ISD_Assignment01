import { FormEvent, useEffect, useRef, useState } from "react";
import {
  HouseCompareResponse,
  HouseRequest,
  HouseResponse,
  ModelOption,
  compareHouseModels,
  getModelOptions,
  predictHouse,
} from "../api/predictionApi";
import ErrorMessage from "../components/ErrorMessage";
import FormField from "../components/FormField";
import InfoBox from "../components/InfoBox";
import InputAccordion from "../components/InputAccordion";
import LoadingState from "../components/LoadingState";
import ResultCard from "../components/ResultCard";
import SelectField from "../components/SelectField";

type HouseField = Exclude<keyof HouseRequest, "model">;
type NumericField = { name: HouseField; label: string; optional?: boolean; min?: number };
type TextField = { name: HouseField; label: string };
type ChoiceField = { name: HouseField; label: string; options: string[] };

const numericFields: NumericField[] = [
  { name: "Area_m2", label: "Diện tích (m2)", min: 1 },
  { name: "Frontage_m", label: "Mặt tiền (m)", optional: true, min: 0 },
  { name: "Access_Road_m", label: "Đường vào (m)", optional: true, min: 0 },
  { name: "Floors", label: "Số tầng", min: 1 },
  { name: "Bedrooms", label: "Phòng ngủ", optional: true, min: 0 },
  { name: "Bathrooms", label: "Phòng tắm", optional: true, min: 0 },
];

const locationFields: TextField[] = [
  { name: "city", label: "Tỉnh/thành phố" },
  { name: "district", label: "Quận/huyện" },
];

const directionOptions = ["Unknown", "Bắc", "Nam", "Tây", "Đông", "Tây - Bắc", "Tây - Nam", "Đông - Bắc", "Đông - Nam"];
const choiceFields: ChoiceField[] = [
  { name: "Legal status", label: "Pháp lý", options: ["Unknown", "Have certificate", "Sale contract"] },
  { name: "Furniture state", label: "Nội thất", options: ["Unknown", "Basic", "Full"] },
  { name: "House direction", label: "Hướng nhà", options: directionOptions },
  { name: "Balcony direction", label: "Hướng ban công", options: directionOptions },
];

const initialForm: Record<HouseField, string> = {
  Area_m2: "84",
  Frontage_m: "",
  Access_Road_m: "",
  Floors: "4",
  Bedrooms: "",
  Bathrooms: "",
  city: "Hưng Yên",
  district: "Văn Giang",
  "Legal status": "Have certificate",
  "Furniture state": "Unknown",
  "House direction": "Unknown",
  "Balcony direction": "Unknown",
};

const fallbackModelOptions: ModelOption[] = [{ id: "improved_dnn", name: "Improved DNN", recommended: true }];
const COMPARE_ALL_MODELS_ID = "__compare_all_models__";
const vndFormatter = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 0 });

function formatBillionPriceAsVnd(priceInBillions: number) {
  return `${vndFormatter.format(Math.round(priceInBillions * 1_000_000_000))} VND`;
}

function TextInputField({
  id,
  label,
  value,
  error,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  error?: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <input id={id} name={id} type="text" value={value} aria-invalid={Boolean(error)} onChange={(event) => onChange(event.target.value)} />
      <p className="field-feedback">{error ?? " "}</p>
    </div>
  );
}

export default function HousePricePipelinePage() {
  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<HouseResponse | null>(null);
  const [compareResult, setCompareResult] = useState<HouseCompareResponse | null>(null);
  const [modelOptions, setModelOptions] = useState(fallbackModelOptions);
  const [selectedModel, setSelectedModel] = useState("improved_dnn");
  const userSelectedModelRef = useRef(false);

  useEffect(() => {
    let ignore = false;
    getModelOptions()
      .then((data) => {
        if (ignore) return;
        setModelOptions(data.house.models);
        if (!userSelectedModelRef.current) setSelectedModel(data.house.default_model);
      })
      .catch(console.error);
    return () => {
      ignore = true;
    };
  }, []);

  function buildPayload() {
    const errors: Record<string, string> = {};
    const payload = {} as HouseRequest;
    const writablePayload = payload as Record<HouseField, number | string | null>;

    for (const field of numericFields) {
      const rawValue = form[field.name].trim();
      if (!rawValue && field.optional) {
        writablePayload[field.name] = null;
        continue;
      }
      const number = Number(rawValue);
      if (!rawValue) errors[field.name] = `Vui lòng nhập ${field.label}.`;
      else if (!Number.isFinite(number)) errors[field.name] = `${field.label} phải là số.`;
      else writablePayload[field.name] = number;
    }

    for (const field of [...locationFields, ...choiceFields]) {
      const rawValue = form[field.name].trim();
      if (!rawValue) errors[field.name] = `Vui lòng nhập ${field.label}.`;
      else writablePayload[field.name] = rawValue;
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
      if (selectedModel === COMPARE_ALL_MODELS_ID) setCompareResult(await compareHouseModels(payload));
      else setResult(await predictHouse(payload));
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
        <p className="eyebrow">Vietnam house price</p>
        <h2>Dự đoán giá nhà</h2>
        <p>Nhập 12 feature gồm thông số nhà, vị trí, pháp lý, nội thất và hướng.</p>
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
                { value: COMPARE_ALL_MODELS_ID, label: "So sánh model đang triển khai" },
              ]}
              onChange={(value) => {
                userSelectedModelRef.current = true;
                setSelectedModel(value);
              }}
            />
            <InputAccordion title="Thông số nhà" defaultOpen>
              <div className="form-grid nested">
                {numericFields.map((field) => (
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
            <InputAccordion title="Vị trí">
              <div className="form-grid nested">
                {locationFields.map((field) => (
                  <TextInputField
                    key={field.name}
                    id={field.name}
                    label={field.label}
                    value={form[field.name]}
                    error={fieldErrors[field.name]}
                    onChange={(value) => setForm((current) => ({ ...current, [field.name]: value }))}
                  />
                ))}
              </div>
            </InputAccordion>
            <InputAccordion title="Pháp lý, nội thất và hướng">
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
            <ResultCard title="Giá nhà ước tính">
              <p className="model-used">Model đã chọn: {result.model?.name ?? selectedModel}</p>
              <p className="result-value house-price">{formatBillionPriceAsVnd(result.predicted_price)}</p>
              <p className="helper-text">Giá trị model trả về theo đơn vị tỷ VND trong pipeline mới.</p>
              <InfoBox title="Lưu ý về kết quả" tone="warning">
                Đây là giá ước tính từ model Machine Learning, không phải giá giao dịch thực tế.
              </InfoBox>
            </ResultCard>
          )}
          {compareResult && (
            <ResultCard title="So sánh kết quả">
              <div className="comparison-list">
                {compareResult.results.map((item) => (
                  <div className="comparison-row" key={item.model_id}>
                    <strong>{item.model_name}</strong>
                    <span>{formatBillionPriceAsVnd(item.predicted_price)}</span>
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
