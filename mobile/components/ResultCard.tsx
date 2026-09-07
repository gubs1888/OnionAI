/**
 * ResultCard — the numeric contract fields in a simple grid.
 * Kept deliberately plain: structure over beauty (per project rules).
 */

import { StyleSheet, Text, View } from "react-native";

import { Assessment } from "../types/assessment";

export default function ResultCard({ assessment }: { assessment: Assessment }) {
  const rows: Array<[string, string]> = [
    ["Total onions", String(assessment.total_onions)],
    ["Healthy", String(assessment.healthy)],
    ["Damaged", String(assessment.damaged)],
    ["Rotten", String(assessment.rotten)],
    ["Sprouted", String(assessment.sprouted)],
    ["Undersized", String(assessment.undersized)],
    ["Defect %", `${assessment.defect_percentage.toFixed(2)}%`],
    ["URS %", `${assessment.urs_percentage.toFixed(1)}%`],
    ["Confidence", `${assessment.confidence.toFixed(1)}%`],
  ];

  return (
    <View style={styles.card}>
      {rows.map(([label, value]) => (
        <View key={label} style={styles.row}>
          <Text style={styles.label}>{label}</Text>
          <Text style={styles.value}>{value}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#fff",
    borderRadius: 16,
    paddingVertical: 6,
    paddingHorizontal: 16,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#F3F4F6",
  },
  label: { fontSize: 14, color: "#6B7280" },
  value: { fontSize: 14, fontWeight: "700", color: "#111827" },
});
