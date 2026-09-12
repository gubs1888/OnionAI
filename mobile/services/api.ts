/**
 * API CLIENT (TEAM C) — the ONLY place the mobile app talks to the backend.
 *
 * DEMO-FIRST behavior:
 *   Every call falls back to clearly-marked MOCK data when the backend is
 *   unreachable, so the full navigation flow works during development and on
 *   stage without a server. Mock results are flagged `is_demo: true` and
 *   logged — we NEVER present them as real AI output.
 */

import { Platform } from "react-native";
import * as FileSystem from "expo-file-system/legacy";
import {
  AnalysisResponse,
  Assessment,
  Batch,
  Grade,
  HealthInfo,
  ReportInfo,
} from "../types/assessment";

// EXPO_PUBLIC_* env vars are inlined at start time (see .env.example).
export const API_BASE_URL: string =
  process.env.EXPO_PUBLIC_API_URL ??
  (typeof window !== "undefined"
    ? (["8081", "8082", "19006"].includes(window.location.port)
        ? `${window.location.protocol}//${window.location.hostname}:8000`
        : window.location.origin)
    : "http://localhost:8000");

const TIMEOUT_MS = 15_000;

// ---------------------------------------------------------------------------
// [MOCK DATA] — used ONLY when the backend cannot be reached.
// ---------------------------------------------------------------------------

function mockNow(): string {
  return new Date().toISOString();
}

function buildMockAssessment(batchCode: string): Assessment {
  // Simple deterministic-ish mock: fresh numbers per call, honest buckets.
  const total = 30 + Math.floor(Math.random() * 25);
  const damaged = Math.floor(Math.random() * 4);
  const rotten = Math.floor(Math.random() * 3);
  const sprouted = Math.floor(Math.random() * 3);
  const undersized = Math.floor(Math.random() * 3);
  const healthy = total - damaged - rotten - sprouted - undersized;
  const defectPct = ((total - healthy) / total) * 100;
  const score = Math.max(0, Math.min(100, 100 - defectPct * 0.85));
  const grade: Grade = score >= 80 ? "A" : score >= 60 ? "B" : score >= 40 ? "C" : "D";
  return {
    assessment_id: 0,
    batch_id: batchCode,
    total_onions: total,
    healthy,
    damaged,
    rotten,
    sprouted,
    undersized,
    defect_percentage: Math.round(defectPct * 100) / 100,
    quality_score: Math.round(score * 10) / 10,
    grade,
    urs_percentage: Math.round(((undersized + rotten + sprouted) / total) * 1000) / 10,
    confidence: Math.round((80 + Math.random() * 15) * 10) / 10,
    reasons: ["MOCK DATA — backend unreachable. Start the backend for real analysis."],
    is_demo: true,
    model_version: "mock-v0",
    created_at: mockNow(),
  };
}

const MOCK_BATCHES: Batch[] = [
  {
    id: 0,
    batch_code: "DEMO-001",
    name: "Demo batch (no backend)",
    variety: "Nashik Red",
    source: "Local storage",
    notes: null,
    status: "analyzed",
    image_count: 1,
    created_at: mockNow(),
  },
];

/** In-memory handoff between analyze -> results screens (mock flow only). */
let lastAssessment: Assessment | null = null;

// ---------------------------------------------------------------------------
// Core request helper
// ---------------------------------------------------------------------------

/** Error from the backend (server was reachable but returned a non-2xx). */
export class ApiError extends Error {
  code: string;
  status: number;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

/** True network failure — backend unreachable, timeout, DNS, etc. */
export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NetworkError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, { ...init, signal: controller.signal });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      const code = body?.detail?.code ?? body?.error?.code ?? "UNKNOWN";
      const message =
        body?.detail?.message ?? body?.error?.message ?? `HTTP ${res.status}`;
      throw new ApiError(res.status, code, message);
    }
    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof ApiError) throw err; // re-throw server errors as-is
    // Everything else is a network-level failure
    throw new NetworkError((err as Error).message ?? "Network request failed");
  } finally {
    clearTimeout(timer);
  }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/** GET /api/health — null when the backend is unreachable. */
export async function healthCheck(): Promise<HealthInfo | null> {
  try {
    return await request<HealthInfo>("/api/health");
  } catch {
    return null;
  }
}

