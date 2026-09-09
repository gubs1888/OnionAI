/**
 * CAMERA / UPLOAD — capture with the device camera or pick from gallery.
 * Both paths hand the image URI to ANALYZING which runs the pipeline.
 */

import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as ImagePicker from "expo-image-picker";

import CameraView from "../components/CameraView";
import { setCapturedImageUri } from "../services/imageStore";

export default function CameraScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ batchCode?: string; batchName?: string }>();
  const batchCode = typeof params.batchCode === "string" ? params.batchCode : undefined;
  const [error, setError] = useState<string | null>(null);

  const proceed = (uri: string) => {
    if (!uri) {
      setError("No image captured — try again.");
      return;
    }
    setCapturedImageUri(uri);
    router.replace({
      pathname: "/analyzing",
      params: { batchCode: batchCode ?? "DEMO-001" },
    });
  };

  const pickFromGallery = async () => {
    setError(null);
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      quality: 0.7,
    });
    if (!result.canceled && result.assets[0]) {
      proceed(result.assets[0].uri);
    }
  };

  return (
    <View style={styles.screen}>
      <View style={styles.batchBanner}>
        <Text style={styles.batchText}>Batch: {batchCode ?? "DEMO-001 (no backend)"}</Text>
      </View>

      <CameraView onCaptured={proceed} />

      <Pressable style={styles.galleryButton} onPress={pickFromGallery}>
        <Text style={styles.galleryButtonText}>Pick from gallery instead</Text>
      </Pressable>
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#111827" },
  batchBanner: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: "#1F2937",
  },
  batchText: { color: "#D1FAE5", fontSize: 12, fontWeight: "600" },
  galleryButton: {
    marginHorizontal: 20,
    marginBottom: 24,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#374151",
    paddingVertical: 12,
    alignItems: "center",
  },
  galleryButtonText: { color: "#D1FAE5", fontWeight: "600" },
  error: { color: "#FCA5A5", textAlign: "center", marginBottom: 16, fontSize: 12 },
});
