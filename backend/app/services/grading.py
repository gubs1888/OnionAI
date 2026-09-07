"""
GRADING ENGINE — converts objective measurements into
quality_score (0..100), grade (A/B/C/D) and human-readable reasons.

DESIGN RULES
------------
1. NO official government thresholds are hard-coded. All numbers live in
   `backend/config/grading_config.json`:
     - `mvp_scoring`   : OUR transparent MVP heuristic (what actually runs)
     - `official_standards_TO_VERIFY` : reserved — TEAM D fills after
       verification. Code does NOT read this section yet.
2. The engine is pure: measurements in -> verdict out. No DB, no I/O.
3. Reasons explain every deduction so the UI can show WHY a grade was given.

STABLE interface (contract-first — see docs/api/API_CONTRACT.md):

    grade_batch(counts, urs_percentage, avg_confidence, config=None)
      -> {"quality_score": float, "grade": "A"|"B"|"C"|"D", "reasons": [str]}
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.config import settings


class GradingError(RuntimeError):
    """Raised when grading configuration is missing/invalid."""


@lru_cache(maxsize=4)
def _load_cached(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise GradingError(
            f"Grading config not found at '{p}'. It ships with the repo — "
            "do not delete backend/config/grading_config.json."
        )
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_config() -> dict:
    """Load (and cache) the grading configuration."""
    return _load_cached(str(settings.grading_config_path))


def aggregate_counts(detections: list[dict], config: dict | None = None) -> dict:
    """
    detections -> mutually-exclusive count buckets.

    Bucketing rules (documented contract):
      * damaged/rotten/sprouted -> their defect bucket.
      * class 'onion' smaller than size threshold -> `undersized`.
      * remaining 'onion' -> `healthy`.
    Buckets always sum to total_onions. Undersized counts as non-healthy in
    defect_percentage (matches the agreed Backend->Mobile contract).
    """
    cfg = config or load_config()
    min_mm = float(cfg["size_thresholds"]["min_size_mm"])  # PLACEHOLDER — verify!

    counts = {
        "total_onions": 0,
        "healthy": 0,
        "damaged": 0,
        "rotten": 0,
        "sprouted": 0,
        "undersized": 0,
    }
    for det in detections:
        counts["total_onions"] += 1
        name = det["class_name"]
        if name in ("damaged", "rotten", "sprouted"):
            counts[name] += 1
        elif name == "onion":
            size = det.get("estimated_size_mm")
            if size is not None and size < min_mm:
                counts["undersized"] += 1
            else:
                counts["healthy"] += 1
        # Unknown class names are ignored with a note (forward compatibility).
    counts["healthy"] = max(
        0,
        counts["total_onions"]
        - counts["damaged"]
        - counts["rotten"]
        - counts["sprouted"]
        - counts["undersized"],
    )
    return counts


def grade_batch(
    counts: dict,
    urs_percentage: float,
    avg_confidence: float,
    config: dict | None = None,
) -> dict:
    """
    Pure MVP scoring:

        score = 100
                - weights.defect      * defect%     (share of non-healthy)
                - weights.urs         * URS%
                - weights.confidence  * 100 * lowConfidenceShare

    then clamped to [floor, ceiling] and mapped to a grade via
    `mvp_scoring.grade_thresholds`.

    THIS IS OUR MVP LOGIC — not an official grading standard.
    """
    cfg = config or load_config()
    mvp = cfg["mvp_scoring"]
    weights = mvp["weights"]
    floor = float(mvp.get("quality_score_floor", 0))
    ceiling = float(mvp.get("quality_score_ceiling", 100))

    total = int(counts.get("total_onions", 0))
    if total <= 0:
        return {
            "quality_score": 0.0,
            "grade": "D",
            "reasons": ["No onions to grade (total = 0)."],
        }

    non_healthy = counts.get("damaged", 0) + counts.get("rotten", 0) + counts.get("sprouted", 0) + counts.get("undersized", 0)
    defect_pct = non_healthy * 100.0 / total

    clamp = lambda v: max(0.0, min(100.0, float(v)))  # noqa: E731
    defect_term = weights["defect"] * clamp(defect_pct)
    urs_term = weights["urs"] * clamp(urs_percentage)

    low_conf_threshold = float(mvp["low_confidence_threshold"])
    total_dets = sum(
        1
        for key in ("healthy", "damaged", "rotten", "sprouted", "undersized")
        # confidence share is computed by the caller over detections; here we
        # approximate with avg_confidence when per-detection data is absent.
        if key in counts
    )
    # avg_confidence (0..1): penalty grows linearly as it drops below threshold.
    if avg_confidence >= low_conf_threshold:
        conf_term = 0.0
    else:
        shortfall = (low_conf_threshold - clamp(avg_confidence)) / low_conf_threshold
        conf_term = weights["confidence"] * 100.0 * min(1.0, shortfall)

    score = 100.0 - defect_term - urs_term - conf_term
    score = round(max(floor, min(ceiling, score)), 1)

    grade = _score_to_grade(score, mvp["grade_thresholds"])

    reasons: list[str] = []
    if defect_pct > 0:
        reasons.append(
            f"{non_healthy}/{total} onions non-healthy (defect {defect_pct:.1f}%) "
            f"-{defect_term:.1f} pts"
        )
    if urs_percentage > 0:
        reasons.append(f"URS {urs_percentage:.1f}% -{urs_term:.1f} pts")
    if conf_term > 0:
        reasons.append(
            f"Average confidence {avg_confidence:.2f} below threshold "
            f"{low_conf_threshold:.2f} -{conf_term:.1f} pts"
        )
    if not reasons:
        reasons.append("No deductions — batch meets MVP thresholds.")
    reasons.append(
        "NOTE: grade per OUR MVP thresholds (mvp_scoring), not an official standard."
    )

    return {"quality_score": score, "grade": grade, "reasons": reasons}


def _score_to_grade(score: float, thresholds: dict) -> str:
    """Highest grade whose threshold is satisfied (thresholds are minimums)."""
    ordered = sorted(thresholds.items(), key=lambda kv: kv[1], reverse=True)
    for grade, minimum in ordered:
        if score >= float(minimum):
            return grade
    return ordered[-1][0] if ordered else "D"
