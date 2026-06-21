"""Processing stage base class and registry."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import ClassVar

from processing.context import ProcessingContext

logger = logging.getLogger("photo_enhancer.processing")


class ProcessingStage(ABC):
    """Independent, configurable processing step."""

    name: ClassVar[str] = "base"
    enabled: ClassVar[bool] = True

    @abstractmethod
    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        """Transform image in context and return updated context."""

    def is_enabled(self, ctx: ProcessingContext) -> bool:
        """Check if stage should run."""
        overrides = ctx.metadata.get("disabled_stages", set())
        return self.enabled and self.name not in overrides

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class StageRegistry:
    """Plugin registry for processing stages."""

    def __init__(self) -> None:
        self._stages: dict[str, ProcessingStage] = {}

    def register(self, stage: ProcessingStage) -> None:
        """Register a stage by name."""
        self._stages[stage.name] = stage
        logger.debug("Registered stage: %s", stage.name)

    def get(self, name: str) -> ProcessingStage | None:
        """Get stage by name."""
        return self._stages.get(name)

    def all(self) -> list[ProcessingStage]:
        """Return all registered stages."""
        return list(self._stages.values())

    def names(self) -> list[str]:
        """Return registered stage names."""
        return list(self._stages.keys())

    def build_sequence(self, names: list[str]) -> list[ProcessingStage]:
        """Build ordered stage list from names, skipping unknown."""
        sequence: list[ProcessingStage] = []
        for name in names:
            stage = self._stages.get(name)
            if stage is not None:
                sequence.append(stage)
            else:
                logger.warning("Unknown stage: %s", name)
        return sequence


from processing.defaults import get_default_stage_order
