import React, { useEffect, useRef } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";
import { colors, radius, typography } from "../../theme";
import { Grade } from "../../types/assessment";

interface GradeRingProps {
  grade: Grade;
  score: number; // 0..100
  size?: number;
}

export default function GradeRing({ grade, score, size = 110 }: GradeRingProps) {
  const animValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(animValue, {
      toValue: Math.min(100, Math.max(0, score)),
      duration: 800,
      useNativeDriver: false,
    }).start();
  }, [score, animValue]);

  const gradeColor = colors.grade[grade] ?? colors.grade.D;
  const innerSize = size - 16;
  const borderRadius = size / 2;
  const innerBorderRadius = innerSize / 2;

  return (
    <View style={[styles.container, { width: size, height: size }]}>
      {/* Background ring */}
      <View
        style={[
          styles.ringBg,
          {
            width: size,
            height: size,
            borderRadius,
            borderColor: `${gradeColor}33`,
          },
        ]}
      />
      
      {/* Outer border indicator ring */}
      <View
        style={[
          styles.outerRing,
          {
            width: size,
            height: size,
            borderRadius,
            borderColor: gradeColor,
          },
        ]}
      />

      {/* Inner circle with content */}
      <View
        style={[
          styles.innerCircle,
          {
            width: innerSize,
            height: innerSize,
            borderRadius: innerBorderRadius,
          },
        ]}
      >
        <Text style={[styles.gradeText, { color: gradeColor }]}>{grade}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  ringBg: {
    position: "absolute",
    borderWidth: 6,
  },
  outerRing: {
    position: "absolute",
    borderWidth: 6,
    borderTopColor: "transparent",
    transform: [{ rotate: "-45deg" }],
  },
  innerCircle: {
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: colors.ink,
    shadowOpacity: 0.05,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  gradeText: {
    fontSize: 34,
    fontWeight: "900",
    lineHeight: 38,
  },
  scoreText: {
    ...typography.micro,
    color: colors.inkMuted,
    marginTop: -2,
  },
});
