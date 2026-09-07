# NEXT STEPS — Sprint Plan to the 11 September Demo

Written: 7 September 2026 (foundation v0.1.0 complete, 37 tests green)
Demo: **Friday 11 September 2026** → **4 working days left.**
Read this once as a team, then work your column. Update statuses in your
daily standup — do not silently re-scope.

---

## 1. Situation

| What | State |
|---|---|
| Repository | modular skeleton, all 4 team areas scaffolded, `main`/`develop`/4 feature branches |
| Backend | 9 endpoints live, DB auto-init, grading+URS config-driven, PDF reports — **works today** |
| Mobile | full flow Home→Batch→Camera→Analyzing→Results→Report — **works today** (MOCK fallback offline) |
| ML | interface + training/eval scripts ready, **no trained model yet** → DEMO MODE |
| Standards | URS + grade thresholds **NOT verified** → MVP heuristics only, disclaimers on |

**The single biggest risk to the demo is the model. Everything else is polish.**

## 2. Strategy: two tracks, one gate

```
TRACK 1 (guaranteed):  DEMO MODE end-to-end, rehearsed, honest labeling.
                       This IS the demo. It works right now.
TRACK 2 (stretch):     Real YOLO11n on real data, swapped in behind
                       DEMO_MODE=false. Ships only if it passes the gate.

GO/NO-GO GATE — evening of 9 September:
   GO   → val mAP50 ≥ 0.6 on `onion` class + stable end-to-end run
          with DEMO_MODE=false on a real photo.
   NO-GO→ demo stays in DEMO MODE. Zero shame: the architecture story
          ("swap one file, nothing else changes") is itself a selling point.
```

Rules for the sprint:
1. Track 1 must never regress. Any commit that breaks the demo flow is reverted first, fixed later.
2. Track 2 work happens on `feature/ml` + a `feature/backend-model-swap` branch — **never** on develop directly.
3. **Contract freeze: end of 8 September.** After that, no field/endpoint renames of any kind — only additions.

## 3. Day-by-day plan

### Day 0 — TODAY, 7 Sep (remaining hours) — "Everyone shipping"
| Team | Task | Pri |
|---|---|---|
| All | Push repo to GitHub (private). Protect `main` (PRs only). Replace CODEOWNERS `@handles` with real usernames. | **P0** |
| All | `scripts/setup.sh` on each laptop → `python -m pytest` → 37 green → `npx expo start` opens the app. Nobody sleeps with a broken clone. | **P0** |
| A+D | **Start photo collection tonight** (300–500 target for 8 Sep evening). Use `docs/dataset/DATASET_GUIDE.md` checklist. Defect-class photos are the bottleneck — start with damaged/rotten/sprouted sources. | **P0** |
| A | Pick annotation tool (Roboflow recommended — free, YOLO export), create the project + 4 classes, annotate the first 30 images as the calibration batch. | **P0** |
| B | JWT enforcement: `POST /api/batches` + `POST /api/analyze` require a valid bearer token (keep `GET /health` + `GET /batches` open). Update mobile api client to attach it. | **P0** |
| B | Alembic init into `app/db/migrations/` with a baseline migration; verify `alembic upgrade head` on an empty Postgres. | P1 |
| C | Run the app on a real phone against the real backend (set `EXPO_PUBLIC_API_URL` to laptop LAN IP). Fix every connection issue TODAY — this is the classic demo-day failure. | **P0** |
| C | Home screen shows real batches from `GET /api/batches` (remove reliance on MOCK when backend is up). | P1 |
| D | Standards verification kickoff (`docs/standards/STANDARDS_TO_VERIFY.md`): find + quote the exact URS definition and grade/size framework from PS 26031 and the applicable official source. Written verdict due 8 Sep EOD. | **P0** |
| D | API smoke-test script `scripts/api_smoke.sh` (curl all 9 endpoints, assert codes). | P1 |
| All | Agree daily rhythm: **09:30 standup (15 min) · 20:00 integration check on `develop`.** | **P0** |

