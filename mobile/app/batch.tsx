/**
 * NEW BATCH — minimal creation form.
 * Creates via POST /api/batches (MOCK fallback keeps the flow alive offline),
 * then moves to CAMERA.
 */

import { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";

import { createBatch } from "../services/api";
import { Batch } from "../types/assessment";

export default function NewBatchScreen() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [variety, setVariety] = useState("");
  const [source, setSource] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (!name.trim()) {
      setError("Batch name is required.");
      return;
    }
    setError(null);
    setSubmitting(true);
    const batch: Batch = await createBatch({
      name: name.trim(),
      variety: variety.trim() || undefined,
      source: source.trim() || undefined,
    });
    setSubmitting(false);
    router.replace({
      pathname: "/camera",
      params: { batchCode: batch.batch_code, batchName: batch.name },
    });
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Text style={styles.label}>Batch name *</Text>
      <TextInput
        style={styles.input}
        value={name}
        onChangeText={setName}
        placeholder="e.g. Lot A — Nashik farm"
        placeholderTextColor="#9CA3AF"
      />
      <Text style={styles.label}>Variety</Text>
      <TextInput
        style={styles.input}
        value={variety}
        onChangeText={setVariety}
        placeholder="e.g. Nashik Red"
        placeholderTextColor="#9CA3AF"
      />
      <Text style={styles.label}>Source / mandi / farm</Text>
      <TextInput
        style={styles.input}
        value={source}
        onChangeText={setSource}
        placeholder="e.g. Lasalgaon Mandi"
        placeholderTextColor="#9CA3AF"
      />

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Pressable
        style={({ pressed }) => [styles.button, pressed && { opacity: 0.85 }]}
        onPress={submit}
        disabled={submitting}
      >
        <Text style={styles.buttonText}>
          {submitting ? "Creating…" : "Create batch → Camera"}
        </Text>
      </Pressable>
      <Text style={styles.note}>
        Placeholder form — extra fields (count, photos, GPS) come later.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { padding: 20 },
  label: { fontSize: 13, fontWeight: "600", color: "#374151", marginTop: 14, marginBottom: 6 },
  input: {
    backgroundColor: "#fff",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  error: { color: "#DC2626", marginTop: 12, fontSize: 13 },
  button: {
    backgroundColor: "#16A34A",
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 24,
  },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  note: { marginTop: 16, fontSize: 11, color: "#9CA3AF", textAlign: "center" },
});
