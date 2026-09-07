/**
 * HOME — entry screen: connection status, New Batch, recent batches.
 * Placeholder data appears (clearly marked) when the backend is unreachable.
 */

import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { Link, useRouter } from "expo-router";

import BatchCard from "../components/BatchCard";
import { healthCheck, listBatches } from "../services/api";
import { Batch, HealthInfo } from "../types/assessment";

export default function HomeScreen() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    const [h, b] = await Promise.all([healthCheck(), listBatches()]);
    setHealth(h);
    setBatches(b);
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const backendUp = health !== null;
  const demoActive = health?.demo_mode ?? true;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.hero}>
        <Text style={styles.heroTitle}>AI Onion Grading</Text>
        <Text style={styles.heroSubtitle}>Smart India Hackathon 2026 — PS 26031</Text>
        <View style={[styles.pill, backendUp ? styles.pillOk : styles.pillWarn]}>
          <Text style={styles.pillText}>
            {backendUp
              ? `Backend ${health!.version} · ${health!.database}${demoActive ? " · DEMO MODE" : ""}`
              : "Backend offline — showing MOCK data"}
          </Text>
        </View>
      </View>

      <Link href="/batch" asChild>
        <Pressable style={styles.primaryButton}>
          <Text style={styles.primaryButtonText}>＋ New Batch</Text>
        </Pressable>
      </Link>

      <Text style={styles.sectionTitle}>Recent batches</Text>
      {loading ? (
        <ActivityIndicator style={{ marginTop: 16 }} color="#14532D" />
      ) : (
        <FlatList
          data={batches}
          keyExtractor={(item) => `${item.id}-${item.batch_code}`}
          renderItem={({ item }) => (
            <BatchCard
              batch={item}
              onPress={() =>
                router.push({
                  pathname: "/camera",
                  params: { batchCode: item.batch_code, batchName: item.name },
                })
              }
            />
          )}
          ListEmptyComponent={<Text style={styles.empty}>No batches yet — create one above.</Text>}
          scrollEnabled={false}
        />
      )}

      <Text style={styles.footerNote}>
        Flow: Home → New Batch → Camera → Analyzing → Results → Report
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { padding: 20, paddingBottom: 40 },
  hero: { marginBottom: 24 },
  heroTitle: { fontSize: 28, fontWeight: "800", color: "#14532D" },
  heroSubtitle: { fontSize: 13, color: "#6B7280", marginTop: 4 },
  pill: {
    alignSelf: "flex-start",
    marginTop: 12,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  pillOk: { backgroundColor: "#DCFCE7" },
  pillWarn: { backgroundColor: "#FEF3C7" },
  pillText: { fontSize: 12, fontWeight: "600", color: "#374151" },
  primaryButton: {
    backgroundColor: "#16A34A",
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
  },
  primaryButtonText: { color: "#fff", fontSize: 18, fontWeight: "700" },
  sectionTitle: { fontSize: 18, fontWeight: "700", marginTop: 28, marginBottom: 12, color: "#111827" },
  empty: { color: "#9CA3AF", textAlign: "center", marginTop: 8 },
  footerNote: { marginTop: 24, fontSize: 11, color: "#9CA3AF", textAlign: "center" },
});
