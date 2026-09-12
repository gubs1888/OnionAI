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
        
        # Attempt OpenCV GrabCut to accurately snap bbox to the onion
        if img_bgr is not None:
            try:
                h_img, w_img = img_bgr.shape[:2]
                cx1, cx2 = max(0, int(x1)), min(w_img, int(x2))
                cy1, cy2 = max(0, int(y1)), min(h_img, int(y2))
                
                if cx2 > cx1 + 10 and cy2 > cy1 + 10:
                    roi = img_bgr[cy1:cy2, cx1:cx2].copy()
                    
                    mask = np.zeros(roi.shape[:2], np.uint8)
                    bgdModel = np.zeros((1, 65), np.float64)
                    fgdModel = np.zeros((1, 65), np.float64)
                    
                    # Define a rect slightly smaller than ROI. The corners of the bounding box
                    # are almost certainly background (especially with round onions).
                    rect = (3, 3, roi.shape[1] - 6, roi.shape[0] - 6)
                    
                    # Run GrabCut (3 iterations is usually enough for a tight snap)
                    import cv2
                    cv2.setRNGSeed(0) # Ensure deterministic GMM clustering
                    cv2.grabCut(roi, mask, rect, bgdModel, fgdModel, 3, cv2.GC_INIT_WITH_RECT)
                    
                    # Where mask is 2 (PR_BGD) or 0 (BGD), set to 0, else 1
                    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
                    
                    # Post-process mask to remove small noise
                    kernel = np.ones((5, 5), np.uint8)
                    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, kernel)
                    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel)
                    
                    contours, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    if contours:
                        largest_contour = max(contours, key=cv2.contourArea)
                        
                        # Get bounding box of the actual segmented onion
                        bx, by, bw, bh = cv2.boundingRect(largest_contour)
                        
                        # Only accept the snapped box if it's reasonably sized (not just a tiny piece of noise)
                        if bw > 0.2 * (cx2 - cx1) and bh > 0.2 * (cy2 - cy1):
                            new_x1 = cx1 + bx
                            new_y1 = cy1 + by
                            new_x2 = new_x1 + bw
                            new_y2 = new_y1 + bh
                            
                            det["bbox"] = [new_x1, new_y1, new_x2, new_y2]
                            
                            # Use the new tightened dimensions
                            major_axis_px = min(bw, bh)
            except Exception as e:
                print(f"GrabCut failed: {e}")
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
