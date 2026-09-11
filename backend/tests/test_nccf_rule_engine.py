"""NCCF Rule Engine tests — verify per-onion grading against government specs."""

import json
from pathlib import Path

import pytest

from app.services.nccf_rule_engine import (
    BatchGradeResult,
    OnionFeatures,
    classify_onion,
    extract_features,
    grade_batch,
    load_nccf_specs,
    get_active_spec,
)

# --- Fixtures ----------------------------------------------------------------

@pytest.fixture(scope="module")
def specs():
    from app.config import settings
    return load_nccf_specs(settings.nccf_spec_path)


@pytest.fixture(scope="module")
def paacs_spec(specs):
    _, spec = get_active_spec(specs)  # default is NCCF_PAACS_2026
    return spec


@pytest.fixture
def paacs_spec_id():
    return "NCCF_PAACS_2026"


@pytest.fixture(scope="module")
def eoi_spec(specs):
    return specs["specifications"]["NCCF_EOI_2026"]


def _perfect_onion(onion_id: int = 1, diameter_mm: float = 55.0) -> OnionFeatures:
    """A perfect healthy onion with no defects."""
    return OnionFeatures(onion_id=onion_id, diameter_mm=diameter_mm, confidence=0.95)


# --- Per-onion classification tests ------------------------------------------

class TestClassifyOnion:

    def test_perfect_onion_is_grade_a(self, paacs_spec, paacs_spec_id):
        onion = _perfect_onion()
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "GRADE_A"
        assert not result.disqualifying_reasons

    def test_sprouted_onion_fails_both_grades(self, paacs_spec, paacs_spec_id):
        onion = _perfect_onion()
        onion.sprouted = True
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "NON_QUALIFYING"
        assert result.disqualifying_reasons == ["Sprouted detected (disqualifies Grade A and URS)"]

    def test_rotten_onion_disqualifying_reasons(self, paacs_spec, paacs_spec_id):
        onion = _perfect_onion()
        onion.rotten = True
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "NON_QUALIFYING"
        assert result.disqualifying_reasons == ["Rotten / decay detected (disqualifies Grade A and URS)"]

    def test_damaged_onion_disqualifying_reasons(self, paacs_spec, paacs_spec_id):
        onion = _perfect_onion()
        onion.damaged = True
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "NON_QUALIFYING"
        assert result.disqualifying_reasons == [
            "Mechanical injury / physical damage detected (disqualifies Grade A and URS)"
        ]

    def test_misshaped_is_grade_a_fail_urs_pass(self, paacs_spec, paacs_spec_id):
        """Misshape disqualifies Grade-A but is allowed in URS."""
        onion = _perfect_onion()
        onion.misshaped = True
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "GRADE_URS"
        assert result.disqualifying_reasons == ["Double / misshaped detected (disqualifies Grade A)"]

    def test_staining_30_pct_is_grade_a_pass(self, paacs_spec, paacs_spec_id):
        """≤30% staining is allowed in Grade-A per PAACS."""
        onion = _perfect_onion()
        onion.staining_percentage = 30.0
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "GRADE_A"

    def test_staining_35_pct_is_urs_pass(self, paacs_spec, paacs_spec_id):
        """35% staining fails Grade-A (>30%) but passes URS (≤40%)."""
        onion = _perfect_onion()
        onion.staining_percentage = 35.0
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "GRADE_URS"
        assert result.disqualifying_reasons == ["Staining / discoloration 35.0% exceeds Grade A limit (30%)"]

    def test_staining_45_pct_fails_both(self, paacs_spec, paacs_spec_id):
        """45% staining exceeds both Grade-A (30%) and URS (40%)."""
        onion = _perfect_onion()
        onion.staining_percentage = 45.0
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "NON_QUALIFYING"
        assert result.disqualifying_reasons == ["Staining / discoloration 45.0% exceeds allowable limits"]

    def test_sunburn_5_pct_is_urs_pass(self, paacs_spec, paacs_spec_id):
        """Sunburn ≤10% is allowed in URS (not Grade-A)."""
        onion = _perfect_onion()
        onion.sunburn_percentage = 5.0
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "GRADE_URS"
        assert result.disqualifying_reasons == ["Sunburn detected (disqualifies Grade A)"]

    def test_undersized_fails_grade_a(self, paacs_spec, paacs_spec_id):
        """30mm diameter is below PAACS range (35-70mm)."""
        onion = _perfect_onion(diameter_mm=30.0)
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "NON_QUALIFYING"
        assert result.disqualifying_reasons == ["Bulb size 30.0mm outside allowable range (35–70mm)"]

    def test_oversized_fails_grade_a(self, paacs_spec, paacs_spec_id):
        """80mm diameter is above PAACS range (35-70mm)."""
        onion = _perfect_onion(diameter_mm=80.0)
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "NON_QUALIFYING"
        assert result.disqualifying_reasons == ["Bulb size 80.0mm outside allowable range (35–70mm)"]

    def test_cut_crack_always_fails(self, paacs_spec, paacs_spec_id):
        """Cut/crack is not allowed in either grade per NCCF."""
        onion = _perfect_onion()
        onion.cut_crack = True
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "NON_QUALIFYING"
        assert result.disqualifying_reasons == ["Cut / crack detected (disqualifies Grade A and URS)"]

    def test_eoi_spec_has_no_urs_grade(self, eoi_spec):
        """EOI spec: onion either Grade-A or Non-Qualifying (no URS)."""
        onion = _perfect_onion()
        onion.misshaped = True
        result = classify_onion(onion, eoi_spec, "NCCF_EOI_2026")
        assert result.grade == "NON_QUALIFYING"
        assert result.disqualifying_reasons == ["Double / misshaped detected (not allowed)"]

    def test_smut_within_grade_a_tolerance(self, paacs_spec, paacs_spec_id):
        """Smut ≤10% is allowed in Grade-A per PAACS."""
        onion = _perfect_onion()
        onion.smut_percentage = 8.0
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "GRADE_A"

    def test_smut_exceeds_grade_a_within_urs(self, paacs_spec, paacs_spec_id):
        """Smut 15% fails Grade-A (>10%) but passes URS (≤30%)."""
        onion = _perfect_onion()
        onion.smut_percentage = 15.0
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert result.grade == "GRADE_URS"
        assert result.disqualifying_reasons == ["Smut 15.0% exceeds Grade A limit (10%)"]

    def test_manual_inspection_flags_populated(self, paacs_spec, paacs_spec_id):
        """All undetectable features should be flagged for manual inspection."""
        onion = _perfect_onion()
        result = classify_onion(onion, paacs_spec, paacs_spec_id)
        assert "ruptured_skin" in result.manual_inspection_required
        assert "open_neck" in result.manual_inspection_required


