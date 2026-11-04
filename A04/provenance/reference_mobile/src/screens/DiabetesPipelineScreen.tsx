import { useEffect, useRef, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import {
  DiabetesCompareResponse,
  DiabetesRequest,
  DiabetesResponse,
  ModelOption,
  compareDiabetesModels,
  getModelOptions,
  predictDiabetes,
} from "../api/predictionApi";
import AppButton from "../components/AppButton";
import ChoiceDropdown from "../components/ChoiceDropdown";
import ErrorMessage from "../components/ErrorMessage";
import FormInput from "../components/FormInput";
import InputSection from "../components/InputSection";
import ModelDropdown from "../components/ModelDropdown";
import ResultCard from "../components/ResultCard";

type DiabetesField = Exclude<keyof DiabetesRequest, "model">;
type Group = "Chỉ số sức khỏe" | "Thói quen và y tế" | "Đánh giá và nhân khẩu";
type Field = { name: DiabetesField; label: string; group: Group; binary?: boolean };

const fields: Field[] = [
  { name: "HighBP", label: "Huyết áp cao", group: "Chỉ số sức khỏe", binary: true },
  { name: "HighChol", label: "Cholesterol cao", group: "Chỉ số sức khỏe", binary: true },
  { name: "CholCheck", label: "Đã kiểm tra cholesterol", group: "Chỉ số sức khỏe", binary: true },
  { name: "BMI", label: "BMI", group: "Chỉ số sức khỏe" },
  { name: "Stroke", label: "Tiền sử đột quỵ", group: "Chỉ số sức khỏe", binary: true },
  { name: "HeartDiseaseorAttack", label: "Bệnh tim/heart attack", group: "Chỉ số sức khỏe", binary: true },
  { name: "Smoker", label: "Từng hút thuốc", group: "Thói quen và y tế", binary: true },
  { name: "PhysActivity", label: "Vận động thể chất", group: "Thói quen và y tế", binary: true },
  { name: "Fruits", label: "Ăn trái cây hằng ngày", group: "Thói quen và y tế", binary: true },
  { name: "Veggies", label: "Ăn rau hằng ngày", group: "Thói quen và y tế", binary: true },
  { name: "HvyAlcoholConsump", label: "Uống rượu nhiều", group: "Thói quen và y tế", binary: true },
  { name: "AnyHealthcare", label: "Có chăm sóc y tế", group: "Thói quen và y tế", binary: true },
  { name: "NoDocbcCost", label: "Không khám vì chi phí", group: "Thói quen và y tế", binary: true },
  { name: "GenHlth", label: "Sức khỏe tổng quát (1-5)", group: "Đánh giá và nhân khẩu" },
  { name: "MentHlth", label: "Ngày sức khỏe tinh thần kém", group: "Đánh giá và nhân khẩu" },
  { name: "PhysHlth", label: "Ngày sức khỏe thể chất kém", group: "Đánh giá và nhân khẩu" },
  { name: "DiffWalk", label: "Khó đi bộ/leo cầu thang", group: "Đánh giá và nhân khẩu", binary: true },
  { name: "Sex", label: "Giới tính source code", group: "Đánh giá và nhân khẩu", binary: true },
  { name: "Age", label: "Nhóm tuổi (1-13)", group: "Đánh giá và nhân khẩu" },
  { name: "Education", label: "Học vấn (1-6)", group: "Đánh giá và nhân khẩu" },
  { name: "Income", label: "Thu nhập (1-8)", group: "Đánh giá và nhân khẩu" },
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

export default function DiabetesPipelineScreen() {
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
    fields.forEach((field) => {
      const rawValue = form[field.name].trim();
      const number = Number(rawValue);
      if (!rawValue) errors[field.name] = `Vui lòng nhập ${field.label}.`;
      else if (!Number.isFinite(number)) errors[field.name] = `${field.label} phải là số.`;
      else writablePayload[field.name] = number;
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
    <View style={styles.container}>
      <View>
        <Text style={styles.eyebrow}>CDC/BRFSS health indicators</Text>
        <Text style={styles.title}>Dự đoán tiểu đường</Text>
        <Text style={styles.subtitle}>Theo dõi 21 feature CDC/BRFSS theo ba nhóm sức khỏe, thói quen và nhân khẩu.</Text>
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
        {groups.map((group, index) => (
          <InputSection key={group} title={group} defaultOpen={index === 0}>
            {fields.filter((field) => field.group === group).map((field) =>
              field.binary ? (
                <ChoiceDropdown
                  key={field.name}
                  label={field.label}
                  value={form[field.name]}
                  options={binaryOptions}
                  onChange={(value) => setForm((current) => ({ ...current, [field.name]: value }))}
                />
              ) : (
                <FormInput
                  key={field.name}
                  label={field.label}
                  value={form[field.name]}
                  error={fieldErrors[field.name]}
                  onChangeText={(value) => setForm((current) => ({ ...current, [field.name]: value }))}
                />
              ),
            )}
          </InputSection>
        ))}
        <View style={styles.buttonRow}>
          <AppButton label={compareLoading ? "Đang so sánh..." : loading ? "Đang dự đoán..." : "Dự đoán"} disabled={loading || compareLoading} onPress={handlePredict} />
          <AppButton label="Demo input" variant="secondary" onPress={() => setForm(initialForm)} />
        </View>
      </View>
      {error ? <ErrorMessage message={error} /> : null}
      {result ? (
        <ResultCard title="Kết quả dự đoán">
          <Text style={styles.modelUsed}>Model đã chọn: {result.model?.name ?? selectedModel}</Text>
          <Text style={styles.resultValue}>{labelFor(result.prediction)}</Text>
          {typeof result.probability === "number" ? <Text style={styles.bigMetric}>{formatPercent(result.probability)}</Text> : null}
          <Text style={styles.note}>Kết quả chỉ phục vụ học tập, không phải chẩn đoán y khoa.</Text>
        </ResultCard>
      ) : null}
      {compareResult ? (
        <ResultCard title="So sánh kết quả">
          {compareResult.results.map((item) => (
            <View key={item.model_id} style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>{item.model_name}</Text>
              <Text style={styles.summaryValue}>{labelFor(item.prediction)}</Text>
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
  buttonRow: { gap: 10, marginTop: 8 },
  resultValue: { color: "#172033", fontSize: 25, fontWeight: "900" },
  modelUsed: { color: "#64748b", fontSize: 14, fontWeight: "700" },
  bigMetric: { color: "#1d4ed8", fontSize: 30, fontWeight: "900" },
  note: { color: "#64748b", fontSize: 14, lineHeight: 21 },
  summaryRow: { flexDirection: "row", justifyContent: "space-between", gap: 12, paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: "#eef2f7" },
  summaryLabel: { flex: 1, color: "#64748b", fontWeight: "700" },
  summaryValue: { flex: 1, color: "#172033", fontWeight: "900", textAlign: "right" },
});
