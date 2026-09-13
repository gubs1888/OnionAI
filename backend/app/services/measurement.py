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
    distance_cm: float | None = None,
    image_width: int = 0,
    image_path: str | None = None,
) -> list[dict]:
    """
    Add `estimated_size_mm` and `diameter_px` to every detection dict.
    Uses OpenCV contour fitting for accurate diameters, falling back to bbox.
    """
    import cv2
    import numpy as np

    cfg = config or load_config()
    out: list[dict] = []
    
    # Calculate physical width of the entire image if distance is provided.
    # We use a calibrated Field-of-View constant of 4.8 for standard portrait mode shots.
    # This accounts for the narrower horizontal FOV of the sensor's short edge.
    mm_per_pixel = None
    if distance_cm is not None and image_width > 0:
        total_fov_width_mm = 4.8 * distance_cm
        mm_per_pixel = total_fov_width_mm / image_width

    # Pre-load image for contour extraction if available
    img_bgr = None
    if image_path:
        img_bgr = cv2.imread(image_path)

    for det in detections:
        det = dict(det)
        x1, y1, x2, y2 = det["bbox"]
        
        # Default fallback: Raw pixel dimensions of the bounding box
        width_px = x2 - x1
        height_px = y2 - y1
        # Use min to avoid massive overestimation if YOLO box spans two onions
        major_axis_px = min(width_px, height_px)
        
        # Attempt fast OpenCV GrabCut refinement for accurate bbox snapping
        if img_bgr is not None:
            try:
                h_img, w_img = img_bgr.shape[:2]
                cx1, cx2 = max(0, int(x1)), min(w_img, int(x2))
                cy1, cy2 = max(0, int(y1)), min(h_img, int(y2))
                
                # Only run GrabCut on reasonably sized regions and limit ROI resolution to max 200px
                if cx2 > cx1 + 15 and cy2 > cy1 + 15:
                    roi = img_bgr[cy1:cy2, cx1:cx2].copy()
                    roi_h, roi_w = roi.shape[:2]
                    scale_factor = 1.0
                    if max(roi_h, roi_w) > 200:
                        scale_factor = 200.0 / max(roi_h, roi_w)
                        roi = cv2.resize(roi, (int(roi_w * scale_factor), int(roi_h * scale_factor)), interpolation=cv2.INTER_AREA)
                    
                    mask = np.zeros(roi.shape[:2], np.uint8)
                    bgdModel = np.zeros((1, 65), np.float64)
                    fgdModel = np.zeros((1, 65), np.float64)
                    
                    if roi.shape[1] > 10 and roi.shape[0] > 10:
                        rect = (2, 2, roi.shape[1] - 4, roi.shape[0] - 4)
                        import cv2
                        if hasattr(cv2, "setRNGSeed"):
                            cv2.setRNGSeed(0)
                        cv2.grabCut(roi, mask, rect, bgdModel, fgdModel, 1, cv2.GC_INIT_WITH_RECT)
                        
                        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
                        contours, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        
                        if contours:
                            largest_contour = max(contours, key=cv2.contourArea)
                            bx, by, bw, bh = cv2.boundingRect(largest_contour)
                            
                            # Scale back coordinates to original resolution
                            bw_orig = int(bw / scale_factor)
                            bh_orig = int(bh / scale_factor)
                            if bw_orig > 0.2 * (cx2 - cx1) and bh_orig > 0.2 * (cy2 - cy1):
                                major_axis_px = min(bw_orig, bh_orig)
            except Exception as e:
                pass
        
        if pixel_to_mm is not None:
            size_mm = major_axis_px * pixel_to_mm
        elif mm_per_pixel is not None:
            size_mm = major_axis_px * mm_per_pixel
        else:
            # Fallback if no distance slider provided.
            # Assume mm_per_pixel is roughly 0.18 for a standard crop/scale.
            size_mm = major_axis_px * 0.18
            
        size_mm = max(0.0, size_mm)
        det["diameter_px"] = round(major_axis_px, 1)
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


def size_in_range(diameter_mm: float | None, spec: dict) -> bool:
    """Check if an onion's diameter falls within the NCCF specification range.

    spec: an NCCF specification dict containing 'size_range_mm' with 'min' and 'max'.
    Returns True if the diameter is within range, or if diameter is None.
    """
    if diameter_mm is None:
        return True  # Cannot verify
    size_range = spec.get("size_range_mm", {})
    min_mm = size_range.get("min", 0)
    max_mm = size_range.get("max", 999)
    return min_mm <= diameter_mm <= max_mm
