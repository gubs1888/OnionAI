import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { colors, radius, typography, borders } from "../theme";
import { Assessment } from "../types/assessment";
import { BlurView } from "expo-blur";

export default function ResultCard({ assessment }: { assessment: Assessment }) {
  const rows: Array<[string, string, boolean?]> = [
    ["Total onions", String(assessment.total_onions), true],
    [
      "Grade A (Count)",
      assessment.grade_a_count !== undefined
        ? String(assessment.grade_a_count)
        : String(assessment.healthy),
    ],
    [
      "Grade URS (Count)",
      assessment.grade_urs_count !== undefined
        ? String(assessment.grade_urs_count)
        : "0",
    ],
    [
      "Non-Qualifying (Count)",
      assessment.non_qualifying_count !== undefined
        ? String(assessment.non_qualifying_count)
        : "0",
    ],
    ["Damaged", String(assessment.damaged)],
    ["Rotten", String(assessment.rotten)],
    ["Sprouted", String(assessment.sprouted)],
    ["Size Out-of-Spec (<35mm / >70mm)", String(assessment.undersized)],
    ["Defect %", `${assessment.defect_percentage.toFixed(2)}%`],
    ["URS % (Under Relaxed Specs)", `${assessment.urs_percentage.toFixed(1)}%`],
  ];

  return (
    <BlurView intensity={20} tint="dark" style={styles.card}>
      <Text style={styles.title}>Assessment Contract Breakdown</Text>
      {rows.map(([label, value, isBold], idx) => (
        <View
          key={label}
          style={[styles.row, idx === rows.length - 1 && styles.lastRow]}
        >
          <Text style={[styles.label, isBold && styles.boldLabel]}>{label}</Text>
          <Text style={[styles.value, isBold && styles.boldValue]}>{value}</Text>
        </View>
      ))}
    </BlurView>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: radius.XL,
    borderWidth: 1,
    borderColor: borders.accent,
    paddingVertical: 12,
    paddingHorizontal: 20,
    marginVertical: 14,
    overflow: "hidden",
  },
  title: {
    ...typography.headline,
    color: colors.primary,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: borders.dim,
    marginBottom: 4,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: borders.dim,
  },
  lastRow: {
    borderBottomWidth: 0,
  },
  label: {
    ...typography.body,
    fontSize: 13,
    color: colors.inkMuted,
    flex: 1,
  },
  boldLabel: {
    fontFamily: typography.bodyMedium.fontFamily,
    fontWeight: "700",
    color: colors.ink,
  },
  value: {
    fontFamily: typography.mono.fontFamily,
    fontSize: 13,
    fontWeight: "600",
    color: colors.ink,
  },
  boldValue: {
    ...typography.headline,
    fontFamily: typography.mono.fontFamily,
    color: colors.primary,
  },
});