/** POST /api/batches */
export async function createBatch(input: {
  name: string;
  variety?: string;
  source?: string;
  notes?: string;
}): Promise<Batch> {
  try {
    return await request<Batch>("/api/batches", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
  } catch (err) {
    console.warn("[api] createBatch failed — MOCK fallback:", (err as Error).message);
    return {
      id: 0,
      batch_code: "DEMO-001",
      name: input.name,
      variety: input.variety ?? null,
      source: input.source ?? null,
      notes: input.notes ?? null,
      status: "created",
      image_count: 0,
      created_at: mockNow(),
    };
  }
}

/** GET /api/batches */
export async function listBatches(): Promise<Batch[]> {
  try {
    return await request<Batch[]>("/api/batches");
  } catch (err) {
    console.warn("[api] listBatches failed — MOCK fallback:", (err as Error).message);
    return MOCK_BATCHES;
  }
}

/** DELETE /api/batches */
export async function clearBatches(): Promise<void> {
  try {
    await request("/api/batches", { method: "DELETE" });
  } catch (err) {
    console.warn("[api] clearBatches failed:", (err as Error).message);
  }
}

/**
 * POST /api/analyze — multipart upload.
 * Falls back to MOCK only when the backend is unreachable (NetworkError).
 */
export async function analyzeImage(imageUri: string, batchCode?: string, distanceCm?: number): Promise<AnalysisResponse> {
  try {
    if (Platform.OS === "web") {
      const form = new FormData();
      const resp = await fetch(imageUri);
      const blob = await resp.blob();
      form.append("image", blob, "onions.jpg");
      if (batchCode) form.append("batch_id", batchCode);
      if (distanceCm) form.append("distance_cm", distanceCm.toString());
      
      const result = await request<AnalysisResponse>("/api/analyze", {
        method: "POST",
        body: form,
      });
      lastAssessment = result;
      return result;
    } else {
      // React Native mobile MUST use expo-file-system for local file uploads
      const formParams: Record<string, string> = {};
      if (batchCode) formParams["batch_id"] = batchCode;
      if (distanceCm) formParams["distance_cm"] = distanceCm.toString();

      const fullUrl = `${API_BASE_URL}/api/analyze`;

      const uploadResult = await FileSystem.uploadAsync(fullUrl, imageUri, {
        fieldName: "image",
        httpMethod: "POST",
        uploadType: FileSystem.FileSystemUploadType.MULTIPART,
        parameters: formParams,
      });

      if (uploadResult.status >= 400) {
        let body: any = null;
        try {
          body = JSON.parse(uploadResult.body);
        } catch {}
        const code = body?.detail?.code ?? body?.error?.code ?? "UNKNOWN";
        const message = body?.detail?.message ?? body?.error?.message ?? `HTTP ${uploadResult.status}`;
        throw new ApiError(uploadResult.status, code, message);
      }

      const result = JSON.parse(uploadResult.body) as AnalysisResponse;
      lastAssessment = result;
      return result;
    }
  } catch (err) {
    // Server returned a real error (e.g. 422 NOTHING_DETECTED) — propagate it
    if (err instanceof ApiError) {
      console.warn("[api] analyzeImage server error:", err.code, err.message);
      throw err;
    }
    // Backend truly unreachable — MOCK fallback
    console.warn("[api] analyzeImage network error — MOCK fallback:", (err as Error).message);
    const mock = {
      ...buildMockAssessment(batchCode ?? "DEMO-001"),
      image_id: 0,
      detections: [],
    };
    lastAssessment = mock;
    return mock;
  }
}

/**
 * GET /api/batches/{batchCode}/assessment — prefers the in-memory result of
 * the just-finished analysis, then the backend, then MOCK.
 */
export async function getAssessment(batchCode: string): Promise<Assessment> {
  if (lastAssessment && lastAssessment.batch_id === batchCode) {
    return lastAssessment;
  }
  try {
    return await request<Assessment>(`/api/batches/${encodeURIComponent(batchCode)}/assessment`);
  } catch (err) {
    console.warn("[api] getAssessment failed — MOCK fallback:", (err as Error).message);
    return lastAssessment ?? buildMockAssessment(batchCode);
  }
}

/** POST /api/reports/{assessmentId} */
export async function generateReport(assessmentId: number): Promise<ReportInfo> {
  try {
    return await request<ReportInfo>(`/api/reports/${assessmentId}`, { method: "POST" });
  } catch (err) {
    console.warn("[api] generateReport failed — MOCK fallback:", (err as Error).message);
    return {
      report_id: 0,
      report_code: `MOCK-RPT-${assessmentId}`,
      assessment_id: assessmentId,
      batch_id: lastAssessment?.batch_id ?? "DEMO-001",
      format: "pdf",
      is_demo: true,
      generated_at: mockNow(),
      download_url: `/api/reports/${assessmentId}/download`,
    };
  }
}

/** Absolute URL for a backend-relative path (report download, uploaded images). */
export function absoluteUrl(path: string): string {
  return path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
}
