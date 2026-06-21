"""Background processing worker."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from app.controller import BatchController
from pipeline import ProcessingOptions, ProcessingPipeline, ProcessingResult, ProgressInfo


class PipelineWorker(QThread):
    """Runs ProcessingPipeline off the UI thread."""

    progress = Signal(object)  # ProgressInfo
    finished_ok = Signal(object)  # ProcessingResult
    failed = Signal(str)

    def __init__(
        self,
        input_path: Path,
        options: ProcessingOptions,
        controller: BatchController,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._input_path = input_path
        self._options = options
        self._controller = controller
        self._pipeline: ProcessingPipeline | None = None

    def run(self) -> None:
        """Execute batch processing."""
        try:
            self._pipeline = self._controller.create_pipeline(self._options)

            def callback(info: ProgressInfo) -> None:
                self.progress.emit(info)

            result = self._pipeline.run(self._input_path, progress_callback=callback)
            self._controller.record_result(result, self._input_path, self._options)
            self.finished_ok.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))

    def cancel(self) -> None:
        """Request pipeline cancellation."""
        self._controller.cancel()
