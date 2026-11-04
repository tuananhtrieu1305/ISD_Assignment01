import { StyleSheet, Text, View } from "react-native";

type ErrorMessageProps = {
  message: string;
};

export default function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderWidth: 1,
    borderColor: "#fed7aa",
    borderRadius: 8,
    backgroundColor: "#fff7ed",
    padding: 14,
  },
  text: {
    color: "#c2410c",
    fontWeight: "700",
  },
});
