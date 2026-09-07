"""OnionDetector interface tests — must work with ZERO heavy deps (demo mode)."""

from pathlib import Path

from ml.inference import OnionDetector, ModelNotAvailableError

FAKE_IMAGE_BYTES = b"\xff\xd8\xff\xe0" + b"ml-contract-test-image" * 128


def _tmp_image(tmp_path: Path, name: str = "img.jpg") -> Path:
    p = tmp_path / name
    p.write_bytes(FAKE_IMAGE_BYTES)
    return p


def test_detector_falls_back_to_demo(tmp_path):
    """No model file + allow_demo=True => demo mode, still a working detector."""
    detector = OnionDetector(allow_demo=True)  # repo has no onion_yolo.pt yet
    result = detector.detect(_tmp_image(tmp_path))
    assert detector.is_demo is True
    assert result["is_demo"] is True
    assert result["model_version"] == "demo-v0"
    assert "DEMO" in result["note"].upper()


def test_detector_without_demo_raises(tmp_path):
    import pytest

    with pytest.raises(ModelNotAvailableError):
        OnionDetector(model_path=tmp_path / "missing.pt", allow_demo=False)


def test_demo_is_deterministic(tmp_path):
    detector = OnionDetector(allow_demo=True)
    img = _tmp_image(tmp_path)
    r1 = detector.detect(img)
    r2 = detector.detect(img)
    assert r1["detections"] == r2["detections"]


def test_different_images_give_different_demo_results(tmp_path):
    detector = OnionDetector(allow_demo=True)
    a = tmp_path / "a.jpg"; a.write_bytes(b"image-A" * 500)
    b = tmp_path / "b.jpg"; b.write_bytes(b"image-B" * 500)
    # 10-60 random detections each: collision probability is negligible.
    assert detector.detect(a)["detections"] != detector.detect(b)["detections"]


def test_missing_image_raises(tmp_path):
    detector = OnionDetector(allow_demo=True)
    import pytest
    with pytest.raises(FileNotFoundError):
        detector.detect(tmp_path / "nope.jpg")
