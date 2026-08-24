import { Pressable, StyleSheet, Text } from "react-native";

type AppButtonProps = {
  label: string;
  variant?: "primary" | "secondary";
  disabled?: boolean;
  onPress: () => void;
};

export default function AppButton({
  label,
  variant = "primary",
  disabled = false,
  onPress,
}: AppButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        variant === "primary" ? styles.primary : styles.secondary,
        disabled && styles.disabled,
        pressed && !disabled && styles.pressed,
      ]}
    >
      <Text
        style={[
          styles.label,
          variant === "primary" ? styles.primaryLabel : styles.secondaryLabel,
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 48,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 16,
    borderWidth: 1,
  },
  primary: {
    backgroundColor: "#2563eb",
    borderColor: "#2563eb",
  },
  secondary: {
    backgroundColor: "#eef4fb",
    borderColor: "#d9e2ec",
  },
  disabled: {
    opacity: 0.72,
  },
  pressed: {
    transform: [{ translateY: 1 }],
  },
  label: {
    fontSize: 16,
    fontWeight: "800",
  },
  primaryLabel: {
    color: "#ffffff",
  },
  secondaryLabel: {
    color: "#172033",
  },
});
