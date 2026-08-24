import { StyleSheet, Text, TextInput, View } from "react-native";

type FormInputProps = {
  label: string;
  value: string;
  error?: string;
  onChangeText: (value: string) => void;
};

export default function FormInput({
  label,
  value,
  error,
  onChangeText,
}: FormInputProps) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        value={value}
        onChangeText={onChangeText}
        keyboardType="numeric"
        inputMode="decimal"
        style={[styles.input, error ? styles.inputError : null]}
      />
      <Text style={styles.feedback}>{error ?? " "}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  field: {
    gap: 7,
  },
  label: {
    color: "#243044",
    fontSize: 15,
    fontWeight: "800",
  },
  input: {
    minHeight: 46,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 8,
    paddingHorizontal: 12,
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
});
