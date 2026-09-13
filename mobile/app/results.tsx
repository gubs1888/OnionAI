import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";

import DefectChart from "../components/DefectChart";
import ResultCard from "../components/ResultCard";
import Banner from "../components/ui/Banner";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import CountUp from "../components/ui/CountUp";
import GradeRing from "../components/ui/GradeRing";
import MeterBar from "../components/ui/MeterBar";
import SectionTitle from "../components/ui/SectionTitle";
import { SkeletonCard } from "../components/ui/Skeleton";
import StatTile from "../components/ui/StatTile";
import { getAssessment, ApiError } from "../services/api";
import { colors, layout, radius, shadows, typography } from "../theme";
import { Assessment } from "../types/assessment";

export default function ResultsScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ batchCode?: string | string[] }>();
  const pBatchCode = Array.isArray(params.batchCode)
    ? params.batchCode[0]
    : params.batchCode;
  const batchCode = pBatchCode || "DEMO-001";
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    getAssessment(batchCode)
      .then(setAssessment)
      .catch((err) => {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Could not load assessment details. Try analyzing this batch.");
        }
      });
  }, [batchCode]);

  if (error) {
    return (
      <ScrollView style={styles.screen} contentContainerStyle={styles.centerContainer}>
        <View style={styles.webWrapper}>
          <Card style={{ padding: 24, alignItems: "center" }}>
            <Banner variant="error" message="Assessment Not Found" />
            <Text style={{ ...typography.body, color: colors.ink, textAlign: "center", marginVertical: 16 }}>
              {error}
            </Text>
            <Button
              label="📷 Capture Photo for this Batch"
              onPress={() =>
                router.push({
                  pathname: "/camera",
                  params: { batchCode },
                })
              }
              variant="primary"
              size="lg"
              style={{ width: "100%", marginBottom: 10 }}
            />
            <Button
              label="← Back to Home"
              onPress={() => router.dismissTo("/")}
              variant="secondary"
              size="md"
              style={{ width: "100%" }}
            />
          </Card>
        </View>
      </ScrollView>
    );
  }

  if (!assessment) {
    return (
      <ScrollView style={styles.screen} contentContainerStyle={styles.centerContainer}>
        <View style={styles.webWrapper}>
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </View>
      </ScrollView>
    );
  }

  const isLowConfidence = assessment.confidence < 70;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.webWrapper}>
        {/* DEMO Banner — mandatory unmissable strip when is_demo */}
        {assessment.is_demo ? (
          <Banner
            variant="demo"
            message="DEMO DATA — synthetic result, not real AI output"
          />
        ) : (
          <Banner
            variant="success"
            message="Verified AI analysis"
          />
        )}



        {/* Grade Hero Card */}
        <Card style={styles.heroCard}>
          <View style={styles.heroRow}>
            <GradeRing grade={assessment.grade} score={assessment.quality_score} />
            <View style={styles.heroMeta}>
              <Text style={styles.batchCode}>{assessment.batch_id}</Text>
            </View>
          </View>
        </Card>

        {/* Counts 2x3 Grid */}
        <SectionTitle title="Batch Counts" subtitle="Total bulbs inspected and defect distribution" />
        <View style={styles.grid}>
          <View style={styles.gridRow}>
            <StatTile
              label="Total Bulbs"
              value={assessment.total_onions}
              bgColor={colors.bg}
              style={styles.gridItem}
            />
            <StatTile
              label="Healthy"
              value={assessment.healthy}
              colorDot={colors.category.healthy}
              dimmed={assessment.healthy === 0}
              style={styles.gridItem}
            />
          </View>
          <View style={styles.gridRow}>
            <StatTile
              label="Damaged"
              value={assessment.damaged}
              colorDot={colors.category.damaged}
              dimmed={assessment.damaged === 0}
              style={styles.gridItem}
            />
            <StatTile
              label="Rotten"
              value={assessment.rotten}
              colorDot={colors.category.rotten}
              dimmed={assessment.rotten === 0}
              style={styles.gridItem}
            />
          </View>
          <View style={styles.gridRow}>
            <StatTile
              label="Sprouted"
              value={assessment.sprouted}
              colorDot={colors.category.sprouted}
              dimmed={assessment.sprouted === 0}
              style={styles.gridItem}
            />
            <StatTile
              label="Undersized"
              value={assessment.undersized}
              colorDot={colors.category.undersized}
              dimmed={assessment.undersized === 0}
              style={styles.gridItem}
            />
          </View>
        </View>

        {/* Defect Chart */}
        <DefectChart
          counts={{
            healthy: assessment.healthy,
            damaged: assessment.damaged,
            rotten: assessment.rotten,
            sprouted: assessment.sprouted,
            undersized: assessment.undersized,
          }}
        />

        {/* Key Quality Metrics MeterBars */}
        <Card title="Quality Indicators" style={{ marginVertical: 12 }}>
          <MeterBar
            label="Defect Rate"
            value={assessment.defect_percentage}
            color={colors.amber}
          />
          <MeterBar
            label="URS (Under Relaxed Specs)"
            value={assessment.urs_percentage}
            color={colors.red}
          />
        </Card>

        {/* Full Contract Rows Card */}
        <ResultCard assessment={assessment} />

        {/* Reasons Card */}
        <Card title="Grade Rationale" style={{ marginBottom: 20 }}>
          {assessment.reasons.length === 0 ? (
            <Text style={styles.noReasons}>No deductions recorded for this lot.</Text>
          ) : (
            assessment.reasons.map((reason, idx) => (
              <View key={idx} style={styles.reasonRow}>
                <View style={styles.reasonDot} />
                <Text style={styles.reasonText}>{reason}</Text>
              </View>
            ))
          )}
        </Card>

        {/* Actions */}
        <Button
          label="View PDF Report →"
          onPress={() =>
            router.push({
              pathname: "/report",
              params: {
                assessmentId: String(assessment.assessment_id),
                batchCode,
              },
            })
          }
          variant="primary"
          size="lg"
          style={{ marginBottom: 12 }}
        />

        <Button
          label="Analyze Another Batch"
          onPress={() => router.dismissTo("/")}
          variant="secondary"
          size="lg"
        />
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
  centerContainer: {
    padding: 16,
    alignItems: "center",
  },
  webWrapper: {
    width: "100%",
    maxWidth: layout.maxWebWidth,
  },
  heroCard: {
    backgroundColor: colors.surface,
    padding: 20,
    marginBottom: 8,
  },
  heroRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  heroMeta: {
    marginLeft: 20,
    flex: 1,
  },
  batchCode: {
    ...typography.title1,
    fontSize: 28,
    color: colors.primary,
    fontWeight: "800",
  },
  scoreCaption: {
    ...typography.caption,
    color: colors.inkMuted,
    marginTop: 2,
  },
  scoreRow: {
    flexDirection: "row",
    alignItems: "baseline",
    marginVertical: 2,
  },
  scoreNumber: {
    ...typography.title1,
    fontSize: 26,
    color: colors.ink,
    fontWeight: "900",
  },
  scoreMax: {
    ...typography.caption,
    color: colors.inkMuted,
    fontSize: 13,
  },
  modelVersion: {
    ...typography.micro,
    color: colors.inkMuted,
    marginTop: 4,
  },
  grid: {
    marginBottom: 8,
  },
  gridRow: {
    flexDirection: "row",
    marginBottom: 10,
  },
  gridItem: {
    flex: 1,
    marginHorizontal: 4,
  },
  reasonRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginVertical: 4,
  },
  reasonDot: {
    width: 6,
    height: 6,
    borderRadius: radius.pill,
    backgroundColor: colors.amber,
    marginTop: 7,
    marginRight: 10,
  },
  reasonText: {
    ...typography.body,
    fontFamily: typography.mono.fontFamily,
    fontSize: 13,
    color: colors.ink,
    flex: 1,
    lineHeight: 18,
  },
  noReasons: {
    ...typography.caption,
    color: colors.inkMuted,
  },
});
