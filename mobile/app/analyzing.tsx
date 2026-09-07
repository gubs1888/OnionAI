/**
 * ANALYZING — uploads the image (POST /api/analyze) and auto-advances to
 * RESULTS. Backend offline? The api client's MOCK fallback keeps the flow
 * alive and the result is flagged is_demo.
 */

import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";

import { analyzeImage } from "../services/api";

export default function AnalyzingScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ uri?: string; batchCode?: string }>();
  const started = useRef(false);
  const [note, setNote] = useState("Uploading image…");

  useEffect(() => {
    if (started.current) return; // guard against double-invoke
    started.current = true;

    const run = async () => {
      const uri = typeof params.uri === "string" ? params.uri : "";
      const batchCode = typeof params.batchCode === "string" ? params.batchCode : undefined;
      if (!uri) {
        setNote("No image received — going back.");
        setTimeout(() => router.back(), 1200);
        return;
      }
      setNote("Running quality pipeline…");
      const result = await analyzeImage(uri, batchCode);
      router.replace({
        pathname: "/results",
        params: { batchCode: result.batch_id },
      });
    };
    run();
  }, [params, router]);

  return (
    <View style={styles.center}>
      <ActivityIndicator size="large" color="#16A34A" />
      <Text style={styles.title}>Analyzing onions…</Text>
      <Text style={styles.note}>{note}</Text>
      <Text style={styles.hint}>
        DEMO MODE returns synthetic results in ~1s. Real YOLO inference will
        replace it without any UI change.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 32 },
  title: { fontSize: 20, fontWeight: "700", color: "#111827", marginTop: 20 },
  note: { fontSize: 14, color: "#6B7280", marginTop: 8 },
  hint: {
    fontSize: 11,
    color: "#9CA3AF",
    textAlign: "center",
    marginTop: 24,
    lineHeight: 16,
  },
});
