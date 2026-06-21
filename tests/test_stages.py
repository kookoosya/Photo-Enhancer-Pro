"""Tests for processing stage pipeline."""

import numpy as np

from core.container import get_container
from processing.context import ProcessingContext
from processing.defaults import get_default_stage_order
from styles.iphone import IPHONE_PRO


def test_default_stage_order_count() -> None:
    order = get_default_stage_order()
    assert len(order) == 17
    assert order[0] == "segmentation"
    assert order[-1] == "safety_blend"


def test_stage_pipeline_runs() -> None:
    container = get_container()
    pipeline = container.build_pipeline(IPHONE_PRO)
    bgr = np.random.randint(50, 200, (200, 300, 3), dtype=np.uint8)
    ctx = ProcessingContext(image=bgr.copy(), original=bgr.copy(), preset=IPHONE_PRO)
    result = pipeline.run(ctx)
    assert result.bgr.shape == bgr.shape
    assert result.masks is not None


def test_stage_registry_names() -> None:
    container = get_container()
    registry = container.build_stage_registry()
    names = registry.names()
    for name in get_default_stage_order():
        assert name in names
