"""URS service tests — the formula must come from config, not code."""

from app.services.grading import load_config
from app.services.urs import compute_urs


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
    # Default config: categories = undersized + rotten + sprouted = 5/48
    assert compute_urs(counts, config) == round((2 + 2 + 1) * 100.0 / 48, 1)


def test_urs_formula_is_configurable():
    config = load_config()
    # Change the definition in CONFIG ONLY — no code change.
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
