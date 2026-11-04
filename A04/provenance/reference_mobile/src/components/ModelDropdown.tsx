import { useMemo, useState } from "react";
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { ModelOption } from "../api/predictionApi";

type ModelDropdownProps = {
  label: string;
  value: string;
  options: ModelOption[];
  onChange: (value: string) => void;
};

function formatOption(option?: ModelOption) {
  if (!option) return "Chọn model";
  return `${option.name}${option.recommended ? " (khuyến nghị)" : ""}`;
}

export default function ModelDropdown({
  label,
  value,
  options,
  onChange,
}: ModelDropdownProps) {
  const [open, setOpen] = useState(false);
  const selectedOption = useMemo(
    () => options.find((option) => option.id === value),
    [options, value],
  );

  function chooseOption(optionId: string) {
    onChange(optionId);
    setOpen(false);
  }

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
          {formatOption(selectedOption)}
        </Text>
        <Text style={styles.chevron}>v</Text>
      </Pressable>

      <Modal
        animationType="slide"
        transparent
        visible={open}
        onRequestClose={() => setOpen(false)}
      >
        <View style={styles.backdrop}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Đóng danh sách model"
            style={styles.backdropHitArea}
            onPress={() => setOpen(false)}
          />
          <View style={styles.sheet}>
            <View style={styles.sheetHeader}>
              <Text style={styles.sheetTitle}>{label}</Text>
            </View>

            <ScrollView style={styles.optionList} contentContainerStyle={styles.optionListContent}>
              {options.map((option) => {
                const selected = option.id === value;

                return (
                  <Pressable
                    accessibilityRole="button"
                    key={option.id}
                    onPress={() => chooseOption(option.id)}
                    style={[styles.option, selected ? styles.selectedOption : null]}
                  >
                    <Text
                      style={[
                        styles.optionText,
                        selected ? styles.selectedOptionText : null,
                      ]}
                    >
                      {formatOption(option)}
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
    gap: 8,
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
  sheetHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  sheetTitle: {
    flex: 1,
    color: "#172033",
    fontSize: 18,
    fontWeight: "900",
  },
  optionList: {
    marginTop: 10,
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
