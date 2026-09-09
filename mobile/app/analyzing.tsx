/**
 * ANALYZING — uploads the image (POST /api/analyze) and auto-advances to
 * RESULTS. Backend offline? The api client's MOCK fallback keeps the flow
 * alive and the result is flagged is_demo.
 * Server errors (e.g. NOTHING_DETECTED) are shown to the user with a
 * go-back option.
 */

import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";

import { analyzeImage, ApiError } from "../services/api";
import { getCapturedImageUri } from "../services/imageStore";

export default function AnalyzingScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ uri?: string; batchCode?: string }>();
  const started = useRef(false);
  const [note, setNote] = useState("Uploading image…");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (started.current) return; // guard against double-invoke
    started.current = true;

    const run = async () => {
      const pUri = Array.isArray(params.uri) ? params.uri[0] : params.uri;
      const paramUri = pUri || "";
      const uri = paramUri ? decodeURIComponent(paramUri) : (getCapturedImageUri() ?? "");
      const pBatchCode = Array.isArray(params.batchCode) ? params.batchCode[0] : params.batchCode;
      const batchCode = pBatchCode || undefined;
      if (!uri) {
        setNote("No image received — going back.");
        setTimeout(() => router.back(), 1200);
        return;
      }
      try {
        setNote("Running quality pipeline…");
        const result = await analyzeImage(uri, batchCode);
        router.replace({
          pathname: "/results",
          params: { batchCode: result.batch_id },
        });
      } catch (err) {
        if (err instanceof ApiError) {
          // Server returned a real error — show it to the user
          const friendly =
            err.code === "NOTHING_DETECTED"
              ? "No onions detected in the image.\nTry a clearer photo with better lighting."
              : err.code === "UNSUPPORTED_FILE_TYPE"
              ? "Unsupported file type. Please use JPG, JPEG, or PNG."
              : err.message;
          setError(friendly);
        } else {
          setError("Something went wrong. Please try again.");
        }
      }
    };
    run();
  }, [params, router]);

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorIcon}>⚠️</Text>
        <Text style={styles.errorTitle}>Analysis Failed</Text>
        <Text style={styles.errorMsg}>{error}</Text>
        <Pressable
          style={styles.retryBtn}
          onPress={() => router.back()}
        >
          <Text style={styles.retryText}>← Go Back & Try Again</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={styles.center}>
      <ActivityIndicator size="large" color="#16A34A" />
      <Text style={styles.title}>Analyzing onions…</Text>
      <Text style={styles.note}>{note}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 32 },
  title: { fontSize: 20, fontWeight: "700", color: "#111827", marginTop: 20 },
  note: { fontSize: 14, color: "#6B7280", marginTop: 8 },
  errorIcon: { fontSize: 48, marginBottom: 12 },
  errorTitle: { fontSize: 22, fontWeight: "700", color: "#DC2626", marginBottom: 8 },
  errorMsg: {
    fontSize: 15,
    color: "#6B7280",
    textAlign: "center",
    lineHeight: 22,
    marginBottom: 24,
    paddingHorizontal: 16,
  },
  retryBtn: {
    backgroundColor: "#16A34A",
    paddingVertical: 12,
    paddingHorizontal: 28,
    borderRadius: 10,
  },
  retryText: { color: "#fff", fontSize: 16, fontWeight: "600" },
});
