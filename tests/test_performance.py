"""Performance benchmark tests."""

import time

import numpy as np
import pytest

from enhancer import ImageEnhancer
from styles.iphone import IPHONE_PRO


@pytest.mark.performance
def test_enhancer_performance_1080p() -> None:
    enhancer = ImageEnhancer(IPHONE_PRO)
    bgr = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    t0 = time.perf_counter()
    result = enhancer.enhance(bgr)
    elapsed = time.perf_counter() - t0
    assert result.shape == bgr.shape
    assert elapsed < 30.0, f"1080p enhancement took {elapsed:.2f}s"
