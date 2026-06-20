"""Image loading and saving utilities."""

from __future__ import annotations

import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIF_SUPPORTED = True
except ImportError:
    HEIF_SUPPORTED = False

from utils.exif import auto_orient_from_exif, transfer_exif


def load_image(path: Path) -> tuple[np.ndarray, Image.Image]:
    """Load image as BGR numpy array and RGB PIL image."""
    pil_img = Image.open(path)
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    pil_img = auto_orient_from_exif(pil_img, path)
    rgb = np.array(pil_img)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return bgr, pil_img


def bgr_to_pil(bgr: np.ndarray) -> Image.Image:
    """Convert BGR numpy array to PIL RGB image."""
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def save_image(
    bgr: np.ndarray,
    dest: Path,
    source_path: Path | None = None,
    quality: int = 95,
    keep_exif: bool = True,
) -> Path:
    """Save BGR image to file preserving format when possible."""
    pil_img = bgr_to_pil(bgr)
    dest.parent.mkdir(parents=True, exist_ok=True)
    suffix = dest.suffix.lower()

    if suffix in (".jpg", ".jpeg"):
        if keep_exif and source_path:
            data = transfer_exif(source_path, pil_img, quality=quality)
            dest.write_bytes(data)
        else:
            pil_img.save(dest, format="JPEG", quality=quality, optimize=True)
    elif suffix == ".png":
        pil_img.save(dest, format="PNG", optimize=True)
    elif suffix == ".webp":
        pil_img.save(dest, format="WEBP", quality=quality)
    elif suffix in (".tiff", ".tif"):
        pil_img.save(dest, format="TIFF")
    elif suffix == ".heic" and HEIF_SUPPORTED:
        pil_img.save(dest, format="HEIF", quality=quality)
    else:
        dest = dest.with_suffix(".jpg")
        if keep_exif and source_path:
            data = transfer_exif(source_path, pil_img, quality=quality)
            dest.write_bytes(data)
        else:
            pil_img.save(dest, format="JPEG", quality=quality, optimize=True)
    return dest


def resize_for_preview(bgr: np.ndarray, max_size: int = 1200) -> np.ndarray:
    """Resize image for preview while maintaining aspect ratio."""
    h, w = bgr.shape[:2]
    if max(h, w) <= max_size:
        return bgr
    scale = max_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)


def compute_histogram(bgr: np.ndarray) -> np.ndarray:
    """Compute RGB histogram visualization."""
    hist_img = np.zeros((200, 512, 3), dtype=np.uint8)
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    for i, color in enumerate(colors):
        hist = cv2.calcHist([bgr], [i], None, [256], [0, 256])
        cv2.normalize(hist, hist, 0, 199, cv2.NORM_MINMAX)
        for x in range(256):
            cv2.line(
                hist_img,
                (x * 2, 199),
                (x * 2, 199 - int(hist[x])),
                color,
                1,
            )
    return hist_img
