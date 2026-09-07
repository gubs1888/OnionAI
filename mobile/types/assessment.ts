/**
 * CONTRACT TYPES — Backend -> Mobile (TEAM C).
 *
 * These mirror `backend/app/schemas/analysis.py` exactly.
 * DO NOT rename fields here without a contract sign-off (docs/api/API_CONTRACT.md).
 */

export type Grade = "A" | "B" | "C" | "D";

/** ML -> Backend -> Mobile detection record. */
export interface Detection {
  class_name: string; // "onion" | "damaged" | "rotten" | "sprouted"
  class_id: number; // 0=onion 1=damaged 2=rotten 3=sprouted
  confidence: number; // 0..1
  bbox: number[]; // [x1, y1, x2, y2] pixels
  estimated_size_mm?: number | null;
}

/** POST /api/analyze and GET /api/batches/{id}/assessment payload. */
export interface Assessment {
  assessment_id: number;
  batch_id: string; // batch CODE, e.g. "ON-0001"
  total_onions: number;
  healthy: number;
  damaged: number;
  rotten: number;
  sprouted: number;
  undersized: number;
  defect_percentage: number;
  quality_score: number; // 0..100 (MVP scoring)
  grade: Grade;
  urs_percentage: number;
  confidence: number; // percent 0..100
  reasons: string[];
  /** TRUE => DEMO DATA — the UI MUST show a demo banner. */
  is_demo: boolean;
  model_version: string;
  created_at: string;
}

/** POST /api/analyze response = Assessment + detection detail. */
export interface AnalysisResponse extends Assessment {
  image_id: number;
  detections: Detection[];
}

/** Batch record. */
export interface Batch {
  id: number;
  batch_code: string;
  name: string;
  variety?: string | null;
  source?: string | null;
  notes?: string | null;
  status: "created" | "analyzing" | "analyzed" | "failed";
  image_count: number;
  created_at: string;
}

/** POST /api/reports/{assessment_id} response. */
export interface ReportInfo {
  report_id: number;
  report_code: string;
  assessment_id: number;
  batch_id: string;
  format: string;
  is_demo: boolean;
  generated_at: string;
  download_url: string;
}

/** Health payload (simplified). */
export interface HealthInfo {
  status: string;
  service: string;
  version: string;
  database: string;
  demo_mode: boolean;
}
