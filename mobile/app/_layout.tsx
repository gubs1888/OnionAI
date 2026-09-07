/**
 * Root layout — navigation flow (contract with the whole team):
 *
 *   HOME -> NEW BATCH -> CAMERA/UPLOAD -> ANALYZING -> RESULTS -> REPORT
 */

import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";

const HEADER_BG = "#14532D"; // deep onion green

export default function RootLayout() {
  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: HEADER_BG },
          headerTintColor: "#FFFFFF",
          headerTitleStyle: { fontWeight: "700" },
          contentStyle: { backgroundColor: "#F6F5EF" },
        }}
      >
        <Stack.Screen name="index" options={{ title: "Onion Quality AI" }} />
        <Stack.Screen name="batch" options={{ title: "New Batch" }} />
        <Stack.Screen name="camera" options={{ title: "Camera / Upload" }} />
        <Stack.Screen
          name="analyzing"
          options={{ title: "Analyzing", gestureEnabled: false }}
        />
        <Stack.Screen name="results" options={{ title: "Results" }} />
        <Stack.Screen name="report" options={{ title: "Report" }} />
      </Stack>
    </>
  );
}
