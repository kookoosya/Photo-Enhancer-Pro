"""Processing context shared across pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from styles.base import EnhancementPreset

if TYPE_CHECKING:
    from segmentation.segmenter import SceneMasks


@dataclass
class ProcessingContext:
    """Mutable state passed through processing stages."""

    image: np.ndarray
    original: np.ndarray
    preset: EnhancementPreset
    masks: SceneMasks | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def bgr(self) -> np.ndarray:
        """Current BGR image."""
        return self.image

    @bgr.setter
    def bgr(self, value: np.ndarray) -> None:
        self.image = value
