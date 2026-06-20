"""Tests for image enhancer."""

import numpy as np

from enhancer import ImageEnhancer
from styles.iphone import IPHONE_PRO


def test_enhancer_preserves_shape() -> None:
    enhancer = ImageEnhancer(IPHONE_PRO)
    bgr = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = enhancer.enhance(bgr)
    assert result.shape == bgr.shape
    assert result.dtype == np.uint8


def test_enhancer_output_range() -> None:
    enhancer = ImageEnhancer(IPHONE_PRO)
    bgr = np.random.randint(50, 200, (200, 300, 3), dtype=np.uint8)
    result = enhancer.enhance(bgr)
    assert result.min() >= 0
    assert result.max() <= 255


def test_enhancer_no_extreme_change() -> None:
    enhancer = ImageEnhancer(IPHONE_PRO)
    bgr = np.random.randint(80, 180, (100, 100, 3), dtype=np.uint8)
    result = enhancer.enhance(bgr)
    diff = np.abs(result.astype(float) - bgr.astype(float)).mean()
    assert diff < 65  # Natural enhancement, not extreme
