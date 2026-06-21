"""Core image enhancement engine — stage-based pipeline."""

from __future__ import annotations

import logging

import numpy as np

from core.container import get_container
from processing.context import ProcessingContext
from segmentation.segmenter import SceneMasks
from styles.base import EnhancementPreset
from upscale.upscaler import upscale_image

logger = logging.getLogger("photo_enhancer.enhancer")


class ImageEnhancer:
    """Production image enhancer using configurable ProcessingStage pipeline."""

    def __init__(
        self,
        preset: EnhancementPreset,
        stage_order: list[str] | None = None,
    ) -> None:
        self.preset = preset
        self._container = get_container()
        config = self._container.config
        order = stage_order or config.pipeline_stages or None
        self._pipeline = self._container.build_pipeline(preset, order)

    def enhance(self, bgr: np.ndarray, masks: SceneMasks | None = None) -> np.ndarray:
        """Run full enhancement pipeline on BGR image."""
        ctx = ProcessingContext(
            image=bgr.copy(),
            original=bgr.copy(),
            preset=self.preset,
            masks=masks,
        )
        ctx = self._pipeline.run(ctx)
        return ctx.bgr

    def upscale_if_requested(self, bgr: np.ndarray, scale: int, use_ai: bool = False) -> np.ndarray:
        """Optional upscaling."""
        return upscale_image(bgr, scale=scale, use_ai=use_ai)
