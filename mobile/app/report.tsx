import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as Linking from "expo-linking";

import Banner from "../components/ui/Banner";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Chip from "../components/ui/Chip";
import { SkeletonCard } from "../components/ui/Skeleton";
import { absoluteUrl, generateReport } from "../services/api";
import { colors, layout, radius, shadows, typography } from "../theme";
import { ReportInfo } from "../types/assessment";

export default function ReportScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{
    assessmentId?: string | string[];
    batchCode?: string | string[];
  }>();

  const pAssessmentId = Array.isArray(params.assessmentId)
    ? params.assessmentId[0]
    : params.assessmentId;
  const assessmentId = Number(pAssessmentId || "0");
  const pBatchCode = Array.isArray(params.batchCode)
    ? params.batchCode[0]
    : params.batchCode;
  const batchCode = pBatchCode || "-";

  const [report, setReport] = useState<ReportInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReport = () => {
    setLoading(true);
    setError(null);
    generateReport(assessmentId)
      .then((r) => {
        setReport(r);
        setLoading(false);
      })
      .catch(() => {
        setError("Could not generate a report. Please try again.");
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchReport();
  }, [assessmentId]);

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.webWrapper}>
        {/* DEMO Report Banner */}
        {report?.is_demo && (
          <Banner
            variant="demo"
            message="DEMO REPORT — generated from synthetic assessment data"
          />
        )}

        {error && <Banner variant="error" message={error} />}

        {loading ? (
          <View>
            <SkeletonCard />
            <Text style={styles.loadingNote}>Generating PDF Report Document…</Text>
          </View>
        ) : report ? (
          <>
            {/* A4 Document Card */}
            <View style={styles.documentCard}>
              <View style={styles.docHeader}>
                <View style={styles.docBrand}>
                  <Text style={styles.docLogo}>🧅 OnionLens</Text>
                  <Text style={styles.docSub}>Official Quality Certificate</Text>
                </View>
                <Chip label="PDF FORMAT" variant="info" />
              </View>

              <View style={styles.divider} />

              <View style={styles.docBody}>
                <View style={styles.docRow}>
                  <Text style={styles.docLabel}>Report Code:</Text>
                  <Text style={styles.docValueCode}>{report.report_code}</Text>
                </View>

                <View style={styles.docRow}>
                  <Text style={styles.docLabel}>Batch Code:</Text>
                  <Text style={styles.docValue}>{batchCode}</Text>
                </View>

                <View style={styles.docRow}>
                  <Text style={styles.docLabel}>Assessment ID:</Text>
                  <Text style={styles.docValue}>#{assessmentId}</Text>
                </View>

                <View style={styles.docRow}>
                  <Text style={styles.docLabel}>Generated At:</Text>
                  <Text style={styles.docValue}>
                    {new Date(report.generated_at).toLocaleString()}
                  </Text>
                </View>

                <View style={styles.docRow}>
                  <Text style={styles.docLabel}>Status:</Text>
                  <Chip
                    label={report.is_demo ? "SYNTHETIC DEMO" : "VERIFIED AI"}
                    variant={report.is_demo ? "warning" : "success"}
                  />
                </View>
              </View>

              <View style={styles.docFooter}>
                <Text style={styles.watermarkText}>
                  {report.is_demo
                    ? "WATERMARKED · DEMO DATA BUILD"
                    : "SIH 2026 OFFICIAL REPORT"}
                </Text>
              </View>
            </View>

            {/* Actions */}
            <Button
              label="Open PDF Document"
              onPress={() => Linking.openURL(absoluteUrl(report.download_url))}
              variant="primary"
              size="lg"
              style={{ marginTop: 20 }}
            />

            <Button
              label="Back to Results"
              onPress={() => router.back()}
              variant="secondary"
              size="lg"
              style={{ marginTop: 10 }}
            />
          </>
        ) : (
          <Button
            label="Retry Report Generation"
            onPress={fetchReport}
            variant="primary"
            size="lg"
          />
        )}

        <Text style={styles.footerHint}>
          The PDF is produced by the backend (ReportLab) and watermarked when the
          underlying data is DEMO.
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
  content: {
    padding: 16,
    paddingBottom: 40,
    alignItems: "center",
  },
  webWrapper: {
    width: "100%",
    maxWidth: layout.maxWebWidth,
  },
  loadingNote: {
    ...typography.caption,
    color: colors.inkMuted,
    textAlign: "center",
    marginTop: 12,
  },
  documentCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.S,
    borderWidth: 2,
    borderColor: colors.line,
    padding: 20,
    marginTop: 8,
    ...shadows.md,
  },
  docHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  docBrand: {
    flex: 1,
  },
  docLogo: {
    ...typography.title2,
    color: colors.primary,
    fontWeight: "800",
  },
  docSub: {
    ...typography.caption,
    color: colors.inkMuted,
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: colors.line,
    marginVertical: 16,
  },
  docBody: {
    marginBottom: 12,
  },
  docRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginVertical: 8,
  },
  docLabel: {
    ...typography.body,
    color: colors.inkMuted,
  },
  docValue: {
    ...typography.bodyMedium,
    color: colors.ink,
    fontWeight: "600",
  },
  docValueCode: {
    ...typography.headline,
    color: colors.primary,
    fontWeight: "800",
  },
  docFooter: {
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.line,
    alignItems: "center",
  },
  watermarkText: {
    ...typography.micro,
    color: colors.inkMuted,
    letterSpacing: 1,
  },
  footerHint: {
    ...typography.micro,
    color: colors.inkMuted,
    textAlign: "center",
    marginTop: 24,
    paddingHorizontal: 16,
  },
});