# --- Batch grading tests -----------------------------------------------------

class TestGradeBatch:

    def test_batch_grade_percentages(self, paacs_spec, paacs_spec_id):
        """Verify correct batch-level percentages."""
        features = []
        # 68 perfect Grade-A onions
        for i in range(68):
            features.append(_perfect_onion(onion_id=i + 1))
        # 21 misshaped onions (Grade-URS in PAACS)
        for i in range(21):
            o = _perfect_onion(onion_id=68 + i + 1)
            o.misshaped = True
            features.append(o)
        # 11 sprouted onions (Non-Qualifying)
        for i in range(11):
            o = _perfect_onion(onion_id=89 + i + 1)
            o.sprouted = True
            features.append(o)

        result = grade_batch(features, paacs_spec, paacs_spec_id)
        assert result.total_onions == 100
        assert result.grade_a_count == 68
        assert result.grade_urs_count == 21
        assert result.non_qualifying_count == 11
        assert result.grade_a_pct == 68.0
        assert result.grade_urs_pct == 21.0
        assert result.non_qualifying_pct == 11.0

    def test_empty_batch(self, paacs_spec, paacs_spec_id):
        result = grade_batch([], paacs_spec, paacs_spec_id)
        assert result.total_onions == 0
        assert result.batch_grade == "NON_QUALIFYING"

    def test_batch_grade_majority_determines_assessment(self, paacs_spec, paacs_spec_id):
        """Batch with >50% Grade-A should have batch_grade GRADE_A."""
        features = [_perfect_onion(i) for i in range(10)]
        result = grade_batch(features, paacs_spec, paacs_spec_id)
        assert result.batch_grade == "GRADE_A"


