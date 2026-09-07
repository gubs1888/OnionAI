# ⚠️ STANDARDS TO VERIFY — TEAM D task before the demo

**Rule for the whole team:** until the items below are verified against the
official sources, every grade / URS number produced by this system is OUR OWN
MVP heuristic. Never present it as an official certification, on stage or in
print. The UI/PDF already carry this disclaimer.

## What must be verified

| # | Item | Where it lands | Status |
|---|------|----------------|--------|
| 1 | **URS** — exact definition, category list, formula & thresholds in the problem statement / applicable standard | `backend/config/grading_config.json → urs.categories` | ⏳ TO VERIFY |
| 2 | **Grade boundaries** (A/B/C/D or official grade names) + any mandatory defect limits | `grading_config.json → official_standards_TO_VERIFY.grade_thresholds / defect_limits` | ⏳ TO VERIFY |
| 3 | **Size categories** — minimum/peer bulb diameter classes for onion (undersized cutoff in mm) | `grading_config.json → size_thresholds` | ⏳ TO VERIFY |
| 4 | **Scoring weights** — if the standard prescribes how defects weigh vs size | `grading_config.json → mvp_scoring.weights` | ⏳ TO VERIFY |
| 5 | **Report wording** — required disclaimers/citations on printed reports | `backend/app/services/report.py` | ⏳ TO VERIFY |

## How to verify (suggested)

1. Re-read Problem Statement 26031 line by line; quote exact metric names.
2. Identify the applicable official grading framework for onions in India
   (e.g. AGMARK grade designations / Food safety requirements — TEAM D to
   confirm the exact, current source and version).
3. Record values + full citation (document, section, year) in the table above.
4. Get architect sign-off → move values into `official_standards_TO_VERIFY` →
   flip the ACTIVE config only after the whole team agrees.

## Non-negotiables while unverified

* Keep `official_standards_TO_VERIFY.status = "NOT VERIFIED — do not use"`.
* Keep the demo banner on mobile results + PDF watermark.
* In the presentation, say: *"MVP scoring — thresholds being aligned with the
  official standard"* — not *"as per <standard>"*.