### Day 1 — 8 Sep — "Data + contracts lock"
| Team | Task | Pri |
|---|---|---|
| A | Annotation sprint to ≥300 labeled images; split train/val by photo session (80/20); first `python ml/train.py` run overnight (cloud/GPU or best laptop). | **P0** |
| A | Record dataset stats (images/class) in `docs/dataset/DATASET_STATS.md` — needed for the presentation slide. | P1 |
| B | Alembic done; `PATCH /api/batches/{id}` (rename/close); fix anything the QA script found; detection bbox draw data double-checked against contract. | **P0** |
| C | Results screen: draw detection bboxes over the analyzed photo (simple absolutely-positioned Views — data already in the response). | P1 |
| C | jest-expo installed; first 2 render tests (Home shows "New Batch", Results shows all contract fields from mock). | P2 |
| D | **Deliver standards verdict** → pair with B to move verified values into `grading_config.json → official_standards_TO_VERIFY` and (only if confident) flip active thresholds. Update report wording. | **P0** |
| D | Dataset collection continues (target 450+); run `scripts/api_smoke.sh` in CI or locally after every develop merge. | **P0** |
| All | 20:00: contract freeze goes into effect. Tag `contract-v1` on develop. | **P0** |

### Day 2 — 9 Sep — "GO/NO-GO + first full rehearsal"
| Team | Task | Pri |
|---|---|---|
| A | Morning: evaluate overnight model (`python ml/evaluate.py`), error analysis on worst images; fine-tune or fix labels; retrain by afternoon. | **P0** |
| A+B | **Gate review at 18:00.** If GO: execute the Model Swap Procedure (§4) on the swap branch, run the full API flow with `DEMO_MODE=false`, compare results sanity. | **P0** |
| B | Report v2: batch metadata + detection summary table in PDF; verify 501/503 paths; reset-DB procedure documented in DEVELOPMENT.md. | P1 |
| C | Airplane-mode drill: full flow with backend OFF (MOCK fallback) — must pass. Loading/error states on every screen. UI polish pass (spacing, colors) — no rewrites. | **P0** |
| D | **Dry-run #1** of `docs/demo/DEMO_SCRIPT.md` with all teams, timed. Record backup screen video (phone + backend flow) as fallback asset #4. | **P0** |
| D | Presentation deck v1 (use ARCHITECTURE.md diagram; status table from README). | **P0** |

### Day 3 — 10 Sep — "Freeze + rehearse on real hardware"
| Team | Task | Pri |
|---|---|---|
| All | **Feature freeze 12:00.** After that only P0 bug fixes, reviewed by the architect. | **P0** |
| All | Full rehearsal ×2 on the actual demo laptop + phone, including venue-like network. Time the run (<6 min). Fix everything that wobbled. | **P0** |
| A | If GO: final weights packaged at `ml/models/onion_yolo.pt` + `eval_report.json` numbers for the slide. If NO-GO: verify demo mode on all 5 sample images; prepare the "swap story" slide. | **P0** |
| B | Seed script `scripts/seed_demo_data.py` (2 batches + assessments) for a populated-looking app at showtime; DB reset rehearsal (drop → compose up → seed → healthy). | **P0** |
| C | Demo phone: app installed, logged-in state cached, Expo Go updated, background apps killed, charger packed. | **P0** |
| D | Deck final + printed demo script + Q&A prep (use DEMO_SCRIPT.md §Q&A). Merge `develop → main`, tag **`v0.1-demo`**. | **P0** |

### Day 4 — 11 Sep — Demo day
| Time | Task |
|---|---|
| −3 h | Full system check on-site: `docker compose up` → health → seed → app connects. Run the demo once end-to-end. |
| −30 min | Pre-demo checklist in `docs/demo/DEMO_SCRIPT.md` (all boxes). Phone on hotspot if venue Wi-Fi is suspect. |
| 0:00–6:00 | Execute the run of show. Say "DEMO MODE" whenever results are synthetic. |
| After | Note judge feedback for the post-event repo retro. |

## 4. Model Swap Procedure (TEAM A + B — the money path)

1. Train → `ml/models/onion_yolo.pt` exists, `eval_report.json` written.
2. Branch `feature/backend-model-swap` from `develop`.
3. `pip install -r ml/requirements.txt` **in the backend venv** (or a unified venv).
4. `.env`: `DEMO_MODE=false`, `MODEL_PATH=./ml/models/onion_yolo.pt`.
5. Verify class names in the trained model match the contract
   (`onion/damaged/rotten/sprouted`, ids 0–3) — `model.names` check.
