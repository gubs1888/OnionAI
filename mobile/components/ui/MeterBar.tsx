import React, { useEffect, useRef } from "react";
import { Animated, StyleSheet, Text, View, ViewStyle } from "react-native";
import { colors, radius, typography } from "../../theme";

interface MeterBarProps {
  label: string;
  value: number; // 0..100
  color?: string;
  bgColor?: string;
  height?: number;
  showValueText?: boolean;
  unit?: string;
  style?: ViewStyle;
}

export default function MeterBar({
  label,
  value,
  color = colors.accent,
  bgColor = colors.bg,
  height = 8,
  showValueText = true,
  unit = "%",
  style,
}: MeterBarProps) {
  const widthAnim = useRef(new Animated.Value(0)).current;
  const clampedVal = Math.min(100, Math.max(0, value));

  useEffect(() => {
    Animated.timing(widthAnim, {
      toValue: clampedVal,
      duration: 600,
      useNativeDriver: false,
    }).start();
  }, [clampedVal, widthAnim]);

  const widthInterpolated = widthAnim.interpolate({
    inputRange: [0, 100],
    outputRange: ["0%", "100%"],
  });

  return (
    <View style={[styles.container, style]}>
      <View style={styles.header}>
        <Text style={styles.label}>{label}</Text>
        {showValueText ? (
          <Text style={styles.valueText}>
            {clampedVal.toFixed(1)}
            {unit}
          </Text>
        ) : null}
      </View>
      <View style={[styles.track, { height, backgroundColor: bgColor }]}>
        <Animated.View
          style={[
            styles.fill,
            {
              height,
              backgroundColor: color,
              width: widthInterpolated,
            },
          ]}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 6,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  label: {
    ...typography.caption,
    color: colors.inkMuted,
    fontWeight: "500",
  },
  valueText: {
    ...typography.caption,
    color: colors.ink,
    fontWeight: "700",
  },
  track: {
    width: "100%",
    borderRadius: radius.pill,
    overflow: "hidden",
  },
  fill: {
    borderRadius: radius.pill,
  },
});
