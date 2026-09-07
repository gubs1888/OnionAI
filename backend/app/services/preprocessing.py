"""
Image preprocessing helpers.

TEAM A owns the real pipeline (denoise, white-balance, background removal...).
For the MVP skeleton this module only guarantees: "give me a decoded image"
with a lazy Pillow import so the backend runs even without imaging libraries.
"""

from __future__ import annotations

from pathlib import Path

from app.config import settings

DEFAULT_MAX_SIDE = 640  # matches YOLO11n inference size


class PreprocessingError(RuntimeError):
    """Raised when an image cannot be decoded/prepared."""


def load_image(image_path: str | Path):
    """
    Decode an image file into a Pillow Image (RGB).

    DEMO MODE note: the demo inference path does NOT need this function
    (it works on raw bytes), so the app runs even without Pillow installed.
    The real YOLO path (TEAM A) should use it or replace it.
    """
    try:
        from PIL import Image as PILImage
    except ImportError as exc:  # pragma: no cover
        raise PreprocessingError(
            "Pillow is not installed — needed for real image preprocessing. "
            "This does not affect DEMO MODE."
        ) from exc

    path = Path(image_path)
    if not path.exists():
        raise PreprocessingError(f"Image not found: {path}")
    try:
        img = PILImage.open(path)
        return img.convert("RGB")
    except Exception as exc:
        raise PreprocessingError(f"Cannot decode image '{path.name}': {exc}") from exc


def resize_keep_aspect(img, max_side: int = DEFAULT_MAX_SIDE):
    """Resize so the longest side == max_side, preserving aspect ratio."""
    width, height = img.size
    scale = max_side / max(width, height)
    if scale >= 1.0:
        return img
    new_size = (int(width * scale), int(height * scale))
    # TODO(TEAM A): replace naive resize with the real preprocessing pipeline.
    return img.resize(new_size)


def prepare_for_inference(image_path: str | Path):
    """Convenience: load + resize. Returns (PIL.Image, original_size)."""
    img = load_image(image_path)
    original = img.size
    if settings.debug:
        print(f"[preprocessing] {Path(image_path).name}: {original} -> prepared")
    return resize_keep_aspect(img), original
