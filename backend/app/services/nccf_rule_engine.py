"""
NCCF GOVERNMENT SPECIFICATION RULE ENGINE

Applies NCCF 2026 procurement specifications to grade individual onions
as GRADE_A / GRADE_URS / NON_QUALIFYING, then aggregates batch-level
statistics.

Architecture:
    YOLO detections → extract_features() → per-onion OnionFeatures
        → classify_onion() per spec → GRADE_A / GRADE_URS / NON_QUALIFYING
        → grade_batch() → BatchGradeResult with counts + percentages

This module is PURE — no DB, no I/O. All thresholds come from the
nccf_specifications.json config file.

Source specifications:
    - NCCF EOI Surveyor 2026 (strict: 45–65mm, zero defect tolerance)
    - NCCF PAACS FPO/PACS 2026 (relaxed: 35–70mm, Grade-A + Grade-URS)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any


# NCCF features that cannot be detected by the current YOLO model
# and must be flagged for manual inspection
_UNDETECTABLE_FEATURES: list[str] = [
    "ruptured_skin",
    "open_neck",
    "dry_sun_scald",
    "sunburn",
    "seed_stem",
    "double_misshape",
    "without_skin",
    "bacterial_soft_neck_rot",
    "thick_neck",
]


# Canonical dictionary mapping internal spec keys to clear, professional human-readable descriptions
_DEFECT_HUMAN_NAMES: dict[str, str] = {
    "cut_crack": "Cut / crack",
    "ruptured_skin": "Ruptured skin",
    "fresh_roots": "Fresh roots",
    "open_neck": "Open neck",
    "dry_sun_scald": "Dry sun scald",
    "seed_stem": "Seed stem",
    "sprouted": "Sprouted",
    "mechanical_injury": "Mechanical injury / physical damage",
    "damaged": "Mechanical injury / physical damage",
    "without_skin": "Without skin",
    "slimy_soft_rot": "Rotten / soft rot",
    "rot_rotting_fungal": "Rotten / decay",
    "bacterial_soft_neck_rot": "Bacterial soft neck rot",
    "double_misshape": "Double / misshaped",
    "misshaped": "Double / misshaped",
    "staining_discoloration": "Staining / discoloration",
    "sunburn": "Sunburn",
    "smut": "Smut",
    "thick_neck": "Thick neck",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class OnionFeatures:
    """Per-onion feature vector extracted from YOLO detections + CV."""

    onion_id: int
    diameter_mm: float | None = None

    # Boolean defects (detected by YOLO or flagged for manual inspection)
    sprouted: bool = False
    rotten: bool = False
    cut_crack: bool = False
    ruptured_skin: bool = False
    fresh_roots: bool = False
    open_neck: bool = False
    dry_sun_scald: bool = False
    seed_stem: bool = False
    misshaped: bool = False
    damaged: bool = False       # generic mechanical injury
    without_skin: bool = False
    bacterial_soft_neck_rot: bool = False

    # Surface-area percentages (require segmentation — currently estimated)
    sunburn_percentage: float = 0.0
    staining_percentage: float = 0.0
    smut_percentage: float = 0.0

    # Physical measurement
    thick_neck_mm: float = 0.0

    # Confidence of the primary onion detection
    confidence: float = 0.0

    # Features that couldn't be measured and need manual inspection
    manual_inspection_required: list[str] = field(
        default_factory=lambda: list(_UNDETECTABLE_FEATURES)
    )

    # Raw defect class names detected on this onion
    detected_defects: list[str] = field(default_factory=list)

    # Spatial geometry details (bounding box, location, coverage %)
    onion_bbox: list[float] | None = None
    defect_details: list[dict] = field(default_factory=list)


@dataclass
class OnionGradeResult:
    """Classification result for a single onion."""

    onion_id: int
    grade: str  # "GRADE_A" | "GRADE_URS" | "NON_QUALIFYING"
    disqualifying_reasons: list[str] = field(default_factory=list)
    manual_inspection_required: list[str] = field(default_factory=list)
    features: OnionFeatures | None = None


@dataclass
class BatchGradeResult:
    """Aggregated grading result for a batch of onions."""

    specification_id: str = ""
    specification_name: str = ""
    total_onions: int = 0
    grade_a_count: int = 0
    grade_urs_count: int = 0
    non_qualifying_count: int = 0
    grade_a_pct: float = 0.0
    grade_urs_pct: float = 0.0
    non_qualifying_pct: float = 0.0
    batch_grade: str = "NON_QUALIFYING"  # overall batch assessment
    per_onion_grades: list[dict] = field(default_factory=list)
    defect_breakdown: dict[str, int] = field(default_factory=dict)
    manual_flags: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


@dataclass
class FailureDetail:
    """Internal detail of a tolerance check failure for precise reasoning."""

    spec_key: str
    feature_attr: str
    failure_type: str  # "not_allowed", "exceeds_pct", "exceeds_mm"
    val: float | bool = True
    max_val: float | None = None


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

@lru_cache(maxsize=4)
def _load_cached(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise RuntimeError(
            f"NCCF specification file not found at '{p}'. "
            "It should be at backend/config/nccf_specifications.json."
        )
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_nccf_specs(path: str | Path) -> dict:
    """Load (and cache) the NCCF specifications."""
    return _load_cached(str(path))


def get_active_spec(specs: dict) -> tuple[str, dict]:
    """Return (spec_id, spec_dict) for the active specification."""
    active_id = specs.get("active_specification", "NCCF_PAACS_2026")
    spec = specs["specifications"].get(active_id)
    if spec is None:
        raise RuntimeError(
            f"Active specification '{active_id}' not found in nccf_specifications.json."
        )
    return active_id, spec


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

# YOLO class name → NCCF defect feature name
_YOLO_TO_NCCF_FEATURE: dict[str, str] = {
    "sprouted": "sprouted",
    "rotten": "rot_rotting_fungal",
    "cut_crack": "cut_crack",
    "smut": "smut",
    "discoloured": "staining_discoloration",
    "fresh_roots": "fresh_roots",
    "damaged": "mechanical_injury",
}


def extract_features(detections: list[dict]) -> list[OnionFeatures]:
    """Convert YOLO detections into per-onion OnionFeatures.

    Strategy:
    1. Find all 'onion'-class detections (healthy onion instances).
    2. For each defect detection, associate it with the nearest/overlapping
       onion by bounding box IoU.
    3. Build an OnionFeatures object for each onion with its defects.

    Defect detections that don't overlap any 'onion' detection are treated
    as standalone onions (the onion detector may have missed them, but the
    defect detector caught them).
    """
    onion_dets: list[dict] = []
    defect_dets: list[dict] = []
    for det in detections:
        if det["class_name"] == "onion":
            onion_dets.append(det)
        else:
            defect_dets.append(det)

    features_map: dict[int, OnionFeatures] = {}
    for i, det in enumerate(onion_dets):
        features_map[i] = OnionFeatures(
            onion_id=i + 1,
            diameter_mm=det.get("estimated_size_mm"),
            confidence=det.get("confidence", 0.0),
            onion_bbox=det.get("bbox"),
        )

    used_defects: set[int] = set()
    for d_idx, ddet in enumerate(defect_dets):
        best_onion_idx = _find_best_overlap(ddet["bbox"], onion_dets)
        if best_onion_idx is not None:
            _apply_defect(features_map[best_onion_idx], ddet)
            used_defects.add(d_idx)

    next_id = len(onion_dets) + 1
    for d_idx, ddet in enumerate(defect_dets):
        if d_idx not in used_defects:
            feat = OnionFeatures(
                onion_id=next_id,
                diameter_mm=ddet.get("estimated_size_mm"),
                confidence=ddet.get("confidence", 0.0),
                onion_bbox=ddet.get("bbox"),
            )
            _apply_defect(feat, ddet)
            features_map[next_id - 1] = feat
            next_id += 1

    for feat in features_map.values():
        feat.manual_inspection_required = list(_UNDETECTABLE_FEATURES)

    return list(features_map.values())


def compute_defect_spatial_details(
    defect_bbox: list[float], onion_bbox: list[float] | None, class_name: str
) -> dict:
    """Compute spatial location and surface coverage for a defect relative to the onion bulb."""
    location = "Surface"
    coverage_pct = 10.0

    if onion_bbox and len(onion_bbox) == 4 and len(defect_bbox) == 4:
        ox1, oy1, ox2, oy2 = onion_bbox
        dx1, dy1, dx2, dy2 = defect_bbox
        ow = max(1.0, ox2 - ox1)
        oh = max(1.0, oy2 - oy1)

        defect_cy = (dy1 + dy2) / 2.0
        rel_y = (defect_cy - oy1) / oh

        if rel_y < 0.35:
            location = "Upper Shoulder / Neck region"
        elif rel_y > 0.65:
            location = "Lower Base / Root region"
        else:
            location = "Mid-Bulb Body region"

        defect_area = max(0.0, dx2 - dx1) * max(0.0, dy2 - dy1)
        onion_area = ow * oh
        coverage_pct = min(100.0, round((defect_area / onion_area) * 100.0, 1))
        if coverage_pct <= 0.0:
            coverage_pct = 5.0

    name_label_map = {
        "cut_crack": "Cut / Crack",
        "damaged": "Mechanical Injury",
        "rotten": "Rotten",
        "sprouted": "Sprouted",
        "smut": "Smut",
        "discoloured": "Discoloured",
        "fresh_roots": "Fresh Roots",
    }
    label = name_label_map.get(class_name, class_name.replace("_", " ").title())

    desc_map = {
        "cut_crack": f"Cut / Crack: Outer skin rupture/tearing located at {location} (~{coverage_pct}% bulb area).",
        "damaged": f"Damaged: Mechanical injury/husk abrasion located at {location} (~{coverage_pct}% bulb area).",
        "rotten": f"Rotten: Fungal rot/soft decay located at {location} (~{coverage_pct}% bulb area).",
        "sprouted": f"Sprouted: Emerging green shoot located at {location} (~{coverage_pct}% bulb area).",
        "smut": f"Smut: Black fungal spore lesion located at {location} (~{coverage_pct}% bulb area).",
        "discoloured": f"Discoloured: Surface husk staining located at {location} (~{coverage_pct}% bulb area).",
        "fresh_roots": f"Fresh Roots: Protruding un-trimmed root cluster at {location} (~{coverage_pct}% bulb area).",
    }
    desc = desc_map.get(class_name, f"{label}: Defect located at {location} (~{coverage_pct}% bulb area).")

    return {
        "class_name": class_name,
        "label": label,
        "location": location,
        "coverage_pct": coverage_pct,
        "description": desc,
    }


def _find_best_overlap(
    defect_bbox: list[float], onion_dets: list[dict]
) -> int | None:
    """Find the onion detection with the highest IoU overlap with the defect bbox."""
    if not onion_dets:
        return None

    best_idx = None
    best_iou = 0.0

    for i, odet in enumerate(onion_dets):
        iou = _bbox_iou(defect_bbox, odet["bbox"])
        if iou > best_iou:
            best_iou = iou
            best_idx = i

    return best_idx if best_iou >= 0.10 else None


def _bbox_iou(a: list[float], b: list[float]) -> float:
    """Compute Intersection over Union for two [x1, y1, x2, y2] bboxes."""
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])

    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if inter == 0:
        return 0.0

    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _apply_defect(features: OnionFeatures, det: dict) -> None:
    """Apply a defect detection to an OnionFeatures object."""
    name = det["class_name"]
    features.detected_defects.append(name)

    bbox = det.get("bbox", [])
    spatial_info = compute_defect_spatial_details(bbox, features.onion_bbox, name)
    features.defect_details.append(spatial_info)

    if name == "sprouted":
        features.sprouted = True
    elif name == "rotten":
        features.rotten = True
    elif name == "cut_crack":
        features.cut_crack = True
    elif name == "smut":
        features.smut_percentage = max(features.smut_percentage, spatial_info["coverage_pct"])
    elif name == "discoloured":
        features.staining_percentage = max(features.staining_percentage, spatial_info["coverage_pct"])
    elif name == "fresh_roots":
        features.fresh_roots = True
    elif name == "damaged":
        features.damaged = True


# ---------------------------------------------------------------------------
# Per-onion classification
# ---------------------------------------------------------------------------

def classify_onion(
    features: OnionFeatures,
    spec: dict,
    spec_id: str = "",
) -> OnionGradeResult:
    """Classify a single onion against a specification.

    Logic:
        1. Check Grade-A tolerances → if all pass → GRADE_A
        2. If Grade-A fails and spec has URS → check Grade-URS → GRADE_URS
        3. Otherwise → NON_QUALIFYING
    """
    result = OnionGradeResult(
        onion_id=features.onion_id,
        grade="GRADE_A",
        manual_inspection_required=list(features.manual_inspection_required),
        features=features,
    )

    # --- Size check (applies to both grades) ---
    size_reason: str | None = None
    size_range = spec.get("size_range_mm", {})
    if features.diameter_mm is not None:
        min_mm = size_range.get("min", 0)
        max_mm = size_range.get("max", 999)
        if not (min_mm <= features.diameter_mm <= max_mm):
            size_reason = (
                f"Bulb size {features.diameter_mm:.1f}mm outside allowable range "
                f"({min_mm}–{max_mm}mm)"
            )

    # --- Check Grade-A ---
    grade_a_spec = spec.get("grade_a", {})
    grade_a_failures = _check_tolerances(features, grade_a_spec)

    if not grade_a_failures and size_reason is None:
        result.grade = "GRADE_A"
        return result

    # --- Check Grade-URS (if available) ---
    if spec.get("has_urs_grade", False):
        grade_urs_spec = spec.get("grade_urs", {})
        grade_urs_failures = _check_tolerances(features, grade_urs_spec)

        if not grade_urs_failures and size_reason is None:
            result.grade = "GRADE_URS"
            reasons = []
            for f in grade_a_failures:
                name = _DEFECT_HUMAN_NAMES.get(f.spec_key, f.spec_key.replace("_", " ").title())
                if f.failure_type == "not_allowed":
                    reasons.append(f"{name} detected (disqualifies Grade A)")
                elif f.failure_type == "exceeds_pct":
                    reasons.append(f"{name} {f.val:.1f}% exceeds Grade A limit ({f.max_val:.0f}%)")
                elif f.failure_type == "exceeds_mm":
                    reasons.append(f"{name} {f.val:.1f}mm exceeds Grade A limit ({f.max_val:.0f}mm)")
            result.disqualifying_reasons = reasons
            return result

        # Failed both Grade A and Grade URS -> NON_QUALIFYING
        result.grade = "NON_QUALIFYING"
        reasons = []
        if size_reason:
            reasons.append(size_reason)

        grade_a_by_attr = {f.feature_attr: f for f in grade_a_failures}
        grade_urs_by_attr = {f.feature_attr: f for f in grade_urs_failures}

        # Deduplicated list of feature_attrs that failed either grade
        all_failed_attrs: list[str] = []
        for f in grade_a_failures:
            if f.feature_attr not in all_failed_attrs:
                all_failed_attrs.append(f.feature_attr)
        for f in grade_urs_failures:
            if f.feature_attr not in all_failed_attrs:
                all_failed_attrs.append(f.feature_attr)

        for attr in all_failed_attrs:
            fa = grade_a_by_attr.get(attr)
            fu = grade_urs_by_attr.get(attr)

            if fa and fu:
                # Failed BOTH Grade A and Grade URS
                name = _DEFECT_HUMAN_NAMES.get(fa.spec_key, fa.spec_key.replace("_", " ").title())
                if fa.failure_type == "not_allowed" and fu.failure_type == "not_allowed":
                    reasons.append(f"{name} detected (disqualifies Grade A and URS)")
                elif fa.failure_type == "exceeds_pct" or fu.failure_type == "exceeds_pct":
                    reasons.append(f"{name} {fa.val:.1f}% exceeds allowable limits")
                elif fa.failure_type == "exceeds_mm" or fu.failure_type == "exceeds_mm":
                    reasons.append(f"{name} {fa.val:.1f}mm exceeds allowable limits")
                else:
                    reasons.append(f"{name} detected (disqualifies Grade A and URS)")
            elif fa and not fu:
                # Failed Grade A only
                name = _DEFECT_HUMAN_NAMES.get(fa.spec_key, fa.spec_key.replace("_", " ").title())
                if fa.failure_type == "not_allowed":
                    reasons.append(f"{name} detected (disqualifies Grade A)")
                elif fa.failure_type == "exceeds_pct":
                    reasons.append(f"{name} {fa.val:.1f}% exceeds Grade A limit ({fa.max_val:.0f}%)")
                elif fa.failure_type == "exceeds_mm":
                    reasons.append(f"{name} {fa.val:.1f}mm exceeds Grade A limit ({fa.max_val:.0f}mm)")
            elif fu and not fa:
                # Failed URS only
                name = _DEFECT_HUMAN_NAMES.get(fu.spec_key, fu.spec_key.replace("_", " ").title())
                reasons.append(f"{name} exceeds URS limit")

        result.disqualifying_reasons = reasons
    else:
        # No URS grade in this spec (e.g. EOI spec)
        result.grade = "NON_QUALIFYING"
        reasons = []
        if size_reason:
            reasons.append(size_reason)

        for f in grade_a_failures:
            name = _DEFECT_HUMAN_NAMES.get(f.spec_key, f.spec_key.replace("_", " ").title())
            if f.failure_type == "not_allowed":
                reasons.append(f"{name} detected (not allowed)")
            elif f.failure_type == "exceeds_pct":
                reasons.append(f"{name} {f.val:.1f}% exceeds max {f.max_val:.0f}%")
            elif f.failure_type == "exceeds_mm":
                reasons.append(f"{name} {f.val:.1f}mm exceeds max {f.max_val:.0f}mm")

        result.disqualifying_reasons = reasons

    return result


def _check_tolerances(
    features: OnionFeatures, grade_spec: dict
) -> list[FailureDetail]:
    """Check an onion's features against a grade's tolerance table.

    Returns a list of FailureDetail objects (empty = passes).
    Deduplicates by feature_attr so multiple spec keys mapping to the same
    underlying feature (e.g., rot_rotting_fungal & slimy_soft_rot -> rotten)
    only produce one failure entry per grade evaluation.
    """
    failures: list[FailureDetail] = []
    seen_feature_attrs: set[str] = set()

    _checks: list[tuple[str, str, Any]] = [
        ("cut_crack", "cut_crack", features.cut_crack),
        ("ruptured_skin", "ruptured_skin", features.ruptured_skin),
        ("fresh_roots", "fresh_roots", features.fresh_roots),
        ("open_neck", "open_neck", features.open_neck),
        ("dry_sun_scald", "dry_sun_scald", features.dry_sun_scald),
        ("seed_stem", "seed_stem", features.seed_stem),
        ("sprouted", "sprouted", features.sprouted),
        ("mechanical_injury", "damaged", features.damaged),
        ("without_skin", "without_skin", features.without_skin),
        ("rot_rotting_fungal", "rotten", features.rotten),
        ("slimy_soft_rot", "rotten", features.rotten),
        ("bacterial_soft_neck_rot", "bacterial_soft_neck_rot", features.bacterial_soft_neck_rot),
        ("double_misshape", "misshaped", features.misshaped),
    ]

    for spec_key, feature_attr, feature_val in _checks:
        if feature_attr in seen_feature_attrs:
            continue
        rule = grade_spec.get(spec_key, {})
        if not rule:
            continue
        if not rule.get("allowed", True) and feature_val:
            failures.append(
                FailureDetail(
                    spec_key=spec_key,
                    feature_attr=feature_attr,
                    failure_type="not_allowed",
                    val=True,
                )
            )
            seen_feature_attrs.add(feature_attr)

    # Surface-area percentage checks
    _pct_checks: list[tuple[str, str, float]] = [
        ("staining_discoloration", "staining_percentage", features.staining_percentage),
        ("sunburn", "sunburn_percentage", features.sunburn_percentage),
        ("smut", "smut_percentage", features.smut_percentage),
    ]

    for spec_key, feature_attr, pct_val in _pct_checks:
        if feature_attr in seen_feature_attrs:
            continue
        rule = grade_spec.get(spec_key, {})
        if not rule:
            continue
        if not rule.get("allowed", True) and pct_val > 0:
            failures.append(
                FailureDetail(
                    spec_key=spec_key,
                    feature_attr=feature_attr,
                    failure_type="not_allowed",
                    val=pct_val,
                )
            )
            seen_feature_attrs.add(feature_attr)
        elif rule.get("allowed", False):
            max_pct = rule.get("max_surface_pct")
            if max_pct is not None and pct_val > max_pct:
                failures.append(
                    FailureDetail(
                        spec_key=spec_key,
                        feature_attr=feature_attr,
                        failure_type="exceeds_pct",
                        val=pct_val,
                        max_val=max_pct,
                    )
                )
                seen_feature_attrs.add(feature_attr)

    # Thick neck diameter check
    thick_rule = grade_spec.get("thick_neck", {})
    if thick_rule and "thick_neck" not in seen_feature_attrs:
        max_mm = thick_rule.get("max_diameter_mm")
        if max_mm is not None and features.thick_neck_mm > max_mm:
            failures.append(
                FailureDetail(
                    spec_key="thick_neck",
                    feature_attr="thick_neck",
                    failure_type="exceeds_mm",
                    val=features.thick_neck_mm,
                    max_val=max_mm,
                )
            )
            seen_feature_attrs.add("thick_neck")

    return failures


# ---------------------------------------------------------------------------
# Batch-level grading
# ---------------------------------------------------------------------------

def grade_batch(
    features_list: list[OnionFeatures],
    spec: dict,
    spec_id: str = "",
) -> BatchGradeResult:
    """Grade a batch of onions against a specification.

    Returns aggregated counts, percentages, and per-onion details.
    """
    result = BatchGradeResult(
        specification_id=spec_id,
        specification_name=spec.get("name", spec_id),
        total_onions=len(features_list),
    )

    if not features_list:
        result.reasons.append("No onions to grade (total = 0).")
        return result

    all_manual_flags: set[str] = set()
    defect_counts: dict[str, int] = {}

    for feat in features_list:
        onion_result = classify_onion(feat, spec, spec_id)

        if onion_result.grade == "GRADE_A":
            result.grade_a_count += 1
        elif onion_result.grade == "GRADE_URS":
            result.grade_urs_count += 1
        else:
            result.non_qualifying_count += 1

        for defect in feat.detected_defects:
            defect_counts[defect] = defect_counts.get(defect, 0) + 1

        all_manual_flags.update(onion_result.manual_inspection_required)

        result.per_onion_grades.append({
            "onion_id": onion_result.onion_id,
            "grade": onion_result.grade,
            "reasons": onion_result.disqualifying_reasons[:5],
            "defects": feat.detected_defects,
            "defect_details": feat.defect_details,
            "diameter_mm": feat.diameter_mm,
            "confidence": feat.confidence,
        })

    total = result.total_onions
    result.grade_a_pct = round(result.grade_a_count * 100.0 / total, 1)
    result.grade_urs_pct = round(result.grade_urs_count * 100.0 / total, 1)
    result.non_qualifying_pct = round(result.non_qualifying_count * 100.0 / total, 1)

    result.defect_breakdown = defect_counts
    result.manual_flags = sorted(all_manual_flags)

    if result.grade_a_pct >= 50:
        result.batch_grade = "GRADE_A"
    elif result.grade_a_pct + result.grade_urs_pct >= 50:
        result.batch_grade = "GRADE_URS"
    else:
        result.batch_grade = "NON_QUALIFYING"

    result.reasons = [
        f"Specification: {result.specification_name}",
        f"Grade A: {result.grade_a_count}/{total} ({result.grade_a_pct}%)",
    ]
    if spec.get("has_urs_grade", False):
        result.reasons.append(
            f"Grade URS: {result.grade_urs_count}/{total} ({result.grade_urs_pct}%)"
        )
    result.reasons.append(
        f"Non-qualifying: {result.non_qualifying_count}/{total} ({result.non_qualifying_pct}%)"
    )
    if defect_counts:
        defect_summary = ", ".join(
            f"{k}: {v}" for k, v in sorted(defect_counts.items(), key=lambda x: -x[1])
        )
        result.reasons.append(f"Defect breakdown: {defect_summary}")
    result.reasons.append(
        "NOTE: AI-based visual pre-grading per NCCF 2026 specifications."
    )

    return result
