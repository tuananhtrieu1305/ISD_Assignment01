import { useEffect, useRef, useState } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";
import {
  CustomerBehaviorCompareResponse,
  CustomerBehaviorRequest,
  CustomerBehaviorResponse,
  ModelOption,
  compareCustomerBehaviorModels,
  getModelOptions,
  predictCustomerBehavior,
} from "../api/predictionApi";
import AppButton from "../components/AppButton";
import ChoiceDropdown from "../components/ChoiceDropdown";
import ErrorMessage from "../components/ErrorMessage";
import FormInput from "../components/FormInput";
import InputSection from "../components/InputSection";
import ModelDropdown from "../components/ModelDropdown";
import ResultCard from "../components/ResultCard";

type CustomerField = Exclude<keyof CustomerBehaviorRequest, "model">;
type Group = "Hồ sơ" | "Giao dịch" | "Phiên truy cập" | "Review" | "Chi tiêu theo category";
type NumericField = { name: CustomerField; label: string; group: Group };
type ChoiceField = { name: CustomerField; label: string; options: string[] };

const numericFields: NumericField[] = [
  { name: "age", label: "Tuổi", group: "Hồ sơ" },
  { name: "email_opt_in", label: "Nhận email (0/1)", group: "Hồ sơ" },
  { name: "has_app", label: "Có dùng app (0/1)", group: "Hồ sơ" },
  { name: "customer_tenure_days", label: "Ngày từ lúc đăng ký", group: "Hồ sơ" },
  { name: "total_transactions", label: "Tổng giao dịch", group: "Giao dịch" },
  { name: "total_quantity", label: "Tổng số lượng", group: "Giao dịch" },
  { name: "avg_discount", label: "Discount trung bình", group: "Giao dịch" },
  { name: "avg_shipping_cost", label: "Phí ship trung bình", group: "Giao dịch" },
  { name: "completed_orders", label: "Đơn hoàn tất", group: "Giao dịch" },
  { name: "total_spent", label: "Tổng chi tiêu", group: "Giao dịch" },
  { name: "avg_order_value", label: "Giá trị đơn TB", group: "Giao dịch" },
  { name: "category_diversity", label: "Số category đã mua", group: "Giao dịch" },
  { name: "brand_diversity", label: "Số brand đã mua", group: "Giao dịch" },
  { name: "cancelled_transactions", label: "Giao dịch bị hủy", group: "Giao dịch" },
  { name: "completed_transactions", label: "Giao dịch hoàn tất", group: "Giao dịch" },
  { name: "pending_transactions", label: "Giao dịch pending", group: "Giao dịch" },
  { name: "refunded_transactions", label: "Giao dịch refund", group: "Giao dịch" },
  { name: "days_since_last_transaction", label: "Ngày từ giao dịch cuối", group: "Giao dịch" },
  { name: "session_count", label: "Số phiên", group: "Phiên truy cập" },
  { name: "avg_session_duration", label: "Thời lượng phiên TB", group: "Phiên truy cập" },
  { name: "total_pages_viewed", label: "Tổng page views", group: "Phiên truy cập" },
  { name: "avg_pages_viewed", label: "Page views TB", group: "Phiên truy cập" },
  { name: "conversion_rate", label: "Tỷ lệ chuyển đổi", group: "Phiên truy cập" },
  { name: "bounce_rate", label: "Tỷ lệ thoát", group: "Phiên truy cập" },
  { name: "cart_additions_total", label: "Tổng add-to-cart", group: "Phiên truy cập" },
  { name: "cart_additions_avg", label: "Add-to-cart TB", group: "Phiên truy cập" },
  { name: "device_diversity", label: "Số loại thiết bị", group: "Phiên truy cập" },
  { name: "channel_diversity", label: "Số kênh truy cập", group: "Phiên truy cập" },
  { name: "days_since_last_session", label: "Ngày từ phiên cuối", group: "Phiên truy cập" },
  { name: "review_count", label: "Số review", group: "Review" },
  { name: "avg_rating", label: "Rating TB", group: "Review" },
  { name: "low_rating_share", label: "Tỷ lệ rating thấp", group: "Review" },
  { name: "verified_review_share", label: "Tỷ lệ verified review", group: "Review" },
  { name: "helpful_votes_total", label: "Tổng helpful votes", group: "Review" },
  { name: "days_since_last_review", label: "Ngày từ review cuối", group: "Review" },
  { name: "spend_category_clothing", label: "Clothing", group: "Chi tiêu theo category" },
  { name: "spend_category_electronics", label: "Electronics", group: "Chi tiêu theo category" },
  { name: "spend_category_food_grocery", label: "Food & Grocery", group: "Chi tiêu theo category" },
  { name: "spend_category_health", label: "Health", group: "Chi tiêu theo category" },
  { name: "spend_category_jewelry", label: "Jewelry", group: "Chi tiêu theo category" },
  { name: "spend_category_office_supplies", label: "Office Supplies", group: "Chi tiêu theo category" },
  { name: "spend_category_pet_supplies", label: "Pet Supplies", group: "Chi tiêu theo category" },
  { name: "spend_category_sports", label: "Sports", group: "Chi tiêu theo category" },
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

export default function CustomerBehaviorPipelineScreen() {
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
    numericFields.forEach((field) => {
      const rawValue = form[field.name].trim();
      const number = Number(rawValue);
      if (!rawValue) errors[field.name] = `Vui lòng nhập ${field.label}.`;
      else if (!Number.isFinite(number)) errors[field.name] = `${field.label} phải là số.`;
      else writablePayload[field.name] = number;
    });
    choiceFields.forEach((field) => {
      const rawValue = form[field.name].trim();
      if (!rawValue) errors[field.name] = `Vui lòng chọn ${field.label}.`;
      else writablePayload[field.name] = rawValue;
    });
    writablePayload.review_text_all = form.review_text_all.trim();
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
    <View style={styles.container}>
      <View>
        <Text style={styles.eyebrow}>Customer behavior</Text>
        <Text style={styles.title}>Dự đoán churn</Text>
        <Text style={styles.subtitle}>Schema mới có 51 feature, chia theo hồ sơ, giao dịch, phiên truy cập, review và chi tiêu.</Text>
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
        <InputSection title="Phân loại và sở thích" defaultOpen>
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
        {groups.map((group) => (
          <InputSection key={group} title={group}>
            {numericFields.filter((field) => field.group === group).map((field) => (
              <FormInput
                key={field.name}
                label={field.label}
                value={form[field.name]}
                error={fieldErrors[field.name]}
                onChangeText={(value) => setForm((current) => ({ ...current, [field.name]: value }))}
              />
            ))}
          </InputSection>
        ))}
        <InputSection title="Review text tổng hợp">
          <TextInput
            accessibilityLabel="Review text tổng hợp"
            value={form.review_text_all}
            multiline
            textAlignVertical="top"
            onChangeText={(value) => setForm((current) => ({ ...current, review_text_all: value }))}
            style={styles.textArea}
          />
        </InputSection>
        <View style={styles.buttonRow}>
          <AppButton label={compareLoading ? "Đang so sánh..." : loading ? "Đang dự đoán..." : "Dự đoán"} disabled={loading || compareLoading} onPress={handlePredict} />
          <AppButton label="Demo input" variant="secondary" onPress={() => setForm(initialForm)} />
        </View>
      </View>
      {error ? <ErrorMessage message={error} /> : null}
      {result ? (
        <ResultCard title="Kết quả dự đoán">
          <Text style={styles.modelUsed}>Model đã chọn: {result.model?.name ?? selectedModel}</Text>
          <Text style={styles.resultValue}>{customerLabel(result.prediction)}</Text>
          {typeof result.churn_score === "number" ? <Text style={styles.bigMetric}>{formatPercent(result.churn_score)}</Text> : null}
          <Text style={styles.note}>{result.interpretation}</Text>
        </ResultCard>
      ) : null}
      {compareResult ? (
        <ResultCard title="So sánh kết quả">
          {compareResult.results.map((item) => (
            <View key={item.model_id} style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>{item.model_name}</Text>
              <Text style={styles.summaryValue}>{customerLabel(item.prediction)}</Text>
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
  textArea: { minHeight: 96, borderWidth: 1, borderColor: "#cbd5e1", borderRadius: 8, paddingHorizontal: 12, paddingVertical: 10, backgroundColor: "#ffffff", color: "#172033", fontSize: 16 },
  summaryRow: { flexDirection: "row", justifyContent: "space-between", gap: 12, paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: "#eef2f7" },
  summaryLabel: { flex: 1, color: "#64748b", fontWeight: "700" },
  summaryValue: { flex: 1, color: "#172033", fontWeight: "900", textAlign: "right" },
});
