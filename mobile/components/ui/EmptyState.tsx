import React, { ReactNode } from "react";
import { StyleSheet, Text, View, ViewStyle } from "react-native";
import { colors, radius, typography } from "../../theme";

interface EmptyStateProps {
  title: string;
  message: string;
  icon?: string;
  action?: ReactNode;
  style?: ViewStyle;
}

export default function EmptyState({
  title,
  message,
  icon = "🧅",
  action,
  style,
}: EmptyStateProps) {
  return (
    <View style={[styles.container, style]}>
      <View style={styles.iconCircle}>
        <Text style={styles.icon}>{icon}</Text>
      </View>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.message}>{message}</Text>
      {action ? <View style={styles.actionContainer}>{action}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    backgroundColor: colors.surface,
    borderRadius: radius.M,
    borderWidth: 1,
    borderColor: colors.line,
    marginVertical: 12,
  },
  iconCircle: {
    width: 56,
    height: 56,
    borderRadius: radius.pill,
    backgroundColor: colors.bg,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  icon: {
    fontSize: 28,
  },
  title: {
    ...typography.headline,
    color: colors.ink,
    textAlign: "center",
  },
  message: {
    ...typography.caption,
    color: colors.inkMuted,
    textAlign: "center",
    marginTop: 4,
    maxWidth: 260,
  },
  actionContainer: {
    marginTop: 16,
  },
});
