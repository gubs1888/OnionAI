/**
 * RESULTS — the full assessment contract on one screen:
 * grade, quality score, counts, defect %, URS %, confidence, reasons.
 */

import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";

import DefectChart from "../components/DefectChart";
import GradeBadge from "../components/GradeBadge";
import ResultCard from "../components/ResultCard";
import { getAssessment } from "../services/api";
import { Assessment } from "../types/assessment";

export default function ResultsScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ batchCode?: string }>();
  const batchCode = typeof params.batchCode === "string" ? params.batchCode : "DEMO-001";
  const [assessment, setAssessment] = useState<Assessment | null>(null);

  useEffect(() => {
    getAssessment(batchCode).then(setAssessment);
  }, [batchCode]);

  if (!assessment) {
    return (
      <View style={styles.center}>
        <Text style={styles.loading}>Loading assessment…</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      {assessment.is_demo ? (
        <View style={styles.demoBanner}>
          <Text style={styles.demoBannerText}>
            DEMO DATA — synthetic result, not real AI output
          </Text>
        </View>
      ) : null}

      <View style={styles.headerRow}>
        <GradeBadge grade={assessment.grade} />
        <View style={styles.headerText}>
          <Text style={styles.batch}>{assessment.batch_id}</Text>
          <Text style={styles.score}>{assessment.quality_score.toFixed(1)} / 100</Text>
          <Text style={styles.model}>{assessment.model_version}</Text>
        </View>
      </View>

      <ResultCard assessment={assessment} />
      <DefectChart
        counts={{
          healthy: assessment.healthy,
          damaged: assessment.damaged,
          rotten: assessment.rotten,
          sprouted: assessment.sprouted,
          undersized: assessment.undersized,
        }}
      />

      <Text style={styles.sectionTitle}>Reasons</Text>
      {assessment.reasons.length === 0 ? (
        <Text style={styles.reason}>No deductions.</Text>
      ) : (
        assessment.reasons.map((reason, i) => (
          <Text key={i} style={styles.reason}>
            • {reason}
          </Text>
        ))
      )}

      <Pressable
        style={styles.primary}
        onPress={() =>
          router.push({
            pathname: "/report",
            params: { assessmentId: String(assessment.assessment_id), batchCode },
          })
        }
      >
        <Text style={styles.primaryText}>View report →</Text>
      </Pressable>
      <Pressable style={styles.secondary} onPress={() => router.dismissTo("/")}>
        <Text style={styles.secondaryText}>Analyze another batch</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { padding: 20, paddingBottom: 48 },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  loading: { color: "#6B7280" },
  demoBanner: {
    backgroundColor: "#F59E0B",
    borderRadius: 10,
    padding: 10,
    marginBottom: 16,
  },
  demoBannerText: { color: "#fff", fontWeight: "800", textAlign: "center", fontSize: 13 },
  headerRow: { flexDirection: "row", alignItems: "center", marginBottom: 20 },
  headerText: { marginLeft: 16 },
  batch: { fontSize: 16, fontWeight: "700", color: "#111827" },
  score: { fontSize: 22, fontWeight: "800", color: "#14532D" },
  model: { fontSize: 11, color: "#9CA3AF" },
  sectionTitle: { fontSize: 16, fontWeight: "700", color: "#111827", marginTop: 20, marginBottom: 8 },
  reason: { fontSize: 12, color: "#4B5563", lineHeight: 18 },
  primary: {
    backgroundColor: "#16A34A",
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 24,
  },
  primaryText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  secondary: {
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 10,
  },
  secondaryText: { color: "#374151", fontWeight: "600" },
});
