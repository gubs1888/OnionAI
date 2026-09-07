/**
 * BatchCard — one row in the HOME batch list.
 * TODO(TEAM C): thumbnail + status color states.
 */

import { Pressable, StyleSheet, Text, View } from "react-native";

import { Batch } from "../types/assessment";

type Props = {
  batch: Batch;
  onPress?: () => void;
};

const STATUS_COLOR: Record<Batch["status"], string> = {
  created: "#6B7280",
  analyzing: "#D97706",
  analyzed: "#16A34A",
  failed: "#DC2626",
};

export default function BatchCard({ batch, onPress }: Props) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.card, pressed && { opacity: 0.9 }]}>
      <View style={styles.row}>
        <Text style={styles.code}>{batch.batch_code}</Text>
        <View style={[styles.chip, { backgroundColor: `${STATUS_COLOR[batch.status]}22` }]}>
          <Text style={[styles.chipText, { color: STATUS_COLOR[batch.status] }]}>
            {batch.status.toUpperCase()}
          </Text>
        </View>
      </View>
      <Text style={styles.name}>{batch.name}</Text>
      <Text style={styles.meta}>
        {batch.variety ?? "variety —"} · {batch.source ?? "source —"} ·{" "}
        {batch.image_count} image(s)
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#fff",
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
  },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  code: { fontWeight: "800", color: "#14532D", fontSize: 13 },
  chip: { borderRadius: 999, paddingHorizontal: 8, paddingVertical: 3 },
  chipText: { fontSize: 10, fontWeight: "800" },
  name: { fontSize: 15, fontWeight: "600", color: "#111827", marginTop: 6 },
  meta: { fontSize: 11, color: "#9CA3AF", marginTop: 4 },
});
