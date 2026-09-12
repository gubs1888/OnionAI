import React, { useRef } from "react";
import {
  ActivityIndicator,
  Animated,
  Pressable,
  StyleSheet,
  Text,
  ViewStyle,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { colors, radius, typography, glows, borders, glass } from "../../theme";

interface ButtonProps {
  label: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "lg" | "md";
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  icon?: string;
}

export default function Button({
  label,
  onPress,
  variant = "primary",
  size = "lg",
  loading = false,
  disabled = false,
  style,
  icon,
}: ButtonProps) {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    Animated.spring(scaleAnim, {
      toValue: 0.98,
      useNativeDriver: true,
      speed: 50,
      bounciness: 4,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scaleAnim, {
      toValue: 1,
      useNativeDriver: true,
      speed: 50,
      bounciness: 4,
    }).start();
  };

  const isPrimary = variant === "primary";
  const isSecondary = variant === "secondary";
  const isGhost = variant === "ghost";
  const isDanger = variant === "danger";

  return (
    <Animated.View style={[{ transform: [{ scale: scaleAnim }] }, style, isPrimary && styles.primaryGlow]}>
      <Pressable
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        disabled={disabled || loading}
        style={({ pressed }) => [
          styles.base,
          size === "lg" ? styles.sizeLg : styles.sizeMd,
          isSecondary && styles.secondaryBg,
          isGhost && styles.ghostBg,
          isDanger && styles.dangerBg,
          (disabled || loading) && styles.disabled,
          pressed && !disabled && { opacity: 0.88 },
          { overflow: 'hidden' }
        ]}
      >
        {isPrimary && (
          <LinearGradient
            colors={[colors.brand500, colors.brand700]}
            style={StyleSheet.absoluteFill}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          />
        )}
        {loading ? (
          <ActivityIndicator
            color={isSecondary || isGhost ? colors.ink : "#FFFFFF"}
          />
        ) : (
          <Text
            style={[
              styles.labelBase,
              size === "lg" ? styles.labelLg : styles.labelMd,
              isPrimary && styles.primaryText,
              isSecondary && styles.secondaryText,
              isGhost && styles.ghostText,
              isDanger && styles.dangerText,
            ]}
          >
            {icon ? `${icon}  ` : ""}
            {label}
          </Text>
        )}
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radius.L,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    paddingHorizontal: 20,
  },
  sizeLg: {
    height: 54,
  },
  sizeMd: {
    height: 44,
  },
  primaryGlow: {
    ...glows.brand,
  },
  secondaryBg: {
    backgroundColor: glass.bg,
    borderWidth: 1,
    borderColor: borders.subtle,
  },
  ghostBg: {
    backgroundColor: "transparent",
  },
  dangerBg: {
    backgroundColor: colors.red,
  },
  disabled: {
    opacity: 0.5,
  },
  labelBase: {
    fontFamily: typography.bodyMedium.fontFamily,
    fontWeight: "700",
  },
  labelLg: {
    fontSize: 16,
  },
  labelMd: {
    fontSize: 14,
  },
  primaryText: {
    color: "#FFFFFF",
  },
  secondaryText: {
    color: colors.inkMuted,
  },
  ghostText: {
    color: colors.primary,
  },
  dangerText: {
    color: "#FFFFFF",
  },
});
