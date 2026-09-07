"""
Size estimation service.

REAL approach (TEAM A + TEAM B, post-MVP): calibrate pixels->mm using a
reference object in the photo (coin, A4 sheet, chessboard) or a fixed
camera-to-tray distance.

MVP DEMO approach (below): map bbox diagonal to a plausible diameter with a
deterministic pseudo-calibration factor. Clearly marked DEMO — numbers are
NOT physically calibrated.
"""

from __future__ import annotations

from app.services.grading import load_config

# DEMO pseudo-calibration: mm = SIZE_DEMO_OFFSET + diag_px * SIZE_DEMO_SCALE
SIZE_DEMO_OFFSET_MM = 20.0
SIZE_DEMO_SCALE = 0.5


def estimate_sizes(
    detections: list[dict],
    config: dict | None = None,
    pixel_to_mm: float | None = None,
) -> list[dict]:
    """
    Add `estimated_size_mm` to every detection dict (returns a NEW list).

    pixel_to_mm: real calibration factor (mm per pixel). When None, the DEMO
    pseudo-calibration is used and the caller must treat sizes as estimates.
    """
    cfg = config or load_config()
    out: list[dict] = []
    for det in detections:
        det = dict(det)
        x1, y1, x2, y2 = det["bbox"]
        diag_px = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if pixel_to_mm is not None:
            size_mm = diag_px * pixel_to_mm
        else:
            # DEMO estimation — NOT calibrated. TODO(Team A/B): real calibration.
            size_mm = SIZE_DEMO_OFFSET_MM + diag_px * SIZE_DEMO_SCALE
        det["estimated_size_mm"] = round(size_mm, 1)
        out.append(det)
    return out


def count_undersized(detections: list[dict], config: dict | None = None) -> int:
    """Count healthy-class onions whose estimated diameter < configured minimum."""
    cfg = config or load_config()
    min_mm = float(cfg["size_thresholds"]["min_size_mm"])  # PLACEHOLDER — verify!
    return sum(
        1
        for d in detections
        if d["class_name"] == "onion"
        and d.get("estimated_size_mm") is not None
        and d["estimated_size_mm"] < min_mm
    )
