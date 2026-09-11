"""URS service tests — tests for both NCCF rule engine URS calculation and legacy formula."""

from app.services.grading import load_config
from app.services.nccf_rule_engine import BatchGradeResult
from app.services.urs import compute_urs, compute_urs_from_nccf


def test_compute_urs_from_nccf():
    batch_res = BatchGradeResult(
        total_onions=100,
        grade_a_count=70,
        grade_urs_count=20,
        non_qualifying_count=10,
        grade_a_pct=70.0,
        grade_urs_pct=20.0,
        non_qualifying_pct=10.0,
        batch_grade="GRADE_URS",
        specification_id="NCCF_PAACS_2026",
    )
    assert compute_urs_from_nccf(batch_res) == 20.0


def test_compute_urs_from_nccf_zero_total():
    batch_res = BatchGradeResult(
        total_onions=0,
        grade_a_count=0,
        grade_urs_count=0,
        non_qualifying_count=0,
        grade_a_pct=0.0,
        grade_urs_pct=0.0,
        non_qualifying_pct=0.0,
        batch_grade="NON_QUALIFYING",
        specification_id="NCCF_PAACS_2026",
    )
    assert compute_urs_from_nccf(batch_res) == 0.0


def test_urs_default_formula():
    config = load_config()
    counts = {
        "total_onions": 48,
        "healthy": 39,
        "damaged": 4,
        "rotten": 2,
        "sprouted": 1,
        "undersized": 2,
    }
    assert compute_urs(counts, config) == round((2 + 2 + 1) * 100.0 / 48, 1)


def test_urs_formula_is_configurable():
    config = load_config()
    config["urs"]["categories"] = ["rotten"]
    counts = {"total_onions": 10, "healthy": 9, "rotten": 1}
    assert compute_urs(counts, config) == 10.0


def test_urs_zero_total_is_zero():
    assert compute_urs({"total_onions": 0}, load_config()) == 0.0


def test_urs_unknown_category_counts_as_zero():
    config = load_config()
    config["urs"]["categories"] = ["not_a_bucket"]
    counts = {"total_onions": 10, "healthy": 10}
    assert compute_urs(counts, config) == 0.0
