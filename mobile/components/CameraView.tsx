/**
 * CameraView — expo-camera wrapper with permission handling.
 *
 * SDK 53 API: `CameraView` + `useCameraPermissions`.
 * Falls back to a clearly-marked placeholder when camera is unavailable
 * (web preview / denied permission) — the gallery path still works.
 */

import { useRef, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { CameraView as ExpoCameraView, useCameraPermissions } from "expo-camera";

type Props = {
  onCaptured: (uri: string) => void;
};

export default function CameraView({ onCaptured }: Props) {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<ExpoCameraView>(null);
  const [busy, setBusy] = useState(false);

  if (!permission) {
    return <View style={styles.placeholder} />;
  }

  if (!permission.granted) {
    return (
      <View style={[styles.placeholder, styles.placeholderContent]}>
        <Text style={styles.placeholderTitle}>Camera permission needed</Text>
        <Text style={styles.placeholderText}>
          Used to photograph onion batches. You can also pick an image from the
          gallery below.
        </Text>
        <Pressable style={styles.button} onPress={requestPermission}>
          <Text style={styles.buttonText}>Grant camera access</Text>
        </Pressable>
        <View style={styles.viewfinderMock}>
          <Text style={styles.mockText}>[ CAMERA VIEWFINDER PLACEHOLDER ]</Text>
        </View>
      </View>
    );
  }

  const capture = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const photo = await cameraRef.current?.takePictureAsync({ quality: 0.7 });
      if (photo?.uri) onCaptured(photo.uri);
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={styles.container}>
      <ExpoCameraView ref={cameraRef} style={styles.camera} facing="back" />
      {/* Viewfinder overlay — TODO(TEAM C): framing rectangle + guides */}
      <View style={styles.viewfinder} />
      <Pressable style={({ pressed }) => [styles.shutter, pressed && { opacity: 0.8 }]} onPress={capture}>
        <Text style={styles.shutterText}>{busy ? "…" : "Capture"}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  camera: { flex: 1 },
  viewfinder: {
    position: "absolute",
    top: "12%",
    left: "10%",
    right: "10%",
    height: "45%",
    borderWidth: 2,
    borderColor: "rgba(255,255,255,0.65)",
    borderRadius: 16,
  },
  shutter: {
    position: "absolute",
    bottom: 28,
    alignSelf: "center",
    backgroundColor: "#16A34A",
    width: 130,
    paddingVertical: 16,
    borderRadius: 999,
    alignItems: "center",
  },
  shutterText: { color: "#fff", fontWeight: "800", fontSize: 16 },
  placeholder: { flex: 1, backgroundColor: "#1F2937" },
  placeholderContent: { alignItems: "center", justifyContent: "center", padding: 24 },
  placeholderTitle: { color: "#F9FAFB", fontSize: 16, fontWeight: "700" },
  placeholderText: { color: "#9CA3AF", fontSize: 12, textAlign: "center", marginTop: 8 },
  button: {
    backgroundColor: "#16A34A",
    borderRadius: 10,
    paddingHorizontal: 20,
    paddingVertical: 12,
    marginTop: 16,
  },
  buttonText: { color: "#fff", fontWeight: "700" },
  viewfinderMock: {
    marginTop: 24,
    borderWidth: 1,
    borderColor: "#374151",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 40,
  },
  mockText: { color: "#6B7280", fontSize: 11, textAlign: "center" },
});
