"""Grading engine unit tests — MVP logic + NCCF integration."""

import pytest

from app.services.grading import GradingError, aggregate_counts, grade_batch, load_config


@pytest.fixture(scope="module")
def config():
    return load_config()


def _counts(**overrides):
    base = {
        "total_onions": 50,
        "healthy": 40,
        "damaged": 2,
        "rotten": 1,
        "sprouted": 1,
        "undersized": 1,
        "cut_crack": 2,
        "smut": 1,
        "discoloured": 1,
        "fresh_roots": 1,
    }
    base.update(overrides)
    return base


def test_config_loads_and_has_required_sections(config):
    assert "mvp_scoring" in config
    assert "urs" in config
    weights = config["mvp_scoring"]["weights"]
    assert abs(weights["defect"] + weights["urs"] + weights["confidence"] - 1.0) < 1e-9


def test_grade_bounds_and_type(config):
    verdict = grade_batch(_counts(), 10.0, 0.9, config=config)
    assert 0 <= verdict["quality_score"] <= 100
    assert verdict["grade"] in ("A", "B", "C", "D")
    assert verdict["reasons"]


def test_worse_quality_gives_lower_score(config):
    good = grade_batch(
        _counts(healthy=49, damaged=0, rotten=0, sprouted=0, undersized=1,
                cut_crack=0, smut=0, discoloured=0, fresh_roots=0),
        urs_percentage=2.0, avg_confidence=0.95, config=config,
    )
    bad = grade_batch(
        _counts(healthy=5, damaged=10, rotten=10, sprouted=5, undersized=5,
                cut_crack=5, smut=5, discoloured=3, fresh_roots=2),
        urs_percentage=30.0, avg_confidence=0.6, config=config,
    )
    assert bad["quality_score"] < good["quality_score"]
    _rank = {"A": 0, "B": 1, "C": 2, "D": 3}
    assert _rank[bad["grade"]] > _rank[good["grade"]]  # D is worst


def test_grade_thresholds_respected(config):
    thresholds = config["mvp_scoring"]["grade_thresholds"]
    verdict = grade_batch(_counts(), 0.0, 0.99, config=config)
    expected = "D"
    for grade, minimum in sorted(thresholds.items(), key=lambda kv: kv[1], reverse=True):
        if verdict["quality_score"] >= minimum:
            expected = grade
            break
    assert verdict["grade"] == expected


def test_zero_onions_is_grade_d(config):
    verdict = grade_batch({"total_onions": 0}, 0.0, 0.0, config=config)
    assert verdict["grade"] == "D"
    assert verdict["quality_score"] == 0.0


def test_aggregate_counts_buckets_sum_to_total(config):
    detections = (
        [{"class_name": "onion", "estimated_size_mm": 60.0}] * 7
        + [{"class_name": "onion", "estimated_size_mm": 30.0}] * 3   # undersized
        + [{"class_name": "damaged"}] * 2
        + [{"class_name": "rotten"}] * 1
        + [{"class_name": "sprouted"}] * 1
        + [{"class_name": "cut_crack"}] * 1
        + [{"class_name": "smut"}] * 1
        + [{"class_name": "discoloured"}] * 1
        + [{"class_name": "fresh_roots"}] * 1
    )
    counts = aggregate_counts(detections, config=config)
    all_counted = sum(
        counts[k] for k in (
            "healthy", "damaged", "rotten", "sprouted", "undersized",
            "cut_crack", "smut", "discoloured", "fresh_roots",
        )
    )
    assert all_counted == counts["total_onions"] == 18
    assert counts["undersized"] == 3
    assert counts["rotten"] == 1
    assert counts["cut_crack"] == 1
    assert counts["smut"] == 1


def test_aggregate_counts_new_classes(config):
    """Verify the 4 new NCCF classes are counted correctly."""
    detections = (
        [{"class_name": "cut_crack"}] * 3
        + [{"class_name": "smut"}] * 2
        + [{"class_name": "discoloured"}] * 4
        + [{"class_name": "fresh_roots"}] * 1
        + [{"class_name": "onion", "estimated_size_mm": 55.0}] * 5
    )
    counts = aggregate_counts(detections, config=config)
    assert counts["cut_crack"] == 3
    assert counts["smut"] == 2
    assert counts["discoloured"] == 4
    assert counts["fresh_roots"] == 1
    assert counts["healthy"] == 5
    assert counts["total_onions"] == 15


def test_missing_config_fails_loudly(tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "grading_config_path", tmp_path / "missing.json")
    import app.services.grading as g
    g._load_cached.cache_clear()
    with pytest.raises(GradingError):
        g.load_config()
    g._load_cached.cache_clear()
