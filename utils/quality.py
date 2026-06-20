"""Image quality analysis utilities."""

from __future__ import annotations

import cv2
import imagehash
import numpy as np
from PIL import Image


def blur_score(bgr: np.ndarray) -> float:
    """Compute blur score using Laplacian variance. Higher = sharper."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_blurry(bgr: np.ndarray, threshold: float = 100.0) -> bool:
    """Determine if image is blurry."""
    return blur_score(bgr) < threshold


def perceptual_hash(pil_img: Image.Image) -> imagehash.ImageHash:
    """Compute perceptual hash for duplicate detection."""
    return imagehash.phash(pil_img)


def hash_distance(h1: imagehash.ImageHash, h2: imagehash.ImageHash) -> int:
    """Hamming distance between two perceptual hashes."""
    return h1 - h2


def quality_score(bgr: np.ndarray) -> float:
    """Composite quality score for ranking best photos."""
    blur = blur_score(bgr)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    contrast = float(gray.std())
    brightness = float(gray.mean())
    brightness_penalty = abs(brightness - 128) / 128
    return blur * 0.5 + contrast * 2.0 - brightness_penalty * 50


def find_duplicates(
  hashes: dict[str, imagehash.ImageHash],
  threshold: int = 5,
) -> list[tuple[str, str]]:
    """Find duplicate image pairs by hash distance."""
    paths = list(hashes.keys())
    duplicates: list[tuple[str, str]] = []
    for i, p1 in enumerate(paths):
        for p2 in paths[i + 1:]:
            if hash_distance(hashes[p1], hashes[p2]) <= threshold:
                duplicates.append((p1, p2))
    return duplicates


def rank_photos(scores: dict[str, float]) -> list[tuple[str, float]]:
    """Rank photos by quality score descending."""
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
