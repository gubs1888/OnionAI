"""Grading engine unit tests — MVP logic must be config-driven and explainable."""

import pytest

from app.services.grading import GradingError, aggregate_counts, grade_batch, load_config


@pytest.fixture(scope="module")
def config():
    return load_config()


def _counts(**overrides):
    base = {
        "total_onions": 50,
        "healthy": 45,
        "damaged": 2,
        "rotten": 1,
        "sprouted": 1,
        "undersized": 1,
    }
    base.update(overrides)
    return base


def test_config_loads_and_has_required_sections(config):
    assert "mvp_scoring" in config
    assert "urs" in config
    assert "official_standards_TO_VERIFY" in config
    assert config["official_standards_TO_VERIFY"]["status"].startswith("NOT VERIFIED")
    weights = config["mvp_scoring"]["weights"]
    assert abs(weights["defect"] + weights["urs"] + weights["confidence"] - 1.0) < 1e-9


def test_grade_bounds_and_type(config):
    verdict = grade_batch(_counts(), 10.0, 0.9, config=config)
    assert 0 <= verdict["quality_score"] <= 100
    assert verdict["grade"] in ("A", "B", "C", "D")
    assert verdict["reasons"]


def test_worse_quality_gives_lower_score(config):
    good = grade_batch(_counts(healthy=49, damaged=0, rotten=0, sprouted=0, undersized=1),
                       urs_percentage=2.0, avg_confidence=0.95, config=config)
    bad = grade_batch(_counts(healthy=5, damaged=20, rotten=15, sprouted=5, undersized=5),
                      urs_percentage=30.0, avg_confidence=0.6, config=config)
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
    )
    counts = aggregate_counts(detections, config=config)
    assert sum(counts[k] for k in ("healthy", "damaged", "rotten", "sprouted", "undersized")) \
        == counts["total_onions"] == 14
    assert counts["undersized"] == 3
    assert counts["rotten"] == 1


def test_missing_config_fails_loudly(tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "grading_config_path", tmp_path / "missing.json")
    import app.services.grading as g
    g._load_cached.cache_clear()
    with pytest.raises(GradingError):
        g.load_config()
    g._load_cached.cache_clear()
