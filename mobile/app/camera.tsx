import React, { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as ImagePicker from "expo-image-picker";

import CameraView from "../components/CameraView";
import Chip from "../components/ui/Chip";
import { setCapturedImageUri } from "../services/imageStore";
import { colors, layout, radius, typography } from "../theme";

export default function CameraScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ batchCode?: string; batchName?: string }>();
  const batchCode = typeof params.batchCode === "string" ? params.batchCode : undefined;
  const batchName = typeof params.batchName === "string" ? params.batchName : undefined;
  const [error, setError] = useState<string | null>(null);
  const [cameraDistance, setCameraDistance] = useState<number>(0); // Default 0cm

  const proceed = (uri: string) => {
    if (!uri) {
      setError("No image captured — try again.");
      return;
    }
    setCapturedImageUri(uri);
    router.replace({
      pathname: "/analyzing",
      params: { ...(batchCode ? { batchCode } : {}), distanceCm: cameraDistance.toString() },
    });
  };

  const pickFromGallery = async () => {
    setError(null);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ["images"],
        quality: 0.7,
      });
      if (!result.canceled && result.assets[0]) {
        proceed(result.assets[0].uri);
      }
    } catch (err) {
      setError("Failed to open gallery. Try camera capture.");
    }
  };

  return (
    <View style={styles.screen}>
      <View style={styles.webWrapper}>
        {/* Top Bar Banner */}
        <View style={styles.topBar}>
          <View style={styles.batchInfo}>
            <Text style={styles.batchLabel} numberOfLines={1}>
              Batch: {batchCode ?? "Walk-in Batch"} {batchName ? `· ${batchName}` : ""}
            </Text>
          </View>
          <Pressable onPress={() => router.back()} style={styles.closeBtn} hitSlop={12}>
            <Text style={styles.closeText}>✕</Text>
          </Pressable>
        </View>

        {/* Camera View preview container */}
        <View style={styles.cameraContainer}>
          <CameraView onCaptured={proceed} />
        </View>
        
        {/* Distance Selector */}
        <View style={styles.distanceContainer}>
          <Text style={styles.distanceLabel}>Camera Distance (for size calc):</Text>
          <View style={styles.distanceRow}>
            {[0, 10, 20, 30, 40, 50, 60].map((d) => (
              <Pressable
                key={d}
                onPress={() => setCameraDistance(d)}
                style={[styles.distBtn, cameraDistance === d && styles.distBtnActive]}
              >
                <Text style={[styles.distText, cameraDistance === d && styles.distTextActive]}>{d}cm</Text>
              </Pressable>
            ))}
          </View>
        </View>

        {/* Quick Framing Tips Row */}
        <View style={styles.tipsRow}>
          <Chip label="☀️ Daylight Best" variant="neutral" style={styles.tipChip} />
          <Chip label="📐 Top-Down Angle" variant="neutral" style={styles.tipChip} />
          <Chip label="📦 Fill Frame" variant="neutral" style={styles.tipChip} />
        </View>

        {/* Bottom Actions Row */}
        <View style={styles.bottomBar}>
          <Pressable style={styles.galleryBtn} onPress={pickFromGallery}>
            <Text style={styles.galleryIcon}>🖼️</Text>
            <Text style={styles.galleryText}>Pick from Gallery</Text>
          </Pressable>
        </View>

        {error ? <Text style={styles.errorText}>{error}</Text> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#101619",
    alignItems: "center",
  },
  webWrapper: {
    width: "100%",
    maxWidth: layout.maxWebWidth,
    flex: 1,
  },
  topBar: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "rgba(16, 22, 25, 0.95)",
    zIndex: 10,
  },
  batchInfo: {
    flex: 1,
    marginRight: 12,
  },
  batchLabel: {
    ...typography.caption,
    color: "#DCFCE7",
    fontWeight: "700",
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: radius.pill,
    backgroundColor: "rgba(255, 255, 255, 0.15)",
    alignItems: "center",
    justifyContent: "center",
  },
  closeText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },
  cameraContainer: {
    flex: 1,
    position: "relative",
  },
  distanceContainer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: "#1A242B",
    borderTopWidth: 1,
    borderTopColor: "rgba(255,255,255,0.1)",
  },
  distanceLabel: {
    ...typography.caption,
    color: "#9CA3AF",
    marginBottom: 12,
    textAlign: "center",
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 1.2,
  },
  distanceRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "rgba(0,0,0,0.4)",
    borderRadius: radius.pill,
    padding: 6,
  },
  distBtn: {
    flex: 1,
    paddingVertical: 12,
    alignItems: "center",
    borderRadius: radius.pill,
  },
  distBtnActive: {
    backgroundColor: colors.primary,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  distText: {
    ...typography.caption,
    color: "#9CA3AF",
    fontWeight: "700",
  },
  distTextActive: {
    color: "#101619",
    fontWeight: "800",
  },
  tipsRow: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: 8,
    backgroundColor: "rgba(16, 22, 25, 0.9)",
  },
  tipChip: {
    marginHorizontal: 4,
    backgroundColor: "rgba(255, 255, 255, 0.1)",
  },
  bottomBar: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: "#101619",
    alignItems: "center",
  },
  galleryBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.3)",
    backgroundColor: "rgba(255, 255, 255, 0.08)",
  },
  galleryIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  galleryText: {
    ...typography.headline,
    color: "#DCFCE7",
    fontSize: 14,
  },
  errorText: {
    ...typography.caption,
    color: "#FEE2E2",
    textAlign: "center",
    paddingBottom: 12,
  },
});
