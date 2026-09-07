# Mobile — Onion Quality AI (TEAM C)

React Native + Expo (SDK 53) + TypeScript + expo-router.

## Run

```bash
cd mobile
npm install
npx expo start          # press a = Android, i = iOS simulator, w = web
```

Point the app at your backend with an env var (see root `.env.example`):

```bash
# Android emulator:
EXPO_PUBLIC_API_URL=http://10.0.2.2:8000 npx expo start
# Physical device (same Wi-Fi) or tunnel:
EXPO_PUBLIC_API_URL=http://<YOUR-LAN-IP>:8000 npx expo start --tunnel
```

DEMO-FIRST: with no backend reachable, every screen falls back to clearly
marked MOCK data so the full flow is always demoable.

## Navigation flow (already wired)

```
HOME (/)  ->  NEW BATCH (/batch)  ->  CAMERA (/camera)  ->  ANALYZING (/analyzing)
          ->  RESULTS (/results)  ->  REPORT (/report)
```

## Layout

```
app/           expo-router screens (one file per step of the flow)
components/    CameraView, BatchCard, ResultCard, GradeBadge, DefectChart
services/api.ts   THE ONLY file that talks to the backend (+ MOCK fallbacks)
types/assessment.ts  Backend->Mobile contract types (mirror of backend schemas)
```

## Rules

* `types/assessment.ts` mirrors `backend/app/schemas/analysis.py`. Field renames
  need a contract sign-off (see docs/api/API_CONTRACT.md).
* All backend access goes through `services/api.ts` — screens never call fetch.
* Mock/demo results must ALWAYS surface `is_demo` as a visible banner.
* Keep screens plain until the flow is stable; beauty pass comes later.

## Smoke test

```bash
npm run smoke     # TypeScript strict typecheck (the MVP smoke test)
```

Jest + jest-expo render tests are a planned TEAM C task (see `__tests__/`).

## Camera note

`CameraView` uses expo-camera SDK 53 (`CameraView` + `useCameraPermissions`).
It degrades to a labeled placeholder when permissions are denied or on web —
the gallery path (expo-image-picker) always works.
