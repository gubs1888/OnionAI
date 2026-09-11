"""
URS SERVICE — computes the "URS percentage" metric.

POST-NCCF ARCHITECTURE:
    URS% is now a RESULT of the NCCF rule engine, not a separate computation.
    The rule engine grades each onion as GRADE_A / GRADE_URS / NON_QUALIFYING,
    and URS% = grade_urs_count / total_onions * 100.

    This module provides:
    1. compute_urs_from_nccf() — derives URS% from rule engine results (primary)
    2. compute_urs() — legacy MVP formula (backward compatibility)

    The legacy formula (configurable categories from grading_config.json)
    is preserved but should not be used for NCCF-compliant reporting.
"""

from __future__ import annotations

from app.services.grading import load_config


def compute_urs_from_nccf(batch_result) -> float:
    """Derive URS percentage from the NCCF rule engine BatchGradeResult.

    URS% = grade_urs_count / total_onions * 100

    This is the correct computation per NCCF specifications.
    """
    if batch_result.total_onions <= 0:
        return 0.0
    return round(batch_result.grade_urs_count * 100.0 / batch_result.total_onions, 1)


def compute_urs(counts: dict, config: dict | None = None) -> float:
    """
    Legacy MVP computation (backward compatibility).

    counts: bucket dict from grading.aggregate_counts(), e.g.
              {"total_onions": 48, "healthy": 39, "damaged": 4,
               "rotten": 2, "sprouted": 1, "undersized": 2, ...}
    returns: URS percentage rounded to 1 decimal (0.0 when total is 0).

    NOTE: This is the legacy formula. For NCCF-compliant reporting,
    use compute_urs_from_nccf() with the rule engine output.
    """
    cfg = config or load_config()
    urs_cfg = cfg.get("urs", {})
    categories = urs_cfg.get("categories", ["undersized", "rotten", "sprouted"])

    total = int(counts.get("total_onions", 0))
    if total <= 0:
        return 0.0

    urs_count = sum(int(counts.get(cat, 0)) for cat in categories)
    return round(urs_count * 100.0 / total, 1)
