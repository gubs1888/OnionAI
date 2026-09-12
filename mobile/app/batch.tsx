import React, { useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";

import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import { createBatch } from "../services/api";
import { colors, layout, radius, typography } from "../theme";
import { Batch } from "../types/assessment";

export default function NewBatchScreen() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [variety, setVariety] = useState("");
  const [source, setSource] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [focusedField, setFocusedField] = useState<string | null>(null);

  const isFormValid = name.trim().length > 0;

  const submit = async () => {
    if (!name.trim()) {
      setError("Batch name is required.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const batch: Batch = await createBatch({
        name: name.trim(),
        variety: variety.trim() || undefined,
        source: source.trim() || undefined,
      });
      router.replace({
        pathname: "/camera",
        params: { batchCode: batch.batch_code, batchName: batch.name },
      });
    } catch (err) {
      setError((err as Error).message ?? "Could not create batch");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.webWrapper}>
        {/* Screen Header */}
        <View style={styles.headerBlock}>
          <Text style={styles.title}>New grading batch</Text>
          <Text style={styles.subtitle}>
            Name your lot — you'll capture or select photos in the next step.
          </Text>
        </View>

        {/* Elevated Form Container */}
        <Card style={styles.formCard}>
          {/* Name Field */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>
              Batch name <Text style={styles.required}>*</Text>
            </Text>
            <TextInput
              style={[
                styles.input,
                focusedField === "name" && styles.inputFocused,
                error && !name.trim() && styles.inputError,
              ]}
              value={name}
              onChangeText={(val) => {
                setName(val);
                if (error) setError(null);
              }}
              onFocus={() => setFocusedField("name")}
              onBlur={() => setFocusedField(null)}
              placeholder="e.g. Lot A — Nashik Red harvest"
              placeholderTextColor={colors.inkMuted}
            />
            <Text style={styles.fieldHelper}>
              Identify the farm lot or warehouse section
            </Text>
          </View>

          {/* Variety Field */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Onion Variety</Text>
            <TextInput
              style={[
                styles.input,
                focusedField === "variety" && styles.inputFocused,
              ]}
              value={variety}
              onChangeText={setVariety}
              onFocus={() => setFocusedField("variety")}
              onBlur={() => setFocusedField(null)}
              placeholder="e.g. Nashik Red, Agrifound Dark Red"
              placeholderTextColor={colors.inkMuted}
            />
            <Text style={styles.fieldHelper}>Optional cultivars classification</Text>
          </View>

          {/* Source / Mandi Field */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Source / Mandi / Farm</Text>
            <TextInput
              style={[
                styles.input,
                focusedField === "source" && styles.inputFocused,
              ]}
              value={source}
              onChangeText={setSource}
              onFocus={() => setFocusedField("source")}
              onBlur={() => setFocusedField(null)}
              placeholder="e.g. Lasalgaon Mandi, Procurement Center 4"
              placeholderTextColor={colors.inkMuted}
            />
            <Text style={styles.fieldHelper}>Origin location for report records</Text>
          </View>

          {error ? <Text style={styles.errorText}>{error}</Text> : null}
        </Card>

        {/* Submit Action */}
        <Button
          label="Continue to camera →"
          onPress={submit}
          variant="primary"
          size="lg"
          disabled={!isFormValid}
          loading={submitting}
          style={{ marginTop: 24 }}
        />

        <Text style={styles.footerNote}>
          Photos stay on your device until you analyze.
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
  headerBlock: {
    marginVertical: 16,
  },
  title: {
    ...typography.title1,
    color: colors.ink,
  },
  subtitle: {
    ...typography.caption,
    color: colors.inkMuted,
    marginTop: 4,
    fontSize: 13,
  },
  formCard: {
    padding: 20,
    marginTop: 8,
  },
  fieldGroup: {
    marginBottom: 18,
  },
  label: {
    ...typography.headline,
    color: colors.ink,
    fontSize: 14,
    marginBottom: 6,
  },
  required: {
    color: colors.red,
  },
  input: {
    height: 52,
    backgroundColor: colors.surface,
    borderRadius: radius.S,
    paddingHorizontal: 16,
    fontSize: 15,
    borderWidth: 1,
    borderColor: colors.line,
    color: colors.ink,
  },
  inputFocused: {
    borderColor: colors.accent,
    borderWidth: 2,
    backgroundColor: "rgba(16, 185, 129, 0.05)",
  },
  inputError: {
    borderColor: colors.red,
    borderWidth: 1.5,
  },
  fieldHelper: {
    ...typography.caption,
    color: colors.inkMuted,
    marginTop: 4,
    fontSize: 11,
  },
  errorText: {
    ...typography.caption,
    color: colors.red,
    fontWeight: "600",
    marginTop: 8,
  },
  footerNote: {
    ...typography.caption,
    color: colors.inkMuted,
    textAlign: "center",
    marginTop: 16,
    fontSize: 12,
  },
});
