# DEMO SCRIPT — presentation on 11 September 2026

Total: ~6 minutes + 2 min Q&A. Golden rule: **always say "DEMO MODE" when
results are synthetic.**

## Pre-demo checklist (night before + 30 min before)

- [ ] `docker compose up` (or local uvicorn) running; `/api/health` → `database: connected`
- [ ] `.env` copied from `.env.example`; `DEMO_MODE=true`
- [ ] Phone with Expo Go on venue Wi-Fi, `EXPO_PUBLIC_API_URL` set to laptop IP
- [ ] Offline fallback rehearsed: mobile MOCK mode (backend fully off)
- [ ] Sample photos ready: `docs/demo/sample_images/`
- [ ] Slide: architecture diagram from `ARCHITECTURE.md`

## Run of show

| # | Time | Beat | Detail |
|---|------|------|--------|
| 1 | 0:00–0:45 | Problem | post-harvest onion losses; manual grading is slow, inconsistent, contested |
| 2 | 0:45–1:30 | Solution | phone photo → AI grading → PDF report; show architecture slide |
| 3 | 1:30–2:15 | Live: health | `curl /api/health` — show honest `database` + `demo_mode` fields |
| 4 | 2:15–4:00 | Live: mobile | Home → New Batch → Camera (photo of onions) → Analyzing → Results: walk through grade, quality score, counts, defect %, URS %, confidence, reasons |
| 5 | 4:00–4:45 | Report | tap View Report → PDF with DEMO watermark; explain why watermark exists (integrity!) |
| 6 | 4:45–5:30 | Engineering | contract-first modular design: ML gateway swapped from DEMO→YOLO with zero app changes; grading thresholds in config; 37 tests |
| 7 | 5:30–6:00 | Roadmap | dataset→train plan, verified official thresholds, multi-image batches |

## Likely Q&A

* *"Is the AI real today?"* → Pipeline is real end-to-end; the detector currently
  runs in DEMO MODE returning deterministic synthetic data, clearly flagged.
  The YOLO11n training path is scaffolded; weights come as soon as the
  annotated dataset is in.
* *"What is URS?"* → Configurable metric, default interpretation
  (undersized+rotten+sprouted)/total; definition being verified against the
  applicable standard — deliberately not hard-coded.
* *"Why not fake accuracy numbers?"* → Judging integrity + the demo banner
  shows we know exactly what is real.
* *"What if internet dies?"* → Full offline fallback: mobile MOCK mode +
  local backend; nothing on stage depends on cloud.

## Fallback ladder

1. Primary: phone + backend over venue Wi-Fi.
2. Backend local on laptop, phone via hotspot.
3. Backend off → mobile pure MOCK mode (still demonstrates the full flow).
4. Worst case: screen recording of the flow + `sample_analysis.json`.
