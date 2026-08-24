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
import ErrorMessage from "../components/ErrorMessage";
import FormInput from "../components/FormInput";
import ModelDropdown from "../components/ModelDropdown";
import ResultCard from "../components/ResultCard";

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
    detail: positiveIsHigher
      ? `Tỉ lệ dương tính đang cao hơn tỉ lệ âm tính (${formatPercent(
          safePositive,
        )} so với ${formatPercent(negativeProbability)}).`
      : `Tỉ lệ âm tính đang cao hơn tỉ lệ dương tính (${formatPercent(
          negativeProbability,
        )} so với ${formatPercent(safePositive)}).`,
  };
}

function diabetesLabel(prediction: number) {
  return prediction === 1 ? "Dương tính" : "Âm tính";
}

function toFriendlyError(message: string) {
  if (message.includes("Missing required field")) {
    return "Vui lòng nhập đầy đủ các trường.";
  }

  if (message.includes("Invalid number")) {
    return "Giá trị nhập vào phải là số hợp lệ.";
  }

  if (message.includes("Network request failed") || message.includes("fetch")) {
    return "Không thể kết nối tới hệ thống. Vui lòng thử lại.";
  }

  return "Không thể hoàn tất dự đoán. Vui lòng kiểm tra dữ liệu và thử lại.";
}

