/**
 * Onion Quality AI — Redesigned Frontend
 * Theme: Dark Mode Glassmorphism · Amber-Gold Onion Accent · Emerald Health
 */

export const colors = {
  // Brand (Amber-Gold Onion Accent)
  primary: "#f59e0b", // brand-400
  primarySoft: "#fef3c7", // brand-100
  brand950: "#1a0e00",
  brand900: "#3d2000",
  brand800: "#6b3800",
  brand700: "#92400e",
  brand600: "#b45309",
  brand500: "#d97706",
  brand400: "#f59e0b",
  brand300: "#fbbf24",
  brand200: "#fde68a",
  brand100: "#fef3c7",
  brand50:  "#fffbeb",

  // Health (Emerald)
  health700: "#065f46",
  health600: "#059669",
  health500: "#10b981",
  health400: "#34d399",
  health200: "#a7f3d0",
  health100: "#d1fae5",
  
  accent: "#10b981", // Using health-500 for positive accents
  amber: "#f59e0b", 
  amberSoft: "rgba(245, 158, 11, 0.12)",
  red: "#ef4444", 
  redSoft: "rgba(239, 68, 68, 0.12)",
  purple: "#a78bfa",
  purpleSoft: "rgba(167, 139, 250, 0.12)",
  blue: "#60a5fa",
  blueSoft: "rgba(96, 165, 250, 0.12)",

  // Backgrounds
  bg: "#0d0f14", // bg-base
  surface: "#141720", // bg-surface
  raised: "#1c2030", // bg-raised
  card: "rgba(28, 32, 48, 0.75)",

  // Text
  ink: "#f1f5f9", // text-primary
  inkMuted: "#94a3b8", // text-secondary
  inkSubtle: "#64748b", // text-muted
  line: "rgba(255, 255, 255, 0.06)", // border-dim

  // Grade badge colors
  grade: {
    A: "#10b981",
    B: "#60a5fa",
    C: "#f59e0b",
    D: "#ef4444",
  },

  // Category defect colors
  category: {
    healthy: "#10b981",
    damaged: "#f59e0b",
    rotten: "#ef4444",
    sprouted: "#a78bfa",
    undersized: "#60a5fa",
  },
};

export const glass = {
  bg: "rgba(255, 255, 255, 0.04)",
  bgHover: "rgba(255, 255, 255, 0.07)",
};

export const borders = {
  dim: "rgba(255, 255, 255, 0.06)",
  subtle: "rgba(255, 255, 255, 0.10)",
  accent: "rgba(245, 158, 11, 0.35)",
  health: "rgba(16, 185, 129, 0.35)",
};

export const typography = {
  display: { fontFamily: "Inter_800ExtraBold", fontSize: 32, lineHeight: 38 },
  title1: { fontFamily: "Inter_700Bold", fontSize: 24, lineHeight: 30 },
  title2: { fontFamily: "Inter_700Bold", fontSize: 18, lineHeight: 24 },
  headline: { fontFamily: "Inter_600SemiBold", fontSize: 15, lineHeight: 20 },
  body: { fontFamily: "Inter_400Regular", fontSize: 14, lineHeight: 20 },
  bodyMedium: { fontFamily: "Inter_500Medium", fontSize: 14, lineHeight: 20 },
  caption: { fontFamily: "Inter_400Regular", fontSize: 12, lineHeight: 16 },
  micro: { fontFamily: "Inter_700Bold", fontSize: 10, letterSpacing: 0.5, lineHeight: 14 },
  mono: { fontFamily: "DMMono_500Medium", fontSize: 14, lineHeight: 20 },
};

export const radius = {
  XS: 6,
  S: 10,
  M: 14,
  L: 20,
  XL: 26,
  XXL: 32,
  pill: 9999,
};

export const shadows = {
  sm: {
    shadowColor: "#000",
    shadowOpacity: 0.4,
    shadowRadius: 3,
    shadowOffset: { width: 0, height: 1 },
    elevation: 2,
  },
  md: {
    shadowColor: "#000",
    shadowOpacity: 0.45,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
  lg: {
    shadowColor: "#000",
    shadowOpacity: 0.55,
    shadowRadius: 40,
    shadowOffset: { width: 0, height: 12 },
    elevation: 8,
  },
  xl: {
    shadowColor: "#000",
    shadowOpacity: 0.65,
    shadowRadius: 64,
    shadowOffset: { width: 0, height: 24 },
    elevation: 12,
  },
};

export const glows = {
  brand: {
    shadowColor: "rgba(245, 158, 11, 0.18)",
    shadowOpacity: 1,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 0 },
    elevation: 8,
  },
  health: {
    shadowColor: "rgba(16, 185, 129, 0.18)",
    shadowOpacity: 1,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 0 },
    elevation: 8,
  },
  danger: {
    shadowColor: "rgba(239, 68, 68, 0.18)",
    shadowOpacity: 1,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 0 },
    elevation: 8,
  },
};

export const layout = {
  maxWebWidth: 480,
};
