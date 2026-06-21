"""Configurable stage pipeline executor."""

from __future__ import annotations

import logging
import time
from typing import Callable

from processing.context import ProcessingContext
from processing.stages.base import ProcessingStage

logger = logging.getLogger("photo_enhancer.processing")


class StagePipeline:
    """Runs an ordered sequence of processing stages."""

    def __init__(
        self,
        stages: list[ProcessingStage],
        on_stage: Callable[[str, float], None] | None = None,
    ) -> None:
        self.stages = stages
        self._on_stage = on_stage

    def run(self, ctx: ProcessingContext) -> ProcessingContext:
        """Execute all enabled stages on context."""
        total = len(self.stages)
        for idx, stage in enumerate(self.stages):
            if not stage.is_enabled(ctx):
                continue
            t0 = time.perf_counter()
            ctx = stage.process(ctx)
            elapsed = time.perf_counter() - t0
            logger.debug("Stage %s completed in %.3fs", stage.name, elapsed)
            if self._on_stage:
                self._on_stage(stage.name, elapsed)
        return ctx
