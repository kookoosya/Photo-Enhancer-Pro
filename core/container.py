"""Dependency injection container."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from config import AppConfig, get_config
from processing.defaults import get_default_stage_order
from processing.stage_pipeline import StagePipeline
from processing.stages.base import StageRegistry
from processing.stages.color import (
    ColorBalanceStage,
    ExposureStage,
    LensCorrectionStage,
    SegmentationStage,
    WhiteBalanceStage,
)
from processing.stages.detail import (
    FinalOptimizationStage,
    NoiseReductionStage,
    RegionalEnhanceStage,
    SafetyBlendStage,
    SharpeningStage,
    TextureStage,
)
from processing.stages.tone import (
    DehazeStage,
    HighlightRecoveryStage,
    LocalContrastStage,
    MicroContrastStage,
    ShadowRecoveryStage,
    ToneMappingStage,
)
from segmentation.segmenter import SceneSegmenter
from styles.base import EnhancementPreset


@dataclass
class ServiceContainer:
    """Simple dependency injection container."""

    config: AppConfig = field(default_factory=get_config)
    _singletons: dict[str, Any] = field(default_factory=dict)
    _factories: dict[str, Callable[[], Any]] = field(default_factory=dict)

    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton service."""
        self._singletons[name] = instance

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """Register a factory for lazy instantiation."""
        self._factories[name] = factory

    def resolve(self, name: str) -> Any:
        """Resolve service by name."""
        if name in self._singletons:
            return self._singletons[name]
        if name in self._factories:
            instance = self._factories[name]()
            self._singletons[name] = instance
            return instance
        raise KeyError(f"Service not registered: {name}")

    def build_stage_registry(self) -> StageRegistry:
        """Build and populate the stage registry."""
        segmenter = self.resolve("segmenter")
        registry = StageRegistry()
        for stage in [
            SegmentationStage(segmenter),
            LensCorrectionStage(),
            WhiteBalanceStage(),
            ExposureStage(),
            HighlightRecoveryStage(),
            ShadowRecoveryStage(),
            ToneMappingStage(),
            LocalContrastStage(),
            MicroContrastStage(),
            TextureStage(),
            DehazeStage(),
            ColorBalanceStage(),
            RegionalEnhanceStage(),
            NoiseReductionStage(),
            SharpeningStage(),
            FinalOptimizationStage(),
            SafetyBlendStage(),
        ]:
            registry.register(stage)
        return registry

    def build_pipeline(
        self,
        preset: EnhancementPreset,
        stage_order: list[str] | None = None,
    ) -> StagePipeline:
        """Build configured stage pipeline."""
        registry = self.build_stage_registry()
        order = stage_order or get_default_stage_order()
        return StagePipeline(registry.build_sequence(order))


_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """Get or create global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer()
        _container.register_factory("segmenter", SceneSegmenter)
    return _container
