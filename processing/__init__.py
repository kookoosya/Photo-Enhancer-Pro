"""Processing package — lazy exports."""

from processing.context import ProcessingContext
from processing.stage_pipeline import StagePipeline
from processing.stages.base import ProcessingStage

__all__ = ["ProcessingContext", "ProcessingStage", "StagePipeline"]
