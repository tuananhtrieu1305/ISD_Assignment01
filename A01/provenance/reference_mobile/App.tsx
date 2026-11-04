import { useEffect, useState } from "react";
import {
  Platform,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { healthCheck } from "./src/api/predictionApi";
import AppButton from "./src/components/AppButton";
import DiabetesScreen from "./src/screens/DiabetesScreen";
import HomeScreen from "./src/screens/HomeScreen";
import HousePriceScreen from "./src/screens/HousePriceScreen";

type Screen = "home" | "diabetes" | "house";

export default function App() {
  const [screen, setScreen] = useState<Screen>("home");
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let ignore = false;

    healthCheck()
      .then(() => {
        if (!ignore) setBackendOnline(true);
      })
      .catch(() => {
        if (!ignore) setBackendOnline(false);
      });

    return () => {
      ignore = true;
    };
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar
        barStyle="dark-content"
        backgroundColor="#ffffff"
        translucent={false}
      />
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Intelligent Systems Development</Text>
        {screen !== "home" ? (
          <AppButton
            label="Trang chủ"
            variant="secondary"
            onPress={() => setScreen("home")}
          />
        ) : null}
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        {screen === "home" ? (
          <HomeScreen
            backendOnline={backendOnline}
            onSelectDiabetes={() => setScreen("diabetes")}
            onSelectHouse={() => setScreen("house")}
          />
        ) : null}
        {screen === "diabetes" ? <DiabetesScreen /> : null}
        {screen === "house" ? <HousePriceScreen /> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#f6f8fb",
    paddingTop: Platform.OS === "android" ? StatusBar.currentHeight ?? 0 : 0,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    paddingHorizontal: 18,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#d9e2ec",
    backgroundColor: "#ffffff",
  },
  headerTitle: {
    flex: 1,
    color: "#172033",
    fontSize: 18,
    fontWeight: "900",
  },
  content: {
    padding: 18,
    paddingBottom: 42,
  },
});
