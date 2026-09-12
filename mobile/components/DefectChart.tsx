import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { colors, radius, typography } from "../theme";
import MeterBar from "./ui/MeterBar";

type Counts = {
  healthy: number;
  damaged: number;
  rotten: number;
  sprouted: number;
  undersized: number;
};

const CATEGORIES: Array<{ key: keyof Counts; label: string; color: string }> = [
  { key: "healthy", label: "Healthy", color: colors.category.healthy },
  { key: "damaged", label: "Damaged", color: colors.category.damaged },
  { key: "rotten", label: "Rotten", color: colors.category.rotten },
  { key: "sprouted", label: "Sprouted", color: colors.category.sprouted },
  { key: "undersized", label: "Size Out of Spec (<35mm / >70mm)", color: colors.category.undersized },
];

export default function DefectChart({ counts }: { counts: Counts }) {
  const total = CATEGORIES.reduce(
    (sum, c) => sum + Math.max(0, counts[c.key] || 0),
    0
  );

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Composition Breakdown</Text>

      {/* Multi-segment stacked bar preview */}
      {total > 0 && (
        <View style={styles.stackedTrack}>
          {CATEGORIES.map(({ key, color }) => {
            const val = Math.max(0, counts[key] || 0);
            const pct = (val / total) * 100;
            if (pct <= 0) return null;
            return (
              <View
                key={key}
                style={{
                  width: `${pct}%`,
                  height: 12,
                  backgroundColor: color,
                }}
              />
            );
          })}
        </View>
      )}

      {/* Individual category bars */}
      <View style={styles.barsList}>
        {CATEGORIES.map(({ key, label, color }) => {
          const value = Math.max(0, counts[key] || 0);
          const pct = total > 0 ? (value / total) * 100 : 0;
          return (
            <MeterBar
              key={key}
              label={`${label} (${value})`}
              value={pct}
              color={color}
              height={8}
            />
          );
        })}
      </View>

      {total === 0 && <Text style={styles.empty}>No detections recorded.</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.M,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 16,
    marginVertical: 8,
  },
  title: {
    ...typography.headline,
    color: colors.ink,
    marginBottom: 12,
  },
  stackedTrack: {
    height: 12,
    flexDirection: "row",
    backgroundColor: colors.bg,
    borderRadius: radius.pill,
    overflow: "hidden",
    marginBottom: 16,
  },
  barsList: {
    marginTop: 4,
  },
  empty: {
    ...typography.caption,
    color: colors.inkMuted,
    textAlign: "center",
    marginVertical: 12,
  },
});
