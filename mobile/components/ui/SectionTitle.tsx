import React, { ReactNode } from "react";
import { Pressable, StyleSheet, Text, View, ViewStyle } from "react-native";
import { colors, typography } from "../../theme";

interface SectionTitleProps {
  title: string;
  subtitle?: string;
  actionText?: string;
  onAction?: () => void;
  rightElement?: ReactNode;
  style?: ViewStyle;
}

export default function SectionTitle({
  title,
  subtitle,
  actionText,
  onAction,
  rightElement,
  style,
}: SectionTitleProps) {
  return (
    <View style={[styles.container, style]}>
      <View style={styles.titleCol}>
        <Text style={styles.title}>{title}</Text>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      </View>
      {rightElement}
      {actionText && onAction && !rightElement ? (
        <Pressable onPress={onAction} hitSlop={8}>
          <Text style={styles.action}>{actionText}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 24,
    marginBottom: 12,
  },
  titleCol: {
    flex: 1,
  },
  title: {
    ...typography.title2,
    color: colors.ink,
  },
  subtitle: {
    ...typography.caption,
    color: colors.inkMuted,
    marginTop: 2,
  },
  action: {
    ...typography.caption,
    color: colors.red,
    fontWeight: "600",
  },
});
