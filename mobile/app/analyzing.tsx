import React, { useEffect, useRef, useState } from "react";
import { Animated, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";

import Banner from "../components/ui/Banner";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import StepDots from "../components/ui/StepDots";
import { analyzeImage, ApiError } from "../services/api";
import { getCapturedImageUri } from "../services/imageStore";
import { colors, layout, radius, shadows, typography } from "../theme";

const STEPS = ["Upload", "Detect", "Measure", "Grade"];

const ROTATING_HINTS = [
  "Uploading image securely…",
  "Detecting every bulb in frame…",
  "Measuring diameter and defects…",
  "Applying NCCF grading rules…",
];

export default function AnalyzingScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ uri?: string; batchCode?: string; distanceCm?: string }>();
  const started = useRef(false);

  const [currentStep, setCurrentStep] = useState(0);
  const [hintIndex, setHintIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const pulseAnim = useRef(new Animated.Value(1)).current;

  // Pulse animation for stage icon
  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.15,
          duration: 600,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 600,
          useNativeDriver: true,
        }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, [pulseAnim]);

  // Step advancement timer
  useEffect(() => {
    if (error) return;
    const stepTimer = setInterval(() => {
      setCurrentStep((prev) => (prev < 2 ? prev + 1 : prev));
      setHintIndex((prev) => (prev + 1) % ROTATING_HINTS.length);
    }, 900);
    return () => clearInterval(stepTimer);
  }, [error]);

  // Main pipeline trigger
  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const run = async () => {
      const pUri = Array.isArray(params.uri) ? params.uri[0] : params.uri;
      const paramUri = pUri || "";
      const uri = paramUri
        ? decodeURIComponent(paramUri)
        : getCapturedImageUri() ?? "";
      const pBatchCode = Array.isArray(params.batchCode)
        ? params.batchCode[0]
        : params.batchCode;
      const batchCode = pBatchCode || undefined;
      
      const pDist = Array.isArray(params.distanceCm) ? params.distanceCm[0] : params.distanceCm;
      const distanceCm = pDist ? parseFloat(pDist) : undefined;

      if (!uri) {
        setError("No image received — returning to camera.");
        setTimeout(() => router.back(), 1500);
        return;
      }

      try {
        const result = await analyzeImage(uri, batchCode, distanceCm);
        setCurrentStep(3); // Grade step complete
        router.replace({
          pathname: "/results",
          params: { batchCode: result.batch_id },
        });
      } catch (err) {
        if (err instanceof ApiError) {
          const friendly =
            err.code === "NOTHING_DETECTED"
              ? "No onions detected in the image.\nTry a clearer photo with better lighting."
              : err.code === "UNSUPPORTED_FILE_TYPE"
              ? "Unsupported file type. Please use JPG, JPEG, or PNG."
              : err.message;
          setError(friendly);
        } else {
          setError((err as Error).message ?? "Pipeline execution failed. Try again.");
        }
      }
    };

    run();
  }, [params, router]);

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.centerContainer}>
      <View style={styles.webWrapper}>
        {error ? (
          <Card style={styles.errorCard}>
            <Banner variant="error" message="Analysis Failed" />
            <Text style={styles.errorMsg}>{error}</Text>
            <Button
              label="← Go Back & Try Again"
              onPress={() => router.back()}
              variant="primary"
              size="lg"
              style={{ marginTop: 16 }}
            />
          </Card>
        ) : (
          <Card style={styles.stageCard}>
            {/* Animated Pulsing Icon Stage */}
            <View style={styles.stageCircle}>
              <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
                <Text style={styles.onionIcon}>🧅</Text>
              </Animated.View>
            </View>

            <Text style={styles.stageTitle}>Analyzing Onion Quality</Text>
            <Text style={styles.rotatingHint}>{ROTATING_HINTS[hintIndex]}</Text>

            {/* StepDots Progress Bar */}
            <View style={styles.stepsContainer}>
              <StepDots steps={STEPS} currentStep={currentStep} />
            </View>

            <Text style={styles.caption}>Usually completes under 5 seconds</Text>
          </Card>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  centerContainer: {
    flexGrow: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  webWrapper: {
    width: "100%",
    maxWidth: layout.maxWebWidth,
  },
  stageCard: {
    alignItems: "center",
    paddingVertical: 32,
    paddingHorizontal: 20,

  },
  stageCircle: {
    width: 100,
    height: 100,
    borderRadius: radius.pill,
    backgroundColor: colors.primarySoft,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 20,
  },
  onionIcon: {
    fontSize: 50,
  },
  stageTitle: {
    ...typography.title2,
    color: colors.ink,
    textAlign: "center",
  },
  rotatingHint: {
    ...typography.headline,
    color: colors.primary,
    textAlign: "center",
    marginTop: 6,
    marginBottom: 24,
    height: 24,
  },
  stepsContainer: {
    width: "100%",
    marginVertical: 16,
  },
  caption: {
    ...typography.caption,
    color: colors.inkMuted,
    marginTop: 16,
    textAlign: "center",
  },
  errorCard: {
    padding: 20,
    alignItems: "center",
  },
  errorMsg: {
    ...typography.body,
    color: colors.ink,
    textAlign: "center",
    marginVertical: 12,
    lineHeight: 22,
  },
});
