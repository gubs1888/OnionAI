import React, { useEffect, useRef } from "react";
import { Animated, StyleSheet, Text, View, ViewStyle } from "react-native";
import { colors, radius, typography } from "../../theme";

interface StepDotsProps {
  steps: string[];
  currentStep: number; // 0..steps.length-1
  style?: ViewStyle;
}

export default function StepDots({ steps, currentStep, style }: StepDotsProps) {
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.2,
          duration: 400,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 400,
          useNativeDriver: true,
        }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, [pulseAnim]);

  return (
    <View style={[styles.container, style]}>
      {steps.map((label, index) => {
        const isDone = index < currentStep;
        const isActive = index === currentStep;

        return (
          <View key={label} style={styles.stepItem}>
            <View style={styles.iconRow}>
              {index > 0 && (
                <View
                  style={[
                    styles.connector,
                    { backgroundColor: isDone || isActive ? colors.accent : colors.line },
                  ]}
                />
              )}
              <Animated.View
                style={[
                  styles.dot,
                  isDone && styles.dotDone,
                  isActive && styles.dotActive,
                  isActive && { transform: [{ scale: pulseAnim }] },
                ]}
              >
                <Text
                  style={[
                    styles.dotText,
                    (isDone || isActive) && styles.dotTextActive,
                  ]}
                >
                  {isDone ? "✓" : index + 1}
                </Text>
              </Animated.View>
            </View>
            <Text
              style={[
                styles.label,
                isActive && styles.labelActive,
                isDone && styles.labelDone,
              ]}
            >
              {label}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    width: "100%",
    paddingHorizontal: 8,
  },
  stepItem: {
    flex: 1,
    alignItems: "center",
  },
  iconRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    width: "100%",
    position: "relative",
  },
  connector: {
    position: "absolute",
    right: "50%",
    left: "-50%",
    height: 2,
    top: 13,
    zIndex: -1,
  },
  dot: {
    width: 28,
    height: 28,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderColor: colors.line,
    alignItems: "center",
    justifyContent: "center",
  },
  dotDone: {
    backgroundColor: colors.accent,
    borderColor: colors.accent,
  },
  dotActive: {
    backgroundColor: colors.primarySoft,
    borderColor: colors.accent,
  },
  dotText: {
    ...typography.micro,
    color: colors.inkMuted,
    fontWeight: "700",
  },
  dotTextActive: {
    color: colors.accent,
  },
  label: {
    ...typography.caption,
    fontSize: 11,
    color: colors.inkMuted,
    marginTop: 6,
    textAlign: "center",
  },
  labelActive: {
    color: colors.accent,
    fontWeight: "700",
  },
  labelDone: {
    color: colors.ink,
    fontWeight: "500",
  },
});
