import { StyleSheet, Text, View } from "react-native";
import AppButton from "../components/AppButton";

type HomeScreenProps = {
  backendOnline: boolean | null;
  onSelectDiabetes: () => void;
  onSelectHouse: () => void;
};

export default function HomeScreen({
  backendOnline,
  onSelectDiabetes,
  onSelectHouse,
}: HomeScreenProps) {
  return (
    <View style={styles.container}>
      <View style={styles.intro}>
        <Text style={styles.eyebrow}>Intelligent Systems Development</Text>
        <Text style={styles.title}>Assignment 01</Text>
        <Text style={styles.subtitle}>
          Chọn một chức năng để nhập thông tin và xem kết quả dự đoán theo cách
          dễ hiểu.
        </Text>
        <Text
          style={[
            styles.status,
            backendOnline === true
              ? styles.online
              : backendOnline === false
                ? styles.offline
                : null,
          ]}
        >
          {backendOnline === null
            ? "Đang kiểm tra"
            : backendOnline
              ? "Hệ thống sẵn sàng"
              : "Không thể kết nối hệ thống"}
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.kicker}>Thông tin sức khỏe</Text>
        <Text style={styles.cardTitle}>Dự đoán tiểu đường</Text>
        <Text style={styles.cardText}>
          Nhập 6 chỉ số sức khỏe để xem nhóm kết quả mô hình dự đoán.
        </Text>
        <AppButton label="Dự đoán tiểu đường" onPress={onSelectDiabetes} />
      </View>

      <View style={styles.card}>
        <Text style={styles.kicker}>Thông tin căn nhà</Text>
        <Text style={styles.cardTitle}>Dự đoán giá nhà</Text>
        <Text style={styles.cardText}>
          Nhập 6 đặc điểm căn nhà để nhận mức giá ước tính từ mô hình.
        </Text>
        <AppButton label="Dự đoán giá nhà" onPress={onSelectHouse} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
  },
  intro: {
    gap: 8,
    marginBottom: 6,
  },
  eyebrow: {
    color: "#2563eb",
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  title: {
    color: "#172033",
    fontSize: 36,
    fontWeight: "900",
  },
  subtitle: {
    color: "#64748b",
    fontSize: 16,
    lineHeight: 24,
  },
  status: {
    alignSelf: "flex-start",
    marginTop: 6,
    paddingHorizontal: 11,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#d9e2ec",
    color: "#64748b",
    fontWeight: "800",
  },
  online: {
    color: "#16803c",
    borderColor: "#b8e4c5",
    backgroundColor: "#effdf4",
  },
  offline: {
    color: "#c2410c",
    borderColor: "#fed7aa",
    backgroundColor: "#fff7ed",
  },
  card: {
    gap: 10,
    padding: 20,
    borderWidth: 1,
    borderColor: "#d9e2ec",
    borderRadius: 8,
    backgroundColor: "#ffffff",
  },
  kicker: {
    color: "#2563eb",
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  cardTitle: {
    color: "#172033",
    fontSize: 24,
    fontWeight: "900",
  },
  cardText: {
    color: "#64748b",
    fontSize: 15,
    lineHeight: 22,
  },
});
