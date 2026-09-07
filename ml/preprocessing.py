"""
Image preprocessing for training + inference (TEAM A owns the real pipeline).

Planned real pipeline (keep in THIS file so training and serving match):
    1. EXIF-aware loading, RGB conversion
    2. resize (letterbox to 640) — matches YOLO11n
    3. optional: denoise / white-balance / background suppression
    4. dataset augmentation lives in train.py (Ultralytics aug params)

MVP: minimal, dependency-tolerant helpers (OpenCV preferred, Pillow fallback).
"""

from __future__ import annotations

from pathlib import Path

from ml.config import IMG_SIZE

try:                                   # OpenCV preferred
    import cv2
    import numpy as np

    HAS_CV2 = True
except ImportError:                    # Pillow fallback
    cv2 = None                         # type: ignore[assignment]
    np = None                          # type: ignore[assignment]
    HAS_CV2 = False


def load_rgb(image_path: str | Path):
    """Return an RGB image (numpy array with cv2, PIL.Image without)."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(path)
    if HAS_CV2:
        img = cv2.imread(str(path))
        if img is None:
            raise ValueError(f"Cannot decode image: {path.name}")
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    from PIL import Image
    return Image.open(path).convert("RGB")


def letterbox_resize(img, target: int = IMG_SIZE):
    """Resize keeping aspect ratio; pad to square (YOLO-style letterbox)."""
    if HAS_CV2:
        h, w = img.shape[:2]
        scale = target / max(h, w)
        nh, nw = int(h * scale), int(w * scale)
        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((target, target, 3), 114, dtype=img.dtype)
        top, left = (target - nh) // 2, (target - nw) // 2
        canvas[top:top + nh, left:left + nw] = resized
        return canvas
    from PIL import Image
    w, h = img.size
    scale = target / max(w, h)
    nw, nh = int(w * scale), int(h * scale)
    resized = img.resize((nw, nh))
    canvas = Image.new("RGB", (target, target), (114, 114, 114))
    canvas.paste(resized, ((target - nw) // 2, (target - nh) // 2))
    return canvas


def prepare(image_path: str | Path, target: int = IMG_SIZE):
    """Convenience: load + letterbox. Used by notebooks and future real serving."""
    return letterbox_resize(load_rgb(image_path), target)
