import React, { useEffect, useRef } from "react";
import { Animated, StyleSheet, View, ViewStyle } from "react-native";
import { colors, radius } from "../../theme";

interface SkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: ViewStyle;
}

export function SkeletonRow({
  width = "100%",
  height = 16,
  borderRadius = radius.S,
  style,
}: SkeletonProps) {
  const opacityAnim = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(opacityAnim, {
          toValue: 0.8,
          duration: 600,
          useNativeDriver: true,
        }),
        Animated.timing(opacityAnim, {
          toValue: 0.3,
          duration: 600,
          useNativeDriver: true,
        }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, [opacityAnim]);

  return (
    <Animated.View
      style={[
        styles.skeleton,
        {
          width: width as any,
          height,
          borderRadius,
          opacity: opacityAnim,
        },
        style,
      ]}
    />
  );
}

export function SkeletonCard({ style }: { style?: ViewStyle }) {
  return (
    <View style={[styles.card, style]}>
      <SkeletonRow width="40%" height={18} style={{ marginBottom: 12 }} />
      <SkeletonRow width="80%" height={14} style={{ marginBottom: 8 }} />
      <SkeletonRow width="60%" height={14} />
    </View>
  );
}

const styles = StyleSheet.create({
  skeleton: {
    backgroundColor: colors.line,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.M,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.line,
    marginBottom: 12,
  },
});