# --- Feature extraction tests -----------------------------------------------

class TestExtractFeatures:

    def test_healthy_onion_detection(self):
        detections = [
            {"class_name": "onion", "class_id": 0, "confidence": 0.95,
             "bbox": [100, 100, 200, 200], "estimated_size_mm": 55.0},
        ]
        features = extract_features(detections)
        assert len(features) == 1
        assert features[0].diameter_mm == 55.0
        assert not features[0].sprouted
        assert not features[0].rotten
        assert not features[0].damaged

    def test_defect_associated_with_overlapping_onion(self):
        detections = [
            {"class_name": "onion", "class_id": 0, "confidence": 0.95,
             "bbox": [100, 100, 200, 200], "estimated_size_mm": 55.0},
            {"class_name": "sprouted", "class_id": 3, "confidence": 0.85,
             "bbox": [110, 110, 190, 190]},  # overlaps the onion
        ]
        features = extract_features(detections)
        assert len(features) == 1  # defect merged into the onion
        assert features[0].sprouted is True

    def test_rotten_and_damaged_feature_extraction(self):
        detections = [
            {"class_name": "onion", "class_id": 0, "confidence": 0.95,
             "bbox": [100, 100, 200, 200], "estimated_size_mm": 55.0},
            {"class_name": "rotten", "class_id": 2, "confidence": 0.88,
             "bbox": [105, 105, 150, 150]},
            {"class_name": "onion", "class_id": 0, "confidence": 0.92,
             "bbox": [300, 300, 400, 400], "estimated_size_mm": 50.0},
            {"class_name": "damaged", "class_id": 1, "confidence": 0.84,
             "bbox": [310, 310, 350, 350]},
        ]
        features = extract_features(detections)
        assert len(features) == 2
        assert features[0].rotten is True
        assert features[0].damaged is False
        assert features[1].rotten is False
        assert features[1].damaged is True

    def test_standalone_defect_creates_new_onion(self):
        detections = [
            {"class_name": "onion", "class_id": 0, "confidence": 0.95,
             "bbox": [100, 100, 200, 200]},
            {"class_name": "rotten", "class_id": 2, "confidence": 0.80,
             "bbox": [400, 400, 500, 500]},  # no overlap
        ]
        features = extract_features(detections)
        assert len(features) == 2

    def test_multiple_defects_on_one_onion(self):
        detections = [
            {"class_name": "onion", "class_id": 0, "confidence": 0.95,
             "bbox": [100, 100, 200, 200]},
            {"class_name": "smut", "class_id": 5, "confidence": 0.85,
             "bbox": [110, 110, 190, 190]},
            {"class_name": "discoloured", "class_id": 6, "confidence": 0.75,
             "bbox": [105, 105, 195, 195]},
        ]
        features = extract_features(detections)
        assert len(features) == 1
        assert features[0].smut_percentage > 0
        assert features[0].staining_percentage > 0


# --- Config loading tests ----------------------------------------------------

class TestConfigLoading:

    def test_specs_load_and_have_required_structure(self, specs):
        assert "specifications" in specs
        assert "active_specification" in specs
        assert "NCCF_PAACS_2026" in specs["specifications"]
        assert "NCCF_EOI_2026" in specs["specifications"]

    def test_paacs_has_urs_grade(self, paacs_spec):
        assert paacs_spec["has_urs_grade"] is True
        assert "grade_urs" in paacs_spec

    def test_eoi_has_no_urs_grade(self, eoi_spec):
        assert eoi_spec["has_urs_grade"] is False

    def test_size_ranges_match_documents(self, paacs_spec, eoi_spec):
        assert paacs_spec["size_range_mm"]["min"] == 35
        assert paacs_spec["size_range_mm"]["max"] == 70
        assert eoi_spec["size_range_mm"]["min"] == 45
        assert eoi_spec["size_range_mm"]["max"] == 65
