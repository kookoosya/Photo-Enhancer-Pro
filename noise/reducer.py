"""Noise reduction module."""

from __future__ import annotations

import cv2
import numpy as np


def reduce_noise(
    bgr: np.ndarray,
    strength: float = 10.0,
    skin_mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    Apply adaptive noise reduction.

    Uses fastNlMeans for general denoising with reduced strength on skin.
    """
    strength = max(0.0, min(strength, 30.0))
    h = int(strength * 0.5)
    if h < 1:
        return bgr

    denoised = cv2.fastNlMeansDenoisingColored(
        bgr, None, h, h, 7, 21
    )

    if skin_mask is not None and skin_mask.max() > 0:
        mask = skin_mask.astype(np.float32)
        if mask.max() > 1:
            mask = mask / 255.0
        blend = 0.3
        mask_3 = np.stack([mask, mask, mask], axis=-1)
        result = bgr.astype(np.float32) * (mask_3 * blend) + denoised.astype(np.float32) * (
            1 - mask_3 * blend
        )
        return np.clip(result, 0, 255).astype(np.uint8)

    return denoised


def bilateral_smooth(bgr: np.ndarray, strength: float = 5.0) -> np.ndarray:
    """Light bilateral filter for noise without losing detail."""
    d = int(max(3, strength))
    sigma = strength * 2
    return cv2.bilateralFilter(bgr, d, sigma, sigma)
