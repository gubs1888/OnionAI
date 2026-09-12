import React, { useCallback, useEffect, useState } from "react";
import {
  FlatList,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { Link, useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { BlurView } from "expo-blur";

import BatchCard from "../components/BatchCard";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Chip from "../components/ui/Chip";
import EmptyState from "../components/ui/EmptyState";
import SectionTitle from "../components/ui/SectionTitle";
import { SkeletonCard } from "../components/ui/Skeleton";
import StatTile from "../components/ui/StatTile";
import { clearBatches, healthCheck, listBatches } from "../services/api";
import { colors, layout, radius, shadows, typography, glass, borders } from "../theme";
import { Batch, HealthInfo } from "../types/assessment";

export default function HomeScreen() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [h, b] = await Promise.all([healthCheck(), listBatches()]);
      setHealth(h);
      setBatches(b);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const onRefresh = () => {
    setRefreshing(true);
    refresh();
  };

  const handleClearAll = async () => {
    await clearBatches();
    refresh();
  };

  const backendUp = health !== null;
  const demoActive = health?.demo_mode ?? true;

  // Compute stats from batches
  const batchesGraded = batches.length;
  const lastBatch = batches.length > 0 ? batches[0] : null;

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.contentContainer}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
      }
    >
      <View style={styles.webWrapper}>
        {/* Hero Header */}
        <LinearGradient
          colors={[colors.brand600, colors.brand800]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.heroContainer}
        >
          <View style={styles.heroTop}>
            <View style={styles.heroTextCol}>
              <Text style={styles.appName}>OnionLens</Text>
              <Text style={styles.subtitle}>AI Onion Grading · SIH 2026</Text>
            </View>
            <View style={styles.heroIconBadge}>
              <Text style={styles.heroIcon}>🧅</Text>
            </View>
          </View>

          {/* Floating Health Status Bar */}
          <Pressable onPress={refresh} style={styles.statusCardContainer}>
            <BlurView intensity={30} tint="dark" style={styles.statusCard}>
              <View style={styles.statusRow}>
                <View
                  style={[
                    styles.statusDot,
                    { backgroundColor: backendUp ? colors.accent : colors.amber },
                  ]}
                />
                <Text style={styles.statusText} numberOfLines={1}>
                  {backendUp
                    ? `Connected · v${health?.version ?? "0.1.0"}`
                    : "Backend offline — showing MOCK data"}
                </Text>
                {demoActive && (
                  <Chip label="DEMO MODE" variant="warning" style={styles.demoChip} />
                )}
              </View>
            </BlurView>
          </Pressable>
        </LinearGradient>

        {/* Primary CTA */}
        <View style={styles.actionContainer}>
          <Link href="/batch" asChild>
            <Button
              label="＋ New grading batch"
              onPress={() => {}}
              variant="primary"
              size="lg"
            />
          </Link>
        </View>

        {/* Quick Stats Summary Row */}
        <View style={styles.statsRow}>
          <StatTile
            label="Batches Graded"
            value={batchesGraded}
            style={styles.statTile}
          />
          <StatTile
            label="Last Status"
            value={lastBatch ? lastBatch.status.toUpperCase() : "-"}
            style={styles.statTile}
          />
        </View>

        {/* Recent Batches List Header */}
        <SectionTitle
          title="Recent Batches"
          actionText={batches.length > 0 ? "Clear all" : undefined}
          onAction={handleClearAll}
        />

        {/* Batch Cards or Loading Skeletons */}
        {loading ? (
          <View style={{ paddingHorizontal: 16 }}>
            <SkeletonCard />
            <SkeletonCard />
          </View>
        ) : (
          <FlatList
            data={batches}
            keyExtractor={(item) => `${item.id}-${item.batch_code}`}
            renderItem={({ item }) => (
              <View style={{ paddingHorizontal: 16 }}>
                <BatchCard
                  batch={item}
                  onPress={() =>
                    router.push({
                      pathname: "/camera",
                      params: { batchCode: item.batch_code, batchName: item.name },
                    })
                  }
                />
              </View>
            )}
            ListEmptyComponent={
              <View style={{ paddingHorizontal: 16 }}>
                <EmptyState
                  title="No batches yet"
                  message="Create your first onion grading batch to start AI quality assessment."
                  icon="🧅"
                  action={
                    <Link href="/batch" asChild>
                      <Button
                        label="Create Batch"
                        onPress={() => {}}
                        variant="primary"
                        size="md"
                      />
                    </Link>
                  }
                />
              </View>
            }
            scrollEnabled={false}
          />
        )}

        <Text style={styles.footerNote}>
          Demo build · results may be synthetic when backend is offline
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  contentContainer: {
    paddingBottom: 40,
    alignItems: "center",
  },
  webWrapper: {
    width: "100%",
    maxWidth: layout.maxWebWidth,
  },
  heroContainer: {
    backgroundColor: colors.primary,
    borderBottomLeftRadius: radius.L,
    borderBottomRightRadius: radius.L,
    padding: 24,
    paddingBottom: 36,
    paddingTop: 100, // accommodate transparent header
    position: "relative",
    ...shadows.md,
  },
  heroTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  heroTextCol: {
    flex: 1,
  },
  appName: {
    ...typography.display,
    color: "#FFFFFF",
  },
  subtitle: {
    ...typography.caption,
    color: "rgba(255, 255, 255, 0.75)",
    marginTop: 2,
  },
  heroIconBadge: {
    width: 48,
    height: 48,
    borderRadius: radius.pill,
    backgroundColor: "rgba(255, 255, 255, 0.15)",
    alignItems: "center",
    justifyContent: "center",
  },
  heroIcon: {
    fontSize: 26,
  },
  statusCardContainer: {
    position: "absolute",
    bottom: -20,
    left: 20,
    right: 20,
    borderRadius: radius.M,
    ...shadows.md,
  },
  statusCard: {
    backgroundColor: colors.card,
    borderRadius: radius.M,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: borders.dim,
    overflow: "hidden",
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: radius.pill,
    marginRight: 8,
  },
  statusText: {
    ...typography.caption,
    color: colors.ink,
    fontWeight: "600",
    flex: 1,
  },
  demoChip: {
    marginLeft: 8,
  },
  actionContainer: {
    marginTop: 36,
    paddingHorizontal: 16,
  },
  statsRow: {
    flexDirection: "row",
    marginHorizontal: 12,
    marginTop: 16,
  },
  statTile: {
    flex: 1,
    marginHorizontal: 4,
  },
  footerNote: {
    ...typography.micro,
    color: colors.inkMuted,
    textAlign: "center",
    marginTop: 32,
    paddingHorizontal: 16,
  },
});
