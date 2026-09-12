import React from "react";
import { StyleSheet, Text, View, ViewStyle } from "react-native";
import { colors, radius, typography } from "../../theme";

interface ChipProps {
  label: string;
  variant?: "success" | "warning" | "error" | "info" | "purple" | "neutral";
  color?: string;
  bgColor?: string;
  style?: ViewStyle;
}

export default function Chip({
  label,
  variant = "neutral",
  color,
  bgColor,
  style,
}: ChipProps) {
  let textColor = colors.ink;
  let background = colors.bg;

  switch (variant) {
    case "success":
      textColor = colors.accent;
      background = colors.primarySoft;
      break;
    case "warning":
      textColor = "#B45309";
      background = colors.amberSoft;
      break;
    case "error":
      textColor = colors.red;
      background = colors.redSoft;
      break;
    case "info":
      textColor = colors.blue;
      background = colors.blueSoft;
      break;
    case "purple":
      textColor = colors.purple;
      background = colors.purpleSoft;
      break;
    case "neutral":
      textColor = colors.inkMuted;
      background = colors.bg;
      break;
  }

  if (color) textColor = color;
  if (bgColor) background = bgColor;

  return (
    <View style={[styles.chip, { backgroundColor: background }, style]}>
      <Text style={[styles.text, { color: textColor }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    borderRadius: radius.pill,
    paddingHorizontal: 10,
    paddingVertical: 4,
    alignSelf: "flex-start",
  },
  text: {
    ...typography.micro,
    fontWeight: "700",
  },
});
