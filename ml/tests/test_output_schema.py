"""Output schema tests — the ML -> Backend contract must never drift."""

from pathlib import Path

from ml.config import CLASS_NAMES
from ml.inference import OnionDetector

ALLOWED_CLASSES = set(CLASS_NAMES.values())


def _detections(tmp_path: Path) -> list[dict]:
    img = tmp_path / "x.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0schema-test" * 200)
    return OnionDetector(model_path=tmp_path / "missing.pt", allow_demo=True).detect(img)["detections"]


def test_contract_keys(tmp_path):
    detections = _detections(tmp_path)
    assert len(detections) > 0, "demo mode must always produce detections"
    for det in detections:
        assert set(det.keys()) == {"class_name", "class_id", "confidence", "bbox"}


def test_class_ids_match_config(tmp_path):
    for det in _detections(tmp_path):
        assert det["class_name"] in ALLOWED_CLASSES
        assert det["class_id"] in CLASS_NAMES
        assert CLASS_NAMES[det["class_id"]] == det["class_name"]


def test_confidence_range(tmp_path):
    for det in _detections(tmp_path):
        assert 0.0 <= det["confidence"] <= 1.0


def test_bbox_structure(tmp_path):
    for det in _detections(tmp_path):
        x1, y1, x2, y2 = det["bbox"]
        assert x2 > x1 and y2 > y1
        assert all(isinstance(v, (int, float)) for v in det["bbox"])


def test_top_level_contract_keys(tmp_path):
    img = tmp_path / "y.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0top-level" * 100)
    result = OnionDetector(model_path=tmp_path / "missing.pt", allow_demo=True).detect(img)
    assert {"detections", "model_version", "is_demo", "inference_ms"} <= set(result.keys())
    assert isinstance(result["is_demo"], bool)
    assert isinstance(result["inference_ms"], (int, float))


def test_real_model_output_schema():
    sample_img = Path("docs/demo/sample_images/sample_onions_01.jpg")
    if sample_img.exists():
        result = OnionDetector(allow_demo=False).detect(sample_img)
        assert {"detections", "model_version", "is_demo", "inference_ms"} <= set(result.keys())
        assert result["is_demo"] is False
        for det in result["detections"]:
            assert set(det.keys()) == {"class_name", "class_id", "confidence", "bbox"}
