import React from "react";
import { StyleSheet, Text, View, ViewStyle } from "react-native";
import { colors, radius, typography } from "../../theme";

interface BannerProps {
  message: string;
  variant?: "demo" | "error" | "info" | "success" | "warning";
  icon?: string;
  style?: ViewStyle;
}

export default function Banner({
  message,
  variant = "demo",
  icon,
  style,
}: BannerProps) {
  let bg = colors.amber;
  let textCol = "#FFFFFF";
  let defaultIcon = "⚠️";

  if (variant === "demo") {
    bg = colors.amber;
    textCol = "#FFFFFF";
    defaultIcon = "⚠️";
  } else if (variant === "error") {
    bg = colors.red;
    textCol = "#FFFFFF";
    defaultIcon = "🚫";
  } else if (variant === "warning") {
    bg = "#D97706";
    textCol = "#FFFFFF";
    defaultIcon = "⚡";
  } else if (variant === "info") {
    bg = colors.blue;
    textCol = "#FFFFFF";
    defaultIcon = "ℹ️";
  } else if (variant === "success") {
    bg = colors.accent;
    textCol = "#FFFFFF";
    defaultIcon = "✓";
  }

  const activeIcon = icon ?? defaultIcon;

  return (
    <View style={[styles.banner, { backgroundColor: bg }, style]}>
      <Text style={styles.icon}>{activeIcon}</Text>
      <Text style={[styles.text, { color: textCol }]}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    borderRadius: radius.S,
    paddingVertical: 12,
    paddingHorizontal: 14,
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
    shadowColor: colors.ink,
    shadowOpacity: 0.08,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 3 },
    elevation: 3,
  },
  icon: {
    fontSize: 16,
    marginRight: 10,
  },
  text: {
    ...typography.headline,
    fontWeight: "700",
    flex: 1,
  },
});
