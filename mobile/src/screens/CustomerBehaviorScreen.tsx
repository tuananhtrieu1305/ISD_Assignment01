// @ts-nocheck
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
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
import ErrorMessage from "../components/ErrorMessage";
import FormInput from "../components/FormInput";
import ModelDropdown from "../components/ModelDropdown";
import ResultCard from "../components/ResultCard";

type CustomerField = Exclude<keyof CustomerBehaviorRequest, "model">;
type NumericCustomerField = {
  name: CustomerField;
  label: string;
  section: "Hồ sơ" | "Giao dịch" | "Phiên truy cập" | "Đánh giá";
};

const numericFields: NumericCustomerField[] = [
  { name: "age", label: "Tuổi", section: "Hồ sơ" },
  { name: "email_opt_in", label: "Nhận email marketing (0/1)", section: "Hồ sơ" },
  { name: "has_app", label: "Có dùng app (0/1)", section: "Hồ sơ" },
  { name: "customer_tenure_days", label: "Số ngày từ lúc đăng ký", section: "Hồ sơ" },
  { name: "transaction_count", label: "Số giao dịch", section: "Giao dịch" },
  { name: "completed_count", label: "Số giao dịch hoàn tất", section: "Giao dịch" },
  { name: "cancelled_rate", label: "Tỷ lệ hủy đơn", section: "Giao dịch" },
  { name: "refunded_rate", label: "Tỷ lệ hoàn tiền", section: "Giao dịch" },
  { name: "total_spent", label: "Tổng chi tiêu", section: "Giao dịch" },
  { name: "avg_order_value", label: "Giá trị đơn trung bình", section: "Giao dịch" },
  { name: "total_quantity", label: "Tổng số lượng sản phẩm", section: "Giao dịch" },
  { name: "avg_discount", label: "Discount trung bình", section: "Giao dịch" },
  { name: "avg_shipping_cost", label: "Phí ship trung bình", section: "Giao dịch" },
  { name: "unique_products", label: "Số sản phẩm khác nhau", section: "Giao dịch" },
  {
    name: "transaction_recency_days",
    label: "Số ngày từ giao dịch gần nhất",
    section: "Giao dịch",
  },
  { name: "session_count", label: "Số phiên truy cập", section: "Phiên truy cập" },
  {
    name: "avg_duration_seconds",
    label: "Thời lượng phiên trung bình",
    section: "Phiên truy cập",
  },
  { name: "total_pages_viewed", label: "Tổng page views", section: "Phiên truy cập" },
  {
    name: "avg_pages_viewed",
    label: "Page views trung bình",
    section: "Phiên truy cập",
  },
  { name: "conversion_rate", label: "Conversion rate", section: "Phiên truy cập" },
  { name: "bounce_rate", label: "Bounce rate", section: "Phiên truy cập" },
  {
    name: "cart_additions_sum",
    label: "Tổng lượt thêm giỏ hàng",
    section: "Phiên truy cập",
  },
  {
    name: "avg_cart_additions",
    label: "Thêm giỏ hàng trung bình",
    section: "Phiên truy cập",
  },
  {
    name: "session_recency_days",
    label: "Số ngày từ phiên gần nhất",
    section: "Phiên truy cập",
  },
  { name: "review_count", label: "Số review", section: "Đánh giá" },
  { name: "avg_rating", label: "Rating trung bình", section: "Đánh giá" },
  { name: "low_rating_share", label: "Tỷ lệ rating thấp", section: "Đánh giá" },
  { name: "helpful_votes_total", label: "Tổng helpful votes", section: "Đánh giá" },
  { name: "verified_review_rate", label: "Tỷ lệ verified review", section: "Đánh giá" },
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

  if (message.includes("Network request failed") || message.includes("fetch")) {
    return "Không thể kết nối tới hệ thống. Vui lòng thử lại.";
  }

  return "Không thể hoàn tất dự đoán. Vui lòng kiểm tra dữ liệu và thử lại.";
}

