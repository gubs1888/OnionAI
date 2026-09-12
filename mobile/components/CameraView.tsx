import React, { useRef, useState } from "react";
import { Platform, Pressable, StyleSheet, Text, View } from "react-native";
import { CameraView as ExpoCameraView, useCameraPermissions } from "expo-camera";
import * as ImagePicker from "expo-image-picker";
import { colors, radius, typography } from "../theme";
import Button from "./ui/Button";
import Card from "./ui/Card";

type Props = {
  onCaptured: (uri: string) => void;
};

export default function CameraView({ onCaptured }: Props) {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<ExpoCameraView>(null);
  const [busy, setBusy] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [permError, setPermError] = useState<string | null>(null);

  const handleGrantPermission = async () => {
    setRequesting(true);
    setPermError(null);
    try {
      if (Platform.OS === "web" && typeof navigator !== "undefined" && navigator.mediaDevices?.getUserMedia) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ video: true });
          // Stop initial test tracks so ExpoCameraView can take over cleanly
          stream.getTracks().forEach((t) => t.stop());
        } catch (webErr) {
          console.warn("Web getUserMedia permission prompt error:", webErr);
        }
      }
      const res = await requestPermission();
      if (!res.granted) {
        setPermError("Camera access denied or blocked by browser settings.");
      }
    } catch (err) {
      setPermError("Could not request camera access. Please check browser site settings.");
    } finally {
      setRequesting(false);
    }
  };

  const pickFromGalleryFallback = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ["images"],
        quality: 0.7,
      });
      if (!result.canceled && result.assets[0]) {
        onCaptured(result.assets[0].uri);
      }
    } catch (err) {
      setPermError("Failed to select image from gallery.");
    }
  };

  if (!permission) {
    return <View style={styles.darkBg} />;
  }

  if (!permission.granted) {
    return (
      <View style={[styles.darkBg, styles.permissionContent]}>
        <Card style={styles.permissionCard}>
          <Text style={styles.permIcon}>📷</Text>
          <Text style={styles.permTitle}>Camera Access Required</Text>
          <Text style={styles.permText}>
            OnionLens needs camera access to capture and grade onion lots in real-time.
          </Text>

          {permError ? (
            <Text style={styles.permErrorText}>
              ⚠️ {permError}{"\n"}
              <Text style={styles.permSubHint}>
                If using desktop browser, click the 🔒 lock icon in the address bar to allow camera access, or upload an image directly.
              </Text>
            </Text>
          ) : null}

          <Button
            label="Grant Camera Access"
            onPress={handleGrantPermission}
            variant="primary"
            loading={requesting}
            style={{ marginTop: 16, width: "100%" }}
          />

          <Button
            label="Pick Photo from Gallery Instead"
            onPress={pickFromGalleryFallback}
            variant="secondary"
            style={{ marginTop: 10, width: "100%" }}
          />
        </Card>
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
      
      {/* Framing Reticle Overlay */}
      <View style={styles.reticleContainer} pointerEvents="none">
        <View style={styles.reticleBox}>
          {/* Corner brackets */}
          <View style={[styles.bracket, styles.topLeft]} />
          <View style={[styles.bracket, styles.topRight]} />
          <View style={[styles.bracket, styles.bottomLeft]} />
          <View style={[styles.bracket, styles.bottomRight]} />
        </View>
        <Text style={styles.guideText}>
          Fill the frame with the onion lot · avoid shadows
        </Text>
      </View>

      {/* Shutter Button */}
      <View style={styles.controlsRow}>
        <Pressable
          style={({ pressed }) => [styles.shutterRing, pressed && styles.shutterPressed]}
          onPress={capture}
          disabled={busy}
        >
          <View style={styles.shutterInner} />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#101619",
    position: "relative",
  },
  camera: {
    flex: 1,
  },
  darkBg: {
    flex: 1,
    backgroundColor: "#101619",
  },
  permissionContent: {
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  permissionCard: {
    alignItems: "center",
    maxWidth: 380,
    width: "100%",
    padding: 20,
  },
  permIcon: {
    fontSize: 40,
    marginBottom: 8,
  },
  permTitle: {
    ...typography.title2,
    color: colors.ink,
    textAlign: "center",
  },
  permText: {
    ...typography.caption,
    color: colors.inkMuted,
    textAlign: "center",
    marginTop: 6,
    lineHeight: 18,
  },
  permErrorText: {
    ...typography.caption,
    color: colors.red,
    textAlign: "center",
    marginTop: 10,
    fontWeight: "600",
  },
  permSubHint: {
    fontWeight: "400",
    color: colors.inkMuted,
    fontSize: 11,
  },
  reticleContainer: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 120,
    alignItems: "center",
    justifyContent: "center",
  },
  reticleBox: {
    width: "80%",
    height: "55%",
    maxWidth: 340,
    maxHeight: 340,
    position: "relative",
  },
  bracket: {
    position: "absolute",
    width: 24,
    height: 24,
    borderColor: "#FFFFFF",
  },
  topLeft: {
    top: 0,
    left: 0,
    borderTopWidth: 3,
    borderLeftWidth: 3,
    borderTopLeftRadius: 10,
  },
  topRight: {
    top: 0,
    right: 0,
    borderTopWidth: 3,
    borderRightWidth: 3,
    borderTopRightRadius: 10,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 3,
    borderLeftWidth: 3,
    borderBottomLeftRadius: 10,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 3,
    borderRightWidth: 3,
    borderBottomRightRadius: 10,
  },
  guideText: {
    ...typography.caption,
    color: "#FFFFFF",
    backgroundColor: "rgba(16, 22, 25, 0.75)",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: radius.pill,
    marginTop: 16,
    overflow: "hidden",
  },
  controlsRow: {
    position: "absolute",
    bottom: 24,
    left: 0,
    right: 0,
    alignItems: "center",
    justifyContent: "center",
  },
  shutterRing: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 4,
    borderColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255, 255, 255, 0.2)",
  },
  shutterPressed: {
    transform: [{ scale: 0.92 }],
    backgroundColor: "rgba(255, 255, 255, 0.4)",
  },
  shutterInner: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: colors.accent,
  },
});