6. `python -m pytest backend/tests` — note: tests force `DEMO_MODE=true`,
   they must stay green untouched. Manual-verify real mode with:
   `curl -F image=@docs/demo/sample_images/sample_onions_01.jpg .../api/analyze`
   → response has `is_demo: false`, plausible counts.
7. Mobile run with banner absent (`is_demo=false` hides the DEMO banner automatically).
8. PR → review by B + A → merge to develop only after 2 clean end-to-end runs.

Rollback = flip `DEMO_MODE=true` in `.env` and restart. **Practice the rollback once.**

## 5. Standards verification procedure (TEAM D)

1. Re-read PS 26031; quote every quality/grade/URS-adjacent phrase verbatim.
2. Identify the applicable official framework for onion grading in India and its current version; record document + section + year in `STANDARDS_TO_VERIFY.md`.
3. Extract: URS definition/formula · grade boundaries & names · size categories (mm) · any mandatory defect limits.
4. Architect sign-off → values into `grading_config.json` (kept in `official_standards_TO_VERIFY` until whole team agrees) → flip active config → regenerate a sample report → update deck wording.
5. If NOT verifiable in time: keep all disclaimers, present as *"MVP scoring, being aligned with the official standard"* — this is the honest and acceptable position.

## 6. Daily rituals (all 4 days)

* **09:30 standup** — each team: done yesterday / doing today / blockers. 15 min hard stop.
* **20:00 integration check** — someone merges reviewed PRs to `develop`, all pull, `python -m pytest` green, app boots against develop backend. The person who breaks develop fixes develop before bed.
* Contract changes (before freeze): 2-minute stand-up agreement + architect in the PR. After freeze: additions only, announced.

## 7. Risk register

| # | Risk | Likelihood | Mitigation | Trigger to invoke |
|---|---|---|---|---|
| 1 | Dataset/model not ready by gate | High | Two-track plan; GO/NO-GO gate; demo mode is the product | gate fails → NO-GO, no debate |
| 2 | Defect-class photos too few | High | start collection tonight; buy damaged/rotten onions if needed; label onion-class first | <50 defect images by 8 Sep EOD |
| 3 | Venue network blocks Expo/cloud | Med | hotspot rehearsal (Day 3), offline MOCK mode, backup screen recording | first sign of blocked ports |
| 4 | Standards not verifiable in time | Med | honest MVP wording everywhere (already built-in) | 8 Sep EOD no citation |
| 5 | Laptop/phone failure | Low | repo on GitHub, compose repro in minutes, backup laptop with clone | any hardware wobble → switch early |
| 6 | Team member unavailable | Low | ownership map + docs allow handoff; no solo knowledge | anyone feels like a single point |
| 7 | Scope creep ("just one more feature") | **Certain** | ARCHITECTURE.md §8 do-not-build list; feature freeze Day 3 | anyone says "small addition" |
| 8 | Contract drift breaks mobile/backend | Low | freeze after Day 1; CI runs backend+ML+mobile checks | any PR touching schemas |

## 8. Demo readiness — definition of done

- [ ] `main` tagged `v0.1-demo`; develop tests green; CI green
- [ ] `/api/health` → `database: connected` on demo hardware
- [ ] Full flow (batch → analyze → results → PDF) timed < 6 min, done twice cleanly
- [ ] Rollback to DEMO MODE practiced (if real model is in)
- [ ] Offline fallback verified (backend off → app still navigates, MOCK banners visible)
- [ ] Every demo result honestly labeled (banner / watermark / verbal)
- [ ] Backup screen recording on the phone
- [ ] Deck + printed script + Q&A answers ready
- [ ] All 4 team members can run the demo, not just one

## 9. After the demo (parking lot — do NOT touch during sprint)

multi-image batches · user management · Alembic autogenerate workflow ·
model retraining pipeline · judge-feedback features · AGMARK alignment doc ·
deployment guide · Expo EAS build for distributable APK.

---

*Owner of this plan: Lead Architect. Changes to priorities (P0) require the
architect. Everything else, teams control inside their owned paths.*
