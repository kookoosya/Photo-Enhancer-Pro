"""Tests for quality utilities."""

import numpy as np

from utils.quality import blur_score, is_blurry, quality_score


def test_blur_score_sharp_vs_blurry() -> None:
    sharp = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    blurry = np.full((200, 200, 3), 128, dtype=np.uint8)
    assert blur_score(sharp) > blur_score(blurry)


def test_is_blurry() -> None:
    uniform = np.full((100, 100, 3), 100, dtype=np.uint8)
    assert is_blurry(uniform) is True


def test_quality_score_positive() -> None:
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    score = quality_score(img)
    assert score > 0
