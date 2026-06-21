"""Application controller — UI-agnostic batch processing."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from pipeline import ProcessingOptions, ProcessingPipeline, ProcessingResult, ProgressInfo

logger = logging.getLogger("photo_enhancer.controller")


@dataclass
class ProjectHistoryEntry:
    """Recent project record."""

    name: str
    input_path: str
    output_path: str
    preset: str
    processed: int
    total: int
    timestamp: str


class BatchController:
    """Coordinates batch processing and project history."""

    HISTORY_FILE = "recent_projects.json"
    MAX_HISTORY = 20

    def __init__(self, history_dir: Path | None = None) -> None:
        self._history_dir = history_dir or Path.home() / ".photo_enhancer_pro"
        self._history_dir.mkdir(parents=True, exist_ok=True)
        self._pipeline: ProcessingPipeline | None = None
        self._last_result: ProcessingResult | None = None
        self._last_output: Path | None = None
        self._last_zip: Path | None = None

    @property
    def last_result(self) -> ProcessingResult | None:
        return self._last_result

    @property
    def last_output(self) -> Path | None:
        return self._last_output

    @property
    def last_zip(self) -> Path | None:
        return self._last_zip

    def create_pipeline(self, options: ProcessingOptions) -> ProcessingPipeline:
        """Create a new processing pipeline."""
        self._pipeline = ProcessingPipeline(options)
        return self._pipeline

    def cancel(self) -> None:
        """Cancel active pipeline."""
        if self._pipeline:
            self._pipeline.cancel()

    def record_result(
        self,
        result: ProcessingResult,
        input_path: Path,
        options: ProcessingOptions,
    ) -> None:
        """Store result and update history."""
        self._last_result = result
        self._last_output = result.output_folder
        self._last_zip = result.zip_path
        entry = ProjectHistoryEntry(
            name=input_path.stem,
            input_path=str(input_path),
            output_path=str(result.output_folder or ""),
            preset=options.preset_name,
            processed=result.processed,
            total=result.total,
            timestamp=datetime.now().isoformat(),
        )
        self._save_history_entry(entry)

    def load_history(self) -> list[ProjectHistoryEntry]:
        """Load recent projects."""
        path = self._history_dir / self.HISTORY_FILE
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [ProjectHistoryEntry(**item) for item in data]
        except Exception as exc:
            logger.warning("Failed to load history: %s", exc)
            return []

    def _save_history_entry(self, entry: ProjectHistoryEntry) -> None:
        history = self.load_history()
        history.insert(0, entry)
        history = history[: self.MAX_HISTORY]
        path = self._history_dir / self.HISTORY_FILE
        path.write_text(
            json.dumps([asdict(h) for h in history], indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def open_path(target: Path) -> bool:
        """Open folder or file in system explorer."""
        if not target.exists():
            return False
        path = str(target)
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
        return True

    @staticmethod
    def collect_input_paths(paths: list[str]) -> list[Path]:
        """Normalize drag-drop paths into processable inputs."""
        result: list[Path] = []
        for p in paths:
            path = Path(p)
            if path.is_dir() or path.suffix.lower() == ".zip":
                result.append(path)
            elif path.is_file() and path.suffix.lower().lstrip(".") in {
                "jpg", "jpeg", "png", "webp", "heic", "tiff", "tif"
            }:
                result.append(path)
        return result
