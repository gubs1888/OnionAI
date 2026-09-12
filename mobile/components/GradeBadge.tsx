import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { colors, radius, typography } from "../theme";
import { Grade } from "../types/assessment";

const GRADE_LABELS: Record<Grade, { label: string; desc: string }> = {
  A: { label: "Grade A", desc: "Premium Quality" },
  B: { label: "Grade B", desc: "Standard Quality" },
  C: { label: "Grade C", desc: "Fair / URS Specs" },
  D: { label: "Grade D", desc: "Below Standard" },
};

export default function GradeBadge({ grade }: { grade: Grade }) {
  const gradeColor = colors.grade[grade] ?? colors.grade.D;
  const info = GRADE_LABELS[grade] ?? GRADE_LABELS.D;

  return (
    <View style={[styles.badge, { backgroundColor: gradeColor }]}>
      <Text style={styles.letter}>{grade}</Text>
      <View style={styles.textCol}>
        <Text style={styles.label}>{info.label}</Text>
        <Text style={styles.desc}>{info.desc}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderRadius: radius.M,
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    shadowColor: colors.ink,
    shadowOpacity: 0.1,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  letter: {
    fontSize: 32,
    fontWeight: "900",
    color: "#FFFFFF",
    lineHeight: 34,
    marginRight: 12,
  },
  textCol: {
    justifyContent: "center",
  },
  label: {
    ...typography.headline,
    color: "#FFFFFF",
    fontWeight: "800",
  },
  desc: {
    ...typography.caption,
    color: "rgba(255, 255, 255, 0.85)",
    fontSize: 11,
  },
});
