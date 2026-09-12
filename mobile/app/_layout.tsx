import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { colors, typography } from "../theme";
import { useFonts, Inter_400Regular, Inter_500Medium, Inter_600SemiBold, Inter_700Bold, Inter_800ExtraBold } from "@expo-google-fonts/inter";
import { DMMono_500Medium } from "@expo-google-fonts/dm-mono";
import * as SplashScreen from 'expo-splash-screen';
import { useEffect } from 'react';
import { BlurView } from 'expo-blur';
import { StyleSheet, View } from 'react-native';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
    Inter_700Bold,
    Inter_800ExtraBold,
    DMMono_500Medium,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded, fontError]);

  if (!fontsLoaded && !fontError) {
    return null;
  }

  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: 'transparent' },
          headerTintColor: colors.ink,
          headerTitleStyle: { fontFamily: typography.headline.fontFamily, fontSize: typography.headline.fontSize },
          headerShadowVisible: false,
          contentStyle: { backgroundColor: colors.bg },
          headerTransparent: true,
          headerBackground: () => (
            <BlurView tint="dark" intensity={80} style={StyleSheet.absoluteFill} />
          ),
        }}
      >
        <Stack.Screen name="index" options={{ title: "Onion Quality AI", headerTransparent: false, headerBackground: () => <View style={[StyleSheet.absoluteFill, { backgroundColor: colors.bg }]} /> }} />
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
