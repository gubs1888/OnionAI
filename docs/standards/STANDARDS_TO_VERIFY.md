# ✅ STANDARDS — VERIFIED against NCCF 2026 procurement documents

**Verified date:** 10 Sep 2026 · **Verified by:** Team via NCCF official PDFs

## Verified sources

| # | Document | Reference | Key Content |
|---|----------|-----------|-------------|
| 1 | NCCF EOI for Empanelment of Eligible Surveyors 2026 | Ref. NCCF/EOI/2026-27/2905 | Grade-A specification (strict): 45–65mm, zero defect tolerance |
| 2 | NCCF EOI for FPO/PACS Support Agencies 2026 | Ref. NCCF/HO/BUSS/ONION/2026-27/, dated 23/06/2026 | Grade-A + Grade-URS specification (relaxed): 35–70mm, defect tolerance table |

## Verification status

| # | Item | Config location | Status |
|---|------|----------------|--------|
| 1 | **Grade-A/URS definitions** — defect tolerance tables | `backend/config/nccf_specifications.json` | ✅ VERIFIED — extracted from PAACS Annexure I pp.22-23 |
| 2 | **Grade boundaries** — GRADE_A / GRADE_URS / NON_QUALIFYING | `backend/app/services/nccf_rule_engine.py` | ✅ VERIFIED — per-onion cascading logic |
| 3 | **Size categories** — diameter ranges | `nccf_specifications.json → size_range_mm` | ✅ VERIFIED — EOI: 45–65mm, PAACS: 35–70mm |
| 4 | **Defect tolerances** — per-defect thresholds | `nccf_specifications.json → grade_a / grade_urs` | ✅ VERIFIED — full table from Annexure I |
| 5 | **Report wording** — disclaimers/citations | `backend/app/services/report.py` | ✅ UPDATED — cites NCCF specification ID |

## Important disclaimers (still apply)

1. **Non-visual parameters** (firmness, moisture, curing, smell/taste) cannot
   be verified by camera AI. The system flags these as "manual inspection required."

2. **Specifications can change** between procurement cycles. The system stores
   the specification ID (`NCCF_EOI_2026` or `NCCF_PAACS_2026`) with each
   assessment so reports are traceable to the exact spec applied.

3. **Surface area percentages** (staining ≤30%/40%, smut ≤10%/30%, sunburn ≤10%)
   are currently estimated, not measured via segmentation. True compliance would
   require instance segmentation to compute actual surface area coverage.

4. This is **AI-based visual pre-grading** — NOT an official government certification.
   Reports carry this disclaimer.

## Presentation wording

Use:
> "AI-based visual pre-grading aligned with NCCF 2026 procurement specifications
> (EOI Surveyor + PAACS FPO/PACS). Per-onion grading against the official defect
> tolerance table with configurable specification selection."

Do NOT say:
> "100% Government-certified grading" or "as per AGMARK standards"
