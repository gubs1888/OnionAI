/**
 * DefectChart — dependency-free horizontal bar chart (pure Views).
 * Intentionally no chart library: works everywhere, zero install weight.
 */

import { StyleSheet, Text, View } from "react-native";

type Counts = {
  healthy: number;
  damaged: number;
  rotten: number;
  sprouted: number;
  undersized: number;
};

const CATEGORIES: Array<{ key: keyof Counts; label: string; color: string }> = [
  { key: "healthy", label: "Healthy", color: "#16A34A" },
  { key: "damaged", label: "Damaged", color: "#D97706" },
  { key: "rotten", label: "Rotten", color: "#DC2626" },
  { key: "sprouted", label: "Sprouted", color: "#7C3AED" },
  { key: "undersized", label: "Size Out of Spec (<35mm / >70mm)", color: "#2563EB" },
];

export default function DefectChart({ counts }: { counts: Counts }) {
  const total = CATEGORIES.reduce((sum, c) => sum + Math.max(0, counts[c.key]), 0);

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Composition</Text>
      {CATEGORIES.map(({ key, label, color }) => {
        const value = Math.max(0, counts[key]);
        const pct = total > 0 ? (value / total) * 100 : 0;
        return (
          <View key={key} style={styles.row}>
            <Text style={styles.label}>
              {label} ({value})
            </Text>
            <View style={styles.track}>
              <View style={[styles.bar, { width: `${pct}%`, backgroundColor: color }]} />
            </View>
            <Text style={styles.pct}>{pct.toFixed(0)}%</Text>
          </View>
        );
      })}
      {total === 0 ? <Text style={styles.empty}>No data.</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 16,
    marginTop: 16,
  },
  title: { fontSize: 15, fontWeight: "700", color: "#111827", marginBottom: 10 },
  row: { marginTop: 8 },
  label: { fontSize: 12, color: "#6B7280", marginBottom: 4 },
  track: {
    height: 8,
    backgroundColor: "#F3F4F6",
    borderRadius: 999,
    overflow: "hidden",
  },
  bar: { height: 8, borderRadius: 999 },
  pct: {
    fontSize: 11,
    fontWeight: "700",
    color: "#374151",
    marginTop: 2,
    textAlign: "right",
  },
  empty: { color: "#9CA3AF", fontSize: 12, marginTop: 8 },
});
