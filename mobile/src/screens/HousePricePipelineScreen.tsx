import { useEffect, useRef, useState } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";
import {
  HouseCompareResponse,
  HouseRequest,
  HouseResponse,
  ModelOption,
  compareHouseModels,
  getModelOptions,
  predictHouse,
} from "../api/predictionApi";
import AppButton from "../components/AppButton";
import ChoiceDropdown from "../components/ChoiceDropdown";
import ErrorMessage from "../components/ErrorMessage";
import FormInput from "../components/FormInput";
import InputSection from "../components/InputSection";
import ModelDropdown from "../components/ModelDropdown";
import ResultCard from "../components/ResultCard";

type HouseField = Exclude<keyof HouseRequest, "model">;
type NumericField = { name: HouseField; label: string; optional?: boolean };
type TextFieldConfig = { name: HouseField; label: string };
type ChoiceField = { name: HouseField; label: string; options: string[] };

const numericFields: NumericField[] = [
  { name: "Area_m2", label: "Diện tích (m2)" },
  { name: "Frontage_m", label: "Mặt tiền (m)", optional: true },
  { name: "Access_Road_m", label: "Đường vào (m)", optional: true },
  { name: "Floors", label: "Số tầng" },
  { name: "Bedrooms", label: "Phòng ngủ", optional: true },
  { name: "Bathrooms", label: "Phòng tắm", optional: true },
];
const locationFields: TextFieldConfig[] = [
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

export default function HousePricePipelineScreen() {
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
    numericFields.forEach((field) => {
      const rawValue = form[field.name].trim();
      if (!rawValue && field.optional) {
        writablePayload[field.name] = null;
        return;
      }
      const number = Number(rawValue);
      if (!rawValue) errors[field.name] = `Vui lòng nhập ${field.label}.`;
      else if (!Number.isFinite(number)) errors[field.name] = `${field.label} phải là số.`;
      else writablePayload[field.name] = number;
    });
    [...locationFields, ...choiceFields].forEach((field) => {
      const rawValue = form[field.name].trim();
      if (!rawValue) errors[field.name] = `Vui lòng nhập ${field.label}.`;
      else writablePayload[field.name] = rawValue;
    });
    setFieldErrors(errors);
    payload.model = selectedModel;
    return Object.keys(errors).length ? null : payload;
  }

  async function handlePredict() {
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
    <View style={styles.container}>
      <View>
        <Text style={styles.eyebrow}>Vietnam house price</Text>
        <Text style={styles.title}>Dự đoán giá nhà</Text>
        <Text style={styles.subtitle}>Nhập 12 feature gồm thông số nhà, vị trí, pháp lý, nội thất và hướng.</Text>
      </View>
      <View style={styles.panel}>
        <ModelDropdown
          label="Chọn model dự đoán"
          value={selectedModel}
          options={[...modelOptions, { id: COMPARE_ALL_MODELS_ID, name: "So sánh model đang triển khai", recommended: false }]}
          onChange={(value) => {
            userSelectedModelRef.current = true;
            setSelectedModel(value);
          }}
        />
        <InputSection title="Thông số nhà" defaultOpen>
          {numericFields.map((field) => (
            <FormInput
              key={field.name}
              label={field.label}
              value={form[field.name]}
              error={fieldErrors[field.name]}
              onChangeText={(value) => setForm((current) => ({ ...current, [field.name]: value }))}
            />
          ))}
        </InputSection>
        <InputSection title="Vị trí">
          {locationFields.map((field) => (
            <View key={field.name} style={styles.field}>
              <Text style={styles.label}>{field.label}</Text>
              <TextInput value={form[field.name]} onChangeText={(value) => setForm((current) => ({ ...current, [field.name]: value }))} style={styles.input} />
              <Text style={styles.feedback}>{fieldErrors[field.name] ?? " "}</Text>
            </View>
          ))}
        </InputSection>
        <InputSection title="Pháp lý, nội thất và hướng">
          {choiceFields.map((field) => (
            <ChoiceDropdown
              key={field.name}
              label={field.label}
              value={form[field.name]}
              options={field.options.map((option) => ({ value: option, label: option }))}
              onChange={(value) => setForm((current) => ({ ...current, [field.name]: value }))}
            />
          ))}
        </InputSection>
        <View style={styles.buttonRow}>
          <AppButton label={compareLoading ? "Đang so sánh..." : loading ? "Đang dự đoán..." : "Dự đoán"} disabled={loading || compareLoading} onPress={handlePredict} />
          <AppButton label="Demo input" variant="secondary" onPress={() => setForm(initialForm)} />
        </View>
      </View>
      {error ? <ErrorMessage message={error} /> : null}
      {result ? (
        <ResultCard title="Giá nhà ước tính">
          <Text style={styles.modelUsed}>Model đã chọn: {result.model?.name ?? selectedModel}</Text>
          <Text style={styles.resultValue}>{formatBillionPriceAsVnd(result.predicted_price)}</Text>
          <Text style={styles.note}>Giá trị model trả về theo đơn vị tỷ VND.</Text>
        </ResultCard>
      ) : null}
      {compareResult ? (
        <ResultCard title="So sánh kết quả">
          {compareResult.results.map((item) => (
            <View key={item.model_id} style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>{item.model_name}</Text>
              <Text style={styles.summaryValue}>{formatBillionPriceAsVnd(item.predicted_price)}</Text>
            </View>
          ))}
        </ResultCard>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 16 },
  eyebrow: { color: "#2563eb", fontSize: 12, fontWeight: "800", textTransform: "uppercase" },
  title: { color: "#172033", fontSize: 30, fontWeight: "900" },
  subtitle: { color: "#64748b", fontSize: 15, lineHeight: 22, marginTop: 6 },
  panel: { gap: 10, padding: 18, borderWidth: 1, borderColor: "#d9e2ec", borderRadius: 8, backgroundColor: "#ffffff" },
  field: { gap: 7 },
  label: { color: "#243044", fontSize: 15, fontWeight: "800" },
  input: { minHeight: 46, borderWidth: 1, borderColor: "#cbd5e1", borderRadius: 8, paddingHorizontal: 12, backgroundColor: "#ffffff", color: "#172033", fontSize: 16 },
  feedback: { minHeight: 18, color: "#c2410c", fontSize: 13 },
  buttonRow: { gap: 10, marginTop: 8 },
  resultValue: { color: "#1d4ed8", fontSize: 28, fontWeight: "900", lineHeight: 34 },
  modelUsed: { color: "#64748b", fontSize: 14, fontWeight: "700" },
  note: { color: "#64748b", fontSize: 14, lineHeight: 21 },
  summaryRow: { flexDirection: "row", justifyContent: "space-between", gap: 12, paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: "#eef2f7" },
  summaryLabel: { flex: 1, color: "#64748b", fontWeight: "700" },
  summaryValue: { flex: 1, color: "#172033", fontWeight: "900", textAlign: "right" },
});
