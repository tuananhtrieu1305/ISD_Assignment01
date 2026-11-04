// @ts-nocheck
import { useEffect, useRef, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
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
import ErrorMessage from "../components/ErrorMessage";
import FormInput from "../components/FormInput";
import ModelDropdown from "../components/ModelDropdown";
import ResultCard from "../components/ResultCard";

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

function formatSignedBillionPriceAsVnd(priceInBillions: number) {
  const prefix = priceInBillions > 0 ? "+" : "";
  return `${prefix}${formatBillionPriceAsVnd(priceInBillions)}`;
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

export default function HousePriceScreen() {
  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [error, setError] = useState("");
  const [compareError, setCompareError] = useState("");
  const [scenarioError, setScenarioError] = useState("");
  const [result, setResult] = useState<HouseResponse | null>(null);
  const [compareResult, setCompareResult] = useState<HouseCompareResponse | null>(
    null,
  );
  const [originalForm, setOriginalForm] =
    useState<Record<HouseField, string> | null>(null);
  const [scenarioForm, setScenarioForm] =
    useState<Record<HouseField, string> | null>(null);
  const [scenarioResult, setScenarioResult] = useState<HouseResponse | null>(null);
  const [modelOptions, setModelOptions] = useState(fallbackModelOptions);
  const [selectedModel, setSelectedModel] = useState(
    "gradient_boosting_regressor",
  );
  const [predictionModelId, setPredictionModelId] = useState<string | null>(null);
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
    source: Record<HouseField, string> = form,
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
        setCompareResult(await compareHouseModels(payload));
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
      const response = await predictHouse(payload);
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
      setScenarioResult(await predictHouse(payload));
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
        <Text style={styles.eyebrow}>Ước tính giá nhà</Text>
        <Text style={styles.title}>Dự đoán giá nhà Việt Nam</Text>
        <Text style={styles.subtitle}>
          Nhập thông tin căn nhà để hệ thống ước tính giá dựa trên dữ liệu đã
          học.
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
        <ResultCard title="Giá nhà ước tính">
          {result.model ? (
            <Text style={styles.modelUsed}>Model đã chọn: {result.model.name}</Text>
          ) : null}
          <Text style={styles.resultValue}>
            {formatBillionPriceAsVnd(result.predicted_price)}
          </Text>
          <Text style={styles.note}>
            Đây là mức giá mà mô hình dự đoán dựa trên 6 đặc điểm của căn nhà
            bạn vừa nhập.
          </Text>

          <View style={styles.warningBox}>
            <Text style={styles.sectionTitle}>Lưu ý về kết quả</Text>
            <Text style={styles.note}>
              Đây là giá ước tính từ mô hình Machine Learning dựa trên các thuộc
              tính hiện có trong bộ dữ liệu. Giá thực tế có thể còn phụ thuộc
              vào các yếu tố khác không nằm trong đầu vào của mô hình.
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
                  {formatBillionPriceAsVnd(item.predicted_price)}
                </Text>
              </View>
            ))}
          </View>

          <View style={styles.infoBox}>
            <Text style={styles.sectionTitle}>Mức phân tán giữa các mô hình</Text>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Thấp nhất</Text>
              <Text style={styles.summaryValue}>
                {formatBillionPriceAsVnd(compareResult.spread.min)}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Trung vị</Text>
              <Text style={styles.summaryValue}>
                {formatBillionPriceAsVnd(compareResult.spread.median)}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Cao nhất</Text>
              <Text style={styles.summaryValue}>
                {formatBillionPriceAsVnd(compareResult.spread.max)}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Chênh lệch</Text>
              <Text style={styles.summaryValue}>
                {formatBillionPriceAsVnd(compareResult.spread.range)}
              </Text>
            </View>
            <Text style={styles.note}>
              Đây là độ phân tán giữa các mô hình trên cùng một input, không
              phải khoảng tin cậy hay cam kết sai số.
            </Text>
          </View>
        </ResultCard>
      ) : null}

      {result ? (
        <ResultCard title="Mô phỏng thay đổi thông tin">
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
                      {formatBillionPriceAsVnd(result.predicted_price)}
                    </Text>
                  </View>
                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>Sau thay đổi</Text>
                    <Text style={styles.summaryValue}>
                      {formatBillionPriceAsVnd(scenarioResult.predicted_price)}
                    </Text>
                  </View>
                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>Chênh lệch</Text>
                    <Text style={styles.summaryValue}>
                      {formatSignedBillionPriceAsVnd(
                        scenarioResult.predicted_price - result.predicted_price,
                      )}
                    </Text>
                  </View>
                </View>
              ) : null}
              <Text style={styles.note}>
                Khi thay đổi đầu vào theo cấu hình trên, mô hình đưa ra kết quả
                dự đoán khác như hiển thị. Đây không phải phát biểu nhân quả.
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
    color: "#1d4ed8",
    fontSize: 28,
    fontWeight: "900",
    lineHeight: 34,
  },
  modelUsed: {
    color: "#64748b",
    fontSize: 14,
    fontWeight: "700",
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
    color: "#1d4ed8",
    fontSize: 14,
    fontWeight: "900",
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
