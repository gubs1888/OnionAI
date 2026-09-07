"""
URS SERVICE — computes the "URS percentage" metric.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!  THE EXACT DEFINITION OF URS IS **NOT YET VERIFIED**.       !!
!!  It comes from the problem statement / an official standard !!
!!  that TEAM D must confirm (docs/standards/STANDARDS_TO_VERIFY.md).
!!  Do NOT present URS numbers as official until verified.      !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

MVP interpretation (CONFIGURABLE, not hard-coded):
    URS% = 100 * (undersized + rotten + sprouted) / total_onions

The category list IS the formula — change it in
backend/config/grading_config.json -> "urs" -> "categories".
"""

from __future__ import annotations

from app.services.grading import load_config


def compute_urs(counts: dict, config: dict | None = None) -> float:
    """
    counts: bucket dict from grading.aggregate_counts(), e.g.
              {"total_onions": 48, "healthy": 39, "damaged": 4,
               "rotten": 2, "sprouted": 1, "undersized": 2}
    returns: URS percentage rounded to 1 decimal (0.0 when total is 0).

    TODO(TEAM D): verify the official URS definition/threshold, then update
    `urs.categories` in grading_config.json — no code change required.
    """
    cfg = config or load_config()
    urs_cfg = cfg.get("urs", {})
    categories = urs_cfg.get("categories", ["undersized", "rotten", "sprouted"])

    total = int(counts.get("total_onions", 0))
    if total <= 0:
        return 0.0

    urs_count = sum(int(counts.get(cat, 0)) for cat in categories)
    return round(urs_count * 100.0 / total, 1)