export default function DiabetesScreen() {
  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [error, setError] = useState("");
  const [compareError, setCompareError] = useState("");
  const [scenarioError, setScenarioError] = useState("");
  const [result, setResult] = useState<DiabetesResponse | null>(null);
  const [compareResult, setCompareResult] = useState<DiabetesCompareResponse | null>(
    null,
  );
  const [originalForm, setOriginalForm] =
    useState<Record<DiabetesField, string> | null>(null);
  const [scenarioForm, setScenarioForm] =
    useState<Record<DiabetesField, string> | null>(null);
  const [scenarioResult, setScenarioResult] = useState<DiabetesResponse | null>(null);
  const [modelOptions, setModelOptions] = useState(fallbackModelOptions);
  const [selectedModel, setSelectedModel] = useState("logistic_regression");
  const [predictionModelId, setPredictionModelId] = useState<string | null>(null);
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
    source: Record<DiabetesField, string> = form,
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
      setPredictionModelId(null);

      try {
        setCompareResult(await compareDiabetesModels(payload));
      } catch (requestError) {
        console.error(requestError);
        setCompareError(
          requestError instanceof Error
            ? toFriendlyError(requestError.message)
            : "Không thể so sánh các mô hình. Vui lòng thử lại.",
        );
      } finally {
        setCompareLoading(false);
      }

      return;
    }

    setLoading(true);

    try {
      const response = await predictDiabetes(payload);
      setResult(response);
      setPredictionModelId(
        response.model?.id ?? payload.model ?? selectedModel,
      );
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
      setScenarioError("Vui lòng nhập đầy đủ thông tin mô phỏng bằng số hợp lệ.");
      return;
    }

    setScenarioLoading(true);
    setScenarioError("");
    setScenarioResult(null);

    try {
      setScenarioResult(await predictDiabetes(payload));
    } catch (requestError) {
      console.error(requestError);
      setScenarioError(
        requestError instanceof Error
          ? toFriendlyError(requestError.message)
          : "Không thể tính lại mô phỏng. Vui lòng thử lại.",
      );
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
        <Text style={styles.eyebrow}>Dự đoán sức khỏe</Text>
        <Text style={styles.title}>Dự đoán tiểu đường</Text>
        <Text style={styles.subtitle}>
          Nhập các thông tin sức khỏe bên dưới để nhận kết quả dự đoán từ mô
          hình.
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
              name: "So sánh 5 mô hình",
              recommended: false,
            },
          ]}
          onChange={handleModelChange}
        />
        {fields.map((field) => (
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
            <Text style={styles.resultValue}>{diabetesLabel(result.prediction)}</Text>
          </View>

          {typeof result.probability === "number" ? (
            (() => {
              const dominant = getDominantProbability(result.probability);

              return (
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>
                    Tỉ lệ {diabetesLabel(result.prediction)} của bạn là:
                  </Text>
                  <Text style={styles.probabilityValue}>
                    {formatPercent(dominant.probability)}
                  </Text>
                  <Text style={styles.note}>
                    {dominant.detail} Đây là tỉ lệ dự đoán của mô hình, không
                    phải xác suất y khoa khẳng định bạn mắc bệnh.
                  </Text>
                </View>
              );
            })()
          ) : null}

          <View style={styles.warningBox}>
            <Text style={styles.sectionTitle}>Lưu ý</Text>
            <Text style={styles.note}>
              Kết quả này chỉ phục vụ mục đích học tập và minh họa Machine
              Learning. Đây không phải chẩn đoán y khoa và không thay thế tư vấn
              của bác sĩ.
            </Text>
          </View>
        </ResultCard>
      ) : null}

      {compareResult ? (
        <ResultCard title="So sánh kết quả">
          <View style={styles.compareList}>
            {compareResult.results.map((item) => {
              const dominant =
                typeof item.probability === "number"
                  ? getDominantProbability(item.probability)
                  : null;

              return (
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
                    {diabetesLabel(item.prediction)}
                    {dominant ? ` - ${formatPercent(dominant.probability)}` : ""}
                  </Text>
                </View>
              );
            })}
          </View>

          <View style={styles.infoBox}>
            <Text style={styles.sectionTitle}>Mức đồng thuận giữa các mô hình</Text>
            <Text style={styles.bigMetric}>
              {formatPercent(compareResult.consensus.agreement_ratio)}
            </Text>
            <Text style={styles.note}>
              {compareResult.consensus.agreeing_models}/
              {compareResult.consensus.total_models} mô hình đưa ra cùng một kết
              luận: {diabetesLabel(compareResult.consensus.majority_prediction)}.
              Đây là tỷ lệ các mô hình đồng ý với nhau, không phải độ tin cậy y
              khoa.
            </Text>
          </View>
        </ResultCard>
      ) : null}

      {result ? (
        <ResultCard title="Mô phỏng thay đổi thông số">
          {scenarioForm ? (
            <>
              <View style={styles.scenarioGrid}>
                {fields.map((field) => (
                  <View key={field.name} style={styles.scenarioField}>
                    <FormInput
                      label={field.label}
                      value={scenarioForm[field.name]}
                      onChangeText={(value) =>
                        setScenarioForm((current) =>
                          current
                            ? { ...current, [field.name]: value }
                            : current,
                        )
                      }
                    />
                  </View>
                ))}
              </View>
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
                      {diabetesLabel(result.prediction)}
                      {typeof result.probability === "number"
                        ? ` - ${formatPercent(
                            getDominantProbability(result.probability)
                              .probability,
                          )}`
                        : ""}
                    </Text>
                  </View>
                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>Sau thay đổi</Text>
                    <Text style={styles.summaryValue}>
                      {diabetesLabel(scenarioResult.prediction)}
                      {typeof scenarioResult.probability === "number"
                        ? ` - ${formatPercent(
                            getDominantProbability(scenarioResult.probability)
                              .probability,
                          )}`
                        : ""}
                    </Text>
                  </View>
                  {typeof result.probability === "number" &&
                  typeof scenarioResult.probability === "number" ? (
                    result.prediction === scenarioResult.prediction ? (
                      <View style={styles.summaryRow}>
                        <Text style={styles.summaryLabel}>Thay đổi</Text>
                        <Text style={styles.summaryValue}>
                          {(
                            (getDominantProbability(scenarioResult.probability)
                              .probability -
                              getDominantProbability(result.probability)
                                .probability) *
                            100
                          ).toFixed(2)}{" "}
                          điểm phần trăm
                        </Text>
                      </View>
                    ) : (
                      <View style={styles.summaryRow}>
                        <Text style={styles.summaryLabel}>Kết luận</Text>
                        <Text style={styles.summaryValue}>
                          Dự đoán đã đổi từ {diabetesLabel(result.prediction)} sang{" "}
                          {diabetesLabel(scenarioResult.prediction)}
                        </Text>
                      </View>
                    )
                  ) : null}
                </View>
              ) : null}
              <Text style={styles.note}>
                Đây chỉ là mô phỏng phản ứng của mô hình khi thay đổi dữ liệu
                đầu vào, không phải khuyến nghị y tế.
              </Text>
            </>
          ) : (
            <AppButton
              label="Thử thay đổi thông số"
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
    gap: 4,
    padding: 18,
    borderWidth: 1,
    borderColor: "#d9e2ec",
    borderRadius: 8,
    backgroundColor: "#ffffff",
  },
  buttonRow: {
    gap: 10,
    marginTop: 8,
  },
  scenarioGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },
  scenarioField: {
    flexBasis: "47%",
    flexGrow: 1,
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
  section: {
    gap: 9,
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: "#d9e2ec",
  },
  sectionTitle: {
    color: "#172033",
    fontSize: 15,
    fontWeight: "900",
  },
  probabilityValue: {
    color: "#1d4ed8",
    fontSize: 34,
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
