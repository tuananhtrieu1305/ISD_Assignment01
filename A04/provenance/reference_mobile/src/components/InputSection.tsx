import { PropsWithChildren, useEffect, useRef, useState } from "react";
import { Animated, Easing, Pressable, StyleSheet, Text, View } from "react-native";

type InputSectionProps = PropsWithChildren<{
  title: string;
  defaultOpen?: boolean;
}>;

export default function InputSection({
  title,
  defaultOpen = false,
  children,
}: InputSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const progress = useRef(new Animated.Value(defaultOpen ? 1 : 0)).current;

  useEffect(() => {
    Animated.timing(progress, {
      toValue: open ? 1 : 0,
      duration: 240,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
  }, [open, progress]);

  const maxHeight = progress.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 2200],
  });
  const opacity = progress.interpolate({
    inputRange: [0, 0.35, 1],
    outputRange: [0, 0, 1],
  });
  const translateY = progress.interpolate({
    inputRange: [0, 1],
    outputRange: [-8, 0],
  });
  const rotate = progress.interpolate({
    inputRange: [0, 1],
    outputRange: ["0deg", "180deg"],
  });
  const borderTopWidth = progress.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 1],
  });

  return (
    <View style={styles.section}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={title}
        accessibilityState={{ expanded: open }}
        onPress={() => setOpen((current) => !current)}
        style={({ pressed }) => [styles.header, pressed ? styles.headerPressed : null]}
      >
        <Text style={styles.title}>{title}</Text>
        <Animated.Text style={[styles.chevron, { transform: [{ rotate }] }]}>v</Animated.Text>
      </Pressable>
      <Animated.View
        pointerEvents={open ? "auto" : "none"}
        style={[styles.bodyShell, { maxHeight, opacity, borderTopWidth }]}
      >
        <Animated.View style={[styles.body, { transform: [{ translateY }] }]}>{children}</Animated.View>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  section: {
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#d9e2ec",
    borderRadius: 8,
    backgroundColor: "#fbfdff",
  },
  header: {
    minHeight: 48,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    paddingHorizontal: 14,
  },
  headerPressed: {
    backgroundColor: "#eff6ff",
  },
  title: {
    flex: 1,
    color: "#172033",
    fontSize: 15,
    fontWeight: "900",
  },
  chevron: {
    color: "#64748b",
    fontSize: 18,
    fontWeight: "900",
  },
  bodyShell: {
    overflow: "hidden",
    borderTopColor: "#d9e2ec",
  },
  body: {
    gap: 4,
    padding: 14,
  },
});
