"""
GRADING ENGINE — converts objective measurements into quality verdicts.

ARCHITECTURE (post-NCCF integration):
--------------------------------------
Two grading paths are available, controlled by grading_config.json:

1. NCCF Rule Engine (default, use_nccf_engine=true):
   Per-onion classification against NCCF 2026 specifications.
   Produces: GRADE_A / GRADE_URS / NON_QUALIFYING per onion,
   then aggregates to batch-level statistics.

2. Legacy MVP Scoring (fallback, use_nccf_engine=false):
   Weighted heuristic: 100 - defect_term - urs_term - confidence_term
   Produces: quality_score (0..100) → grade (A/B/C/D).

Both paths are pure: measurements in → verdict out. No DB, no I/O.

STABLE interface:
    grade_batch(counts, urs_percentage, avg_confidence, config=None)
      -> {"quality_score", "grade", "reasons", ...}

    grade_batch_nccf(detections, config=None)
      -> BatchGradeResult (from nccf_rule_engine)
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


# --- 8-class defect names (matches ml/config.py contract) ---
DEFECT_CLASS_NAMES = (
    "damaged", "rotten", "sprouted", "cut_crack", "smut", "discoloured", "fresh_roots"
)


def aggregate_counts(detections: list[dict], config: dict | None = None) -> dict:
    """
    detections -> mutually-exclusive count buckets.

    Bucketing rules:
      * Any known defect class -> its bucket.
      * class 'onion' smaller than size threshold -> `undersized`.
      * remaining 'onion' -> `healthy`.
    Buckets always sum to total_onions.
    """
    cfg = config or load_config()
    min_mm = float(cfg.get("size_thresholds", {}).get("min_size_mm", 35))
    max_mm = float(cfg.get("size_thresholds", {}).get("max_size_mm", 70))

    counts: dict[str, int] = {
        "total_onions": 0,
        "healthy": 0,
        "damaged": 0,
        "rotten": 0,
        "sprouted": 0,
        "undersized": 0,
        # New NCCF-specific buckets
        "cut_crack": 0,
        "smut": 0,
        "discoloured": 0,
        "fresh_roots": 0,
    }
    for det in detections:
        counts["total_onions"] += 1
        name = det["class_name"]
        if name in DEFECT_CLASS_NAMES:
            counts[name] = counts.get(name, 0) + 1
        elif name == "onion":
            size = det.get("estimated_size_mm")
            if size is not None and (size < min_mm or size > max_mm):
                counts["undersized"] += 1
            else:
                counts["healthy"] += 1
        # Unknown class names are ignored with a note (forward compatibility).

    # Recompute healthy to ensure buckets sum correctly
    total_defects = sum(
        counts.get(k, 0) for k in DEFECT_CLASS_NAMES
    ) + counts["undersized"]
    counts["healthy"] = max(0, counts["total_onions"] - total_defects)
    return counts


# ---------------------------------------------------------------------------
# NCCF Rule Engine path (primary)
# ---------------------------------------------------------------------------

def grade_batch_nccf(detections: list[dict], config: dict | None = None):
    """Grade a batch using the NCCF specification rule engine.

    Returns a BatchGradeResult with per-onion grades and batch statistics.
    """
    from app.services.nccf_rule_engine import (
        BatchGradeResult,
        extract_features,
        get_active_spec,
        grade_batch as nccf_grade_batch,
        load_nccf_specs,
    )

    specs = load_nccf_specs(settings.nccf_spec_path)
    spec_id, spec = get_active_spec(specs)
    features = extract_features(detections)
    return nccf_grade_batch(features, spec, spec_id)


# ---------------------------------------------------------------------------
# Legacy MVP scoring path (backward compatibility)
# ---------------------------------------------------------------------------

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
    Preserved for backward compatibility.
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

    non_healthy = sum(
        counts.get(k, 0) for k in DEFECT_CLASS_NAMES
    ) + counts.get("undersized", 0)
    defect_pct = non_healthy * 100.0 / total

    clamp = lambda v: max(0.0, min(100.0, float(v)))  # noqa: E731
    defect_term = weights["defect"] * clamp(defect_pct)
    urs_term = weights["urs"] * clamp(urs_percentage)

    low_conf_threshold = float(mvp["low_confidence_threshold"])
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
