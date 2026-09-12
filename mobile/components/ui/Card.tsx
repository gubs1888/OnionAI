import React, { ReactNode } from "react";
import { StyleSheet, Text, View, ViewStyle } from "react-native";
import { colors, radius, shadows, typography } from "../../theme";

interface CardProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  style?: ViewStyle;
  contentStyle?: ViewStyle;
}

export default function Card({
  children,
  title,
  subtitle,
  action,
  style,
  contentStyle,
}: CardProps) {
  return (
    <View style={[styles.card, style]}>
      {(title || action) && (
        <View style={styles.header}>
          <View style={styles.headerText}>
            {title ? <Text style={styles.title}>{title}</Text> : null}
            {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
          </View>
          {action}
        </View>
      )}
      <View style={contentStyle}>{children}</View>
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
    ...shadows.md,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  headerText: {
    flex: 1,
  },
  title: {
    ...typography.headline,
    color: colors.ink,
  },
  subtitle: {
    ...typography.caption,
    color: colors.inkMuted,
    marginTop: 2,
  },
});
