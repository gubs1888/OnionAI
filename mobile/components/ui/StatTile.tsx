import React from "react";
import { StyleSheet, Text, View, ViewStyle } from "react-native";
import { colors, radius, typography, glass, borders } from "../../theme";

interface StatTileProps {
  label: string;
  value: string | number;
  colorDot?: string;
  bgColor?: string;
  dimmed?: boolean;
  style?: ViewStyle;
}

export default function StatTile({
  label,
  value,
  colorDot,
  bgColor,
  dimmed = false,
  style,
}: StatTileProps) {
  return (
    <View
      style={[
        styles.tile,
        bgColor ? { backgroundColor: bgColor } : styles.defaultBg,
        dimmed && styles.dimmedTile,
        style,
      ]}
    >
      <View style={styles.topRow}>
        {colorDot ? (
          <View style={[styles.dot, { backgroundColor: colorDot }]} />
        ) : null}
        <Text style={[styles.label, dimmed && styles.dimmedText]} numberOfLines={1}>
          {label}
        </Text>
      </View>
      <Text style={[styles.value, dimmed && styles.dimmedText]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  tile: {
    borderRadius: radius.M,
    padding: 16,
    borderWidth: 1,
    borderColor: borders.dim,
  },
  defaultBg: {
    backgroundColor: glass.bg,
  },
  dimmedTile: {
    opacity: 0.6,
  },
  topRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: radius.pill,
    marginRight: 6,
  },
  label: {
    ...typography.caption,
    color: colors.inkMuted,
    textTransform: "uppercase",
    letterSpacing: 0.4,
    flex: 1,
  },
  value: {
    ...typography.title2,
    color: colors.ink,
    fontFamily: typography.mono.fontFamily,
  },
  dimmedText: {
    color: colors.inkSubtle,
  },
});
