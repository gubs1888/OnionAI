/**
 * REPORT — generates the PDF report for an assessment and shows its metadata.
 * On a real device "Open PDF" hits the backend download URL.
 */

import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import * as Linking from "expo-linking";

import { absoluteUrl, generateReport } from "../services/api";
import { ReportInfo } from "../types/assessment";

export default function ReportScreen() {
  const params = useLocalSearchParams<{ assessmentId?: string; batchCode?: string }>();
  const assessmentId = Number(
    typeof params.assessmentId === "string" ? params.assessmentId : "0"
  );
  const batchCode = typeof params.batchCode === "string" ? params.batchCode : "-";
  const [report, setReport] = useState<ReportInfo | null>(null);
  const [note, setNote] = useState("Generating PDF…");

  useEffect(() => {
    generateReport(assessmentId)
      .then((r) => {
        setReport(r);
        setNote("");
      })
      .catch(() => setNote("Could not generate a report."));
  }, [assessmentId]);

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      {report?.is_demo ? (
        <View style={styles.demoBanner}>
          <Text style={styles.demoBannerText}>
            DEMO REPORT — generated from synthetic assessment data
          </Text>
        </View>
      ) : null}

      <View style={styles.card}>
        <Text style={styles.title}>Assessment report</Text>
        <Text style={styles.line}>Batch: {batchCode}</Text>
        <Text style={styles.line}>Assessment: #{assessmentId}</Text>
        {report ? (
          <>
            <Text style={styles.line}>Report code: {report.report_code}</Text>
            <Text style={styles.line}>Format: {report.format.toUpperCase()}</Text>
            <Text style={styles.line}>
              Generated: {new Date(report.generated_at).toLocaleString()}
            </Text>
          </>
        ) : (
          <Text style={styles.line}>{note}</Text>
        )}
      </View>

      {report ? (
        <Pressable
          style={styles.primary}
          onPress={() => Linking.openURL(absoluteUrl(report.download_url))}
        >
          <Text style={styles.primaryText}>Open PDF</Text>
        </Pressable>
      ) : null}
      <Text style={styles.hint}>
        The PDF is produced by the backend (ReportLab) and watermarked when the
        underlying data is DEMO.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { padding: 20 },
  demoBanner: { backgroundColor: "#F59E0B", borderRadius: 10, padding: 10, marginBottom: 16 },
  demoBannerText: { color: "#fff", fontWeight: "800", textAlign: "center", fontSize: 13 },
  card: { backgroundColor: "#fff", borderRadius: 16, padding: 18 },
  title: { fontSize: 17, fontWeight: "800", color: "#111827", marginBottom: 10 },
  line: { fontSize: 13, color: "#374151", marginTop: 4 },
  primary: {
    backgroundColor: "#14532D",
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 20,
  },
  primaryText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  hint: { fontSize: 11, color: "#9CA3AF", textAlign: "center", marginTop: 14 },
});
