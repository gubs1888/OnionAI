/**
 * GradeBadge — big colored circle with the MVP grade letter.
 * Colors: A green · B blue · C orange · D red.
 */

import { StyleSheet, Text, View } from "react-native";

import { Grade } from "../types/assessment";

const COLORS: Record<Grade, { bg: string; label: string }> = {
  A: { bg: "#16A34A", label: "Excellent" },
  B: { bg: "#2563EB", label: "Good" },
  C: { bg: "#D97706", label: "Fair" },
  D: { bg: "#DC2626", label: "Poor" },
};

export default function GradeBadge({ grade }: { grade: Grade }) {
  const color = COLORS[grade] ?? COLORS.D;
  return (
    <View style={[styles.circle, { backgroundColor: color.bg }]}>
      <Text style={styles.letter}>{grade}</Text>
      <Text style={styles.sub}>{color.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  circle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    alignItems: "center",
    justifyContent: "center",
  },
  letter: { color: "#fff", fontSize: 40, fontWeight: "900", lineHeight: 44 },
  sub: { color: "rgba(255,255,255,0.9)", fontSize: 10, fontWeight: "700" },
});
