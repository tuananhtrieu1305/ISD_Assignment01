import { useMemo, useState } from "react";
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

export type ChoiceOption = {
  value: string;
  label: string;
};

type ChoiceDropdownProps = {
  label: string;
  value: string;
  options: ChoiceOption[];
  onChange: (value: string) => void;
};

export default function ChoiceDropdown({
  label,
  value,
  options,
  onChange,
}: ChoiceDropdownProps) {
  const [open, setOpen] = useState(false);
  const selectedLabel = useMemo(
    () => options.find((option) => option.value === value)?.label ?? value,
    [options, value],
  );

  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={label}
        onPress={() => setOpen(true)}
        style={({ pressed }) => [styles.trigger, pressed ? styles.triggerPressed : null]}
      >
        <Text style={styles.triggerText} numberOfLines={1}>
          {selectedLabel}
        </Text>
        <Text style={styles.chevron}>v</Text>
      </Pressable>

      <Modal animationType="slide" transparent visible={open} onRequestClose={() => setOpen(false)}>
        <View style={styles.backdrop}>
          <Pressable style={styles.backdropHitArea} onPress={() => setOpen(false)} />
          <View style={styles.sheet}>
            <Text style={styles.sheetTitle}>{label}</Text>
            <ScrollView style={styles.optionList} contentContainerStyle={styles.optionListContent}>
              {options.map((option) => {
                const selected = option.value === value;
                return (
                  <Pressable
                    accessibilityRole="button"
                    key={option.value}
                    onPress={() => {
                      onChange(option.value);
                      setOpen(false);
                    }}
                    style={[styles.option, selected ? styles.selectedOption : null]}
                  >
                    <Text style={[styles.optionText, selected ? styles.selectedOptionText : null]}>
                      {option.label}
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

const styles = StyleSheet.create({
  container: {
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
});