function ChoiceDropdown({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const selectedText = useMemo(
    () => options.find((option) => option === value) ?? value,
    [options, value],
  );

  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={label}
        onPress={() => setOpen(true)}
        style={({ pressed }) => [styles.trigger, pressed ? styles.triggerPressed : null]}
      >
        <Text style={styles.triggerText} numberOfLines={1}>
          {selectedText}
        </Text>
        <Text style={styles.chevron}>v</Text>
      </Pressable>

      <Modal
        animationType="fade"
        transparent
        visible={open}
        onRequestClose={() => setOpen(false)}
      >
        <View style={styles.backdrop}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Đóng danh sách lựa chọn"
            style={styles.backdropHitArea}
            onPress={() => setOpen(false)}
          />
          <View style={styles.sheet}>
            <Text style={styles.sheetTitle}>{label}</Text>
            <ScrollView
              style={styles.optionList}
              contentContainerStyle={styles.optionListContent}
            >
              {options.map((option) => {
                const selected = option === value;

                return (
                  <Pressable
                    accessibilityRole="button"
                    key={option}
                    onPress={() => {
                      onChange(option);
                      setOpen(false);
                    }}
                    style={[styles.option, selected ? styles.selectedOption : null]}
                  >
                    <Text
                      style={[
                        styles.optionText,
                        selected ? styles.selectedOptionText : null,
                      ]}
                    >
                      {option}
                    </Text>
                    {selected ? <Text style={styles.checkMark}>✓</Text> : null}
                  </Pressable>
                );
              })}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
}

export default function CustomerBehaviorScreen() {
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
    source: Record<CustomerField, string> = form,
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

  async function handlePredict() {
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
        setCompareError("Không thể so sánh các mô hình. Vui lòng thử lại.");
      } finally {
        setCompareLoading(false);
      }

      return;
    }

    setLoading(true);

    try {
      const response = await predictCustomerBehavior(payload);
      setResult(response);
      setPredictionModelId(response.model?.id ?? payload.model ?? selectedModel);
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
    setScenarioResult(null);

    try {
      setScenarioResult(await predictCustomerBehavior(payload));
    } catch (requestError) {
      console.error(requestError);
      setScenarioError("Không thể tính lại mô phỏng. Vui lòng thử lại.");
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
    <View style={styles.container}>
      <View>
        <Text style={styles.eyebrow}>Customer Behavior</Text>
        <Text style={styles.title}>Dự đoán hành vi khách hàng</Text>
        <Text style={styles.subtitle}>
          Nhập dữ liệu hồ sơ, giao dịch, phiên truy cập và review để dự đoán
          nguy cơ churn của khách hàng.
        </Text>
      </View>

      <View style={styles.panel}>
        <ModelDropdown
          label="Chọn model dự đoán"
          value={selectedModel}
          options={[
            ...modelOptions,
            {
              id: COMPARE_ALL_MODELS_ID,
              name: "So sánh 6 mô hình",
              recommended: false,
            },
          ]}
          onChange={handleModelChange}
        />

        {sections.map((section) => (
          <View key={section} style={styles.sectionGroup}>
            <Text style={styles.sectionTitle}>{section}</Text>
            {numericFields
              .filter((field) => field.section === section)
              .map((field) => (
                <FormInput
                  key={field.name}
                  label={field.label}
                  value={form[field.name]}
                  error={fieldErrors[field.name]}
                  onChangeText={(value) =>
                    setForm((current) => ({ ...current, [field.name]: value }))
                  }
                />
              ))}
          </View>
        ))}

        <View style={styles.sectionGroup}>
          <Text style={styles.sectionTitle}>Phân loại và sở thích</Text>
          {selectFields.map((field) => (
            <ChoiceDropdown
              key={field.name}
              label={field.label}
              value={form[field.name]}
              options={field.options}
              onChange={(value) =>
                setForm((current) => ({ ...current, [field.name]: value }))
              }
            />
          ))}
        </View>

        <View style={styles.field}>
          <Text style={styles.label}>Review text đã clean</Text>
          <TextInput
            accessibilityLabel="Review text đã clean"
            value={form.review_text_clean}
            multiline
            textAlignVertical="top"
            onChangeText={(value) =>
              setForm((current) => ({ ...current, review_text_clean: value }))
            }
            style={[styles.textArea, fieldErrors.review_text_clean ? styles.inputError : null]}
          />
          <Text style={styles.feedback}>{fieldErrors.review_text_clean ?? " "}</Text>
        </View>

        <View style={styles.buttonRow}>
          <AppButton
            label={
              compareLoading
                ? "Đang so sánh..."
                : loading
                  ? "Đang dự đoán..."
                  : "Dự đoán"
            }
            disabled={loading || compareLoading}
            onPress={handlePredict}
          />
          <AppButton label="Nhập lại" variant="secondary" onPress={clearForm} />
        </View>
      </View>

      {error ? <ErrorMessage message={error} /> : null}
      {compareError ? <ErrorMessage message={compareError} /> : null}

      {result ? (
        <ResultCard title="Kết quả dự đoán">
          {result.model ? (
            <Text style={styles.modelUsed}>Model đã chọn: {result.model.name}</Text>
          ) : null}
          <View
            style={[
              styles.statusBox,
              result.prediction === 1 ? styles.statusWarning : styles.statusSuccess,
            ]}
          >
            <Text style={styles.resultValue}>{customerLabel(result.prediction)}</Text>
            <Text style={styles.note}>{result.interpretation}</Text>
          </View>

          {typeof result.churn_score === "number" ? (
            <View style={styles.infoBox}>
              <Text style={styles.sectionTitle}>Churn score</Text>
              <Text style={styles.bigMetric}>{formatPercent(result.churn_score)}</Text>
              <Text style={styles.note}>
                Với Linear SVM, score này được quy đổi từ decision function để dễ
                đọc, không phải calibrated probability.
              </Text>
            </View>
          ) : null}

          <View style={styles.warningBox}>
            <Text style={styles.sectionTitle}>Lưu ý</Text>
            <Text style={styles.note}>
              Kết quả này chỉ phục vụ mục đích học tập và minh họa Machine
              Learning. Đây không phải kết luận chắc chắn về hành vi khách hàng.
            </Text>
          </View>
        </ResultCard>
      ) : null}

      {compareResult ? (
        <ResultCard title="So sánh kết quả">
          <View style={styles.compareList}>
            {compareResult.results.map((item) => (
              <View key={item.model_id} style={styles.compareRow}>
                <View style={styles.compareMain}>
                  <Text style={styles.compareModel}>{item.model_name}</Text>
                  {item.recommended ? (
                    <View style={styles.badge}>
                      <Text style={styles.badgeText}>Khuyến nghị</Text>
                    </View>
                  ) : null}
                </View>
                <Text style={styles.compareValue}>
                  {customerLabel(item.prediction)}
                  {typeof item.churn_score === "number"
                    ? ` - ${formatPercent(item.churn_score)}`
                    : ""}
                </Text>
              </View>
            ))}
          </View>

          <View style={styles.infoBox}>
            <Text style={styles.sectionTitle}>Mức đồng thuận giữa các mô hình</Text>
            <Text style={styles.bigMetric}>
              {formatPercent(compareResult.consensus.agreement_ratio)}
            </Text>
            <Text style={styles.note}>
              {compareResult.consensus.agreeing_models}/
              {compareResult.consensus.total_models} mô hình đưa ra cùng kết
              luận: {customerLabel(compareResult.consensus.majority_prediction)}.
            </Text>
          </View>
        </ResultCard>
      ) : null}

      {result ? (
        <ResultCard title="Mô phỏng thay đổi hành vi">
          {scenarioForm ? (
            <>
              {numericFields.map((field) => (
                <FormInput
                  key={field.name}
                  label={field.label}
                  value={scenarioForm[field.name]}
                  onChangeText={(value) =>
                    setScenarioForm((current) =>
                      current ? { ...current, [field.name]: value } : current,
                    )
                  }
                />
              ))}
              <View style={styles.scenarioButtonRow}>
                <AppButton
                  label={scenarioLoading ? "Đang tính..." : "Tính lại"}
                  disabled={scenarioLoading}
                  onPress={handleScenarioPredict}
                />
                <AppButton
                  label="Reset mô phỏng"
                  variant="secondary"
                  onPress={resetScenario}
                />
              </View>
              {scenarioError ? <ErrorMessage message={scenarioError} /> : null}
              {scenarioResult ? (
                <View style={styles.whatIfResult}>
                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>Ban đầu</Text>
                    <Text style={styles.summaryValue}>
                      {customerLabel(result.prediction)}
                      {typeof result.churn_score === "number"
                        ? ` - ${formatPercent(result.churn_score)}`
                        : ""}
                    </Text>
                  </View>
                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>Sau thay đổi</Text>
                    <Text style={styles.summaryValue}>
                      {customerLabel(scenarioResult.prediction)}
                      {typeof scenarioResult.churn_score === "number"
                        ? ` - ${formatPercent(scenarioResult.churn_score)}`
                        : ""}
                    </Text>
                  </View>
                </View>
              ) : null}
              <Text style={styles.note}>
                Mô phỏng chỉ thay đổi numeric features; categorical và review text
                giữ nguyên so với input ban đầu.
              </Text>
            </>
          ) : (
            <AppButton
              label="Thử thay đổi thông tin"
              variant="secondary"
              onPress={startScenario}
            />
          )}
        </ResultCard>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
  },
  eyebrow: {
    color: "#2563eb",
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  title: {
    color: "#172033",
    fontSize: 30,
    fontWeight: "900",
  },
  subtitle: {
    color: "#64748b",
    fontSize: 15,
    lineHeight: 22,
    marginTop: 6,
  },
  panel: {
    gap: 10,
    padding: 18,
    borderWidth: 1,
    borderColor: "#d9e2ec",
    borderRadius: 8,
    backgroundColor: "#ffffff",
  },
  sectionGroup: {
    gap: 4,
    paddingTop: 10,
  },
  field: {
    gap: 7,
  },
  label: {
    color: "#243044",
    fontSize: 15,
    fontWeight: "800",
  },
  trigger: {
    minHeight: 46,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 8,
    paddingHorizontal: 12,
    backgroundColor: "#ffffff",
  },
  triggerPressed: {
    borderColor: "#2563eb",
    backgroundColor: "#eff6ff",
  },
  triggerText: {
    flex: 1,
    color: "#172033",
    fontSize: 16,
    fontWeight: "800",
  },
  chevron: {
    color: "#64748b",
    fontSize: 18,
    fontWeight: "900",
  },
  backdrop: {
    flex: 1,
    justifyContent: "flex-end",
    backgroundColor: "rgba(15, 23, 42, 0.32)",
  },
  backdropHitArea: {
    ...StyleSheet.absoluteFillObject,
  },
  sheet: {
    maxHeight: "78%",
    borderTopLeftRadius: 14,
    borderTopRightRadius: 14,
    backgroundColor: "#ffffff",
    padding: 18,
  },
  sheetTitle: {
    color: "#172033",
    fontSize: 18,
    fontWeight: "900",
    paddingBottom: 12,
  },
  optionList: {
    marginTop: 4,
  },
  optionListContent: {
    gap: 8,
    paddingBottom: 10,
  },
  option: {
    minHeight: 48,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    borderWidth: 1,
    borderColor: "#d9e2ec",
    borderRadius: 8,
    paddingHorizontal: 12,
    backgroundColor: "#ffffff",
  },
  selectedOption: {
    borderColor: "#2563eb",
    backgroundColor: "#eff6ff",
  },
  optionText: {
    flex: 1,
    color: "#172033",
    fontSize: 15,
    fontWeight: "800",
  },
  selectedOptionText: {
    color: "#1d4ed8",
    fontWeight: "900",
  },
  checkMark: {
    color: "#1d4ed8",
    fontSize: 18,
    fontWeight: "900",
  },
  textArea: {
    minHeight: 96,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: "#ffffff",
    color: "#172033",
    fontSize: 16,
  },
  inputError: {
    borderColor: "#c2410c",
  },
  feedback: {
    minHeight: 18,
    color: "#c2410c",
    fontSize: 13,
  },
  buttonRow: {
    gap: 10,
    marginTop: 8,
  },
  scenarioButtonRow: {
    gap: 10,
    marginTop: 4,
  },
  resultValue: {
    color: "#172033",
    fontSize: 25,
    fontWeight: "900",
  },
  modelUsed: {
    color: "#64748b",
    fontSize: 14,
    fontWeight: "700",
  },
  statusBox: {
    gap: 8,
    padding: 14,
    borderWidth: 1,
    borderRadius: 8,
  },
  statusSuccess: {
    borderColor: "#b8e4c5",
    backgroundColor: "#f2fbf5",
  },
  statusWarning: {
    borderColor: "#fed7aa",
    backgroundColor: "#fff7ed",
  },
  sectionTitle: {
    color: "#172033",
    fontSize: 15,
    fontWeight: "900",
  },
  summaryRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#eef2f7",
  },
  summaryLabel: {
    flex: 1,
    color: "#64748b",
    fontWeight: "700",
  },
  summaryValue: {
    flex: 1,
    color: "#172033",
    fontWeight: "900",
    textAlign: "right",
  },
  compareList: {
    gap: 10,
  },
  compareRow: {
    gap: 6,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#eef2f7",
  },
  compareMain: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  compareModel: {
    flex: 1,
    color: "#172033",
    fontSize: 15,
    fontWeight: "900",
  },
  compareValue: {
    color: "#475569",
    fontSize: 14,
    fontWeight: "800",
  },
  badge: {
    borderRadius: 999,
    backgroundColor: "#eff6ff",
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  badgeText: {
    color: "#1d4ed8",
    fontSize: 12,
    fontWeight: "900",
  },
  bigMetric: {
    color: "#1d4ed8",
    fontSize: 30,
    fontWeight: "900",
  },
  whatIfResult: {
    gap: 8,
    padding: 14,
    borderWidth: 1,
    borderColor: "#d9e2ec",
    borderRadius: 8,
    backgroundColor: "#f8fafc",
  },
  infoBox: {
    gap: 8,
    padding: 14,
    borderWidth: 1,
    borderColor: "#d9e2ec",
    borderRadius: 8,
    backgroundColor: "#f8fafc",
  },
  warningBox: {
    gap: 8,
    padding: 14,
    borderWidth: 1,
    borderColor: "#fed7aa",
    borderRadius: 8,
    backgroundColor: "#fff7ed",
  },
  note: {
    color: "#64748b",
    fontSize: 14,
    lineHeight: 21,
  },
});
