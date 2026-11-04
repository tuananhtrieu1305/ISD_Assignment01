import { ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";

type ResultCardProps = {
  title: string;
  children: ReactNode;
};

export default function ResultCard({ title, children }: ResultCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: 10,
    borderWidth: 1,
    borderColor: "#d9e2ec",
    borderRadius: 8,
    backgroundColor: "#ffffff",
    padding: 18,
  },
  title: {
    color: "#64748b",
    fontSize: 13,
    fontWeight: "800",
    textTransform: "uppercase",
  },
});
