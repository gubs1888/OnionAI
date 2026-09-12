import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { colors, radius, shadows, typography, borders } from "../theme";
import { Batch } from "../types/assessment";
import Chip from "./ui/Chip";
import { BlurView } from "expo-blur";

type Props = {
  batch: Batch;
  onPress?: () => void;
};

const STATUS_CONFIG: Record<
  Batch["status"],
  { label: string; variant: "success" | "warning" | "error" | "neutral"; color: string }
> = {
  created: { label: "CREATED", variant: "neutral", color: colors.inkMuted },
  analyzing: { label: "ANALYZING", variant: "warning", color: colors.amber },
  analyzed: { label: "ANALYZED", variant: "success", color: colors.accent },
  failed: { label: "FAILED", variant: "error", color: colors.red },
};

export default function BatchCard({ batch, onPress }: Props) {
  const statusCfg = STATUS_CONFIG[batch.status] ?? STATUS_CONFIG.created;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.cardContainer, pressed && styles.pressed]}
    >
      <BlurView intensity={20} tint="dark" style={styles.card}>
        <View style={[styles.spine, { backgroundColor: statusCfg.color }]} />
        <View style={styles.content}>
          <View style={styles.topRow}>
            <Text style={styles.code}>{batch.batch_code}</Text>
            <View style={styles.chipGroup}>
              <Chip label={statusCfg.label} variant={statusCfg.variant} />
            </View>
          </View>

          <Text style={styles.name} numberOfLines={1}>
            {batch.name}
          </Text>

          <View style={styles.bottomRow}>
            <Text style={styles.meta}>
              {batch.variety ? `${batch.variety}` : "Variety unspecified"}
              {batch.source ? ` · ${batch.source}` : ""}
            </Text>
            <Text style={styles.imageCount}>
              📷 {batch.image_count} {batch.image_count === 1 ? "photo" : "photos"}
            </Text>
          </View>
        </View>
        <Text style={styles.chevron}>›</Text>
      </BlurView>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  cardContainer: {
    borderRadius: radius.XL,
    marginBottom: 14,
    ...shadows.md,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: radius.XL,
    borderWidth: 1,
    borderColor: borders.accent,
    flexDirection: "row",
    alignItems: "center",
    overflow: "hidden",
  },
  pressed: {
    opacity: 0.88,
    transform: [{ scale: 0.99 }],
  },
  spine: {
    width: 5,
    alignSelf: "stretch",
  },
  content: {
    flex: 1,
    padding: 16,
    paddingLeft: 14,
  },
  topRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  code: {
    ...typography.headline,
    color: colors.primary,
  },
  chipGroup: {
    flexDirection: "row",
    alignItems: "center",
  },
  name: {
    ...typography.bodyMedium,
    color: colors.ink,
    marginTop: 6,
  },
  bottomRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 10,
  },
  meta: {
    ...typography.caption,
    color: colors.inkMuted,
    flex: 1,
  },
  imageCount: {
    ...typography.micro,
    color: colors.inkMuted,
    marginLeft: 8,
  },
  chevron: {
    fontSize: 22,
    color: colors.inkMuted,
    paddingRight: 16,
    fontWeight: "300",
  },
});
