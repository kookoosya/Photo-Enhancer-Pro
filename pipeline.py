"""Batch processing pipeline."""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from config import get_config
from enhancer import ImageEnhancer
from styles import get_preset
from styles.base import EnhancementPreset
from utils.files import (
    collect_images,
    create_zip,
    ensure_dir,
    extract_zip,
    get_output_folder_name,
    is_supported_image,
)
from utils.image_io import load_image, resize_for_preview, save_image
from utils.quality import blur_score, find_duplicates, perceptual_hash, quality_score, rank_photos

logger = logging.getLogger("photo_enhancer.pipeline")


@dataclass
class ProcessingOptions:
    """Options for batch processing."""

    preset_name: str = "iphone_pro"
    output_dir: Path | None = None
    keep_exif: bool = True
    create_zip: bool = True
    overwrite_existing: bool = False
    resize: bool = False
    resize_max: int = 0
    upscale: bool = False
    upscale_scale: int = 2
    preview_before_save: bool = False
    duplicate_detection: bool = True
    blur_detection: bool = True
    best_photo_ranking: bool = True


@dataclass
class ProcessingResult:
    """Result of batch processing."""

    total: int = 0
    processed: int = 0
    failed: int = 0
    skipped: int = 0
    output_folder: Path | None = None
    zip_path: Path | None = None
    errors: list[str] = field(default_factory=list)
    duplicates: list[tuple[str, str]] = field(default_factory=list)
    blurry: list[str] = field(default_factory=list)
    rankings: list[tuple[str, float]] = field(default_factory=list)
    elapsed_seconds: float = 0.0


@dataclass
class ProgressInfo:
    """Progress update for UI callbacks."""

    current: int
    total: int
    filename: str
    elapsed: float
    estimated_remaining: float
    preview_before: np.ndarray | None = None
    preview_after: np.ndarray | None = None


def process_single_image(
    source_path: Path,
    dest_path: Path,
    preset: EnhancementPreset,
    options: ProcessingOptions,
) -> tuple[bool, str | None]:
    """Process a single image file."""
    try:
        if dest_path.exists() and not options.overwrite_existing:
            return True, None

        bgr, pil_img = load_image(source_path)
        enhancer = ImageEnhancer(preset)
        result = enhancer.enhance(bgr)

        if options.upscale:
            result = enhancer.upscale_if_requested(result, options.upscale_scale)

        if options.resize and options.resize_max > 0:
            h, w = result.shape[:2]
            if max(h, w) > options.resize_max:
                scale = options.resize_max / max(h, w)
                new_w, new_h = int(w * scale), int(h * scale)
                result = cv2.resize(result, (new_w, new_h), interpolation=cv2.INTER_AREA)

        save_image(
            result,
            dest_path,
            source_path=source_path,
            quality=get_config().processing.jpeg_quality,
            keep_exif=options.keep_exif,
        )
        return True, None
    except Exception as exc:
        logger.exception("Failed to process %s: %s", source_path, exc)
        return False, str(exc)


class ProcessingPipeline:
    """Orchestrates batch photo enhancement."""

    def __init__(self, options: ProcessingOptions | None = None) -> None:
        self.config = get_config()
        self.options = options or ProcessingOptions()
        self.preset = get_preset(self.options.preset_name)
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel ongoing processing."""
        self._cancelled = True

    def prepare_input(self, input_path: Path) -> tuple[Path, str]:
        """Prepare input: extract ZIP or use folder."""
        if input_path.suffix.lower() == ".zip":
            extract_dir = input_path.parent / f"{input_path.stem}_extracted"
            ensure_dir(extract_dir)
            extract_zip(input_path, extract_dir)
            return extract_dir, input_path.stem
        return input_path, input_path.name

    def get_output_path(self, input_name: str) -> Path:
        """Determine output directory."""
        if self.options.output_dir:
            base = self.options.output_dir
        else:
            base = Path.cwd()
        folder_name = get_output_folder_name(input_name)
        return ensure_dir(base / folder_name)

    def run(
        self,
        input_path: Path,
        progress_callback: Callable[[ProgressInfo], None] | None = None,
    ) -> ProcessingResult:
        """Run full batch processing pipeline."""
        start_time = time.time()
        result = ProcessingResult()
        self._cancelled = False

        source_dir, input_name = self.prepare_input(input_path)
        images = collect_images(source_dir)
        result.total = len(images)

        if not images:
            result.errors.append("No supported images found")
            return result

        output_dir = self.get_output_path(input_name)
        result.output_folder = output_dir

        hashes: dict[str, object] = {}
        quality_scores: dict[str, float] = {}
        blur_list: list[str] = []

        workers = min(self.config.processing.max_workers, len(images), 8)
        progress_lock = threading.Lock()
        completed_count = 0

        def process_one(idx: int, img_path: Path) -> tuple[int, Path, bool, str | None, object]:
            if self._cancelled:
                return idx, img_path, False, "cancelled", None
            rel_path = img_path.relative_to(source_dir)
            dest_path = output_dir / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            preview_before = None
            preview_after = None
            if progress_callback:
                try:
                    bgr_before, _ = load_image(img_path)
                    preview_before = resize_for_preview(
                        bgr_before, self.config.processing.preview_max_size
                    )
                except Exception:
                    pass
            success, error = process_single_image(
                img_path, dest_path, self.preset, self.options
            )
            if success and progress_callback and preview_before is not None:
                try:
                    bgr_after, _ = load_image(dest_path)
                    preview_after = resize_for_preview(
                        bgr_after, self.config.processing.preview_max_size
                    )
                except Exception:
                    pass
            return idx, img_path, success, error, (preview_before, preview_after)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(process_one, idx, img_path): (idx, img_path)
                for idx, img_path in enumerate(images)
            }
            for future in as_completed(futures):
                if self._cancelled:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                idx, img_path, success, error, previews = future.result()
                preview_before, preview_after = previews if previews else (None, None)

                if success:
                    if error is None:
                        result.processed += 1
                    else:
                        result.skipped += 1
                    if self.options.duplicate_detection or self.options.blur_detection:
                        try:
                            bgr, pil_img = load_image(img_path)
                            if self.options.duplicate_detection:
                                hashes[str(img_path)] = perceptual_hash(pil_img)
                            if self.options.blur_detection:
                                score = blur_score(bgr)
                                if score < 100:
                                    blur_list.append(str(img_path))
                            if self.options.best_photo_ranking:
                                quality_scores[str(img_path)] = quality_score(bgr)
                        except Exception:
                            pass
                else:
                    if error != "cancelled":
                        result.failed += 1
                        if error:
                            result.errors.append(f"{img_path.name}: {error}")

                with progress_lock:
                    completed_count += 1
                    elapsed = time.time() - start_time
                    avg_per_image = elapsed / completed_count
                    remaining = avg_per_image * (len(images) - completed_count)

                if progress_callback:
                    progress_callback(
                        ProgressInfo(
                            current=completed_count,
                            total=len(images),
                            filename=img_path.name,
                            elapsed=elapsed,
                            estimated_remaining=remaining,
                            preview_before=preview_before,
                            preview_after=preview_after,
                        )
                    )

        if self.options.duplicate_detection and hashes:
            hash_map = {k: v for k, v in hashes.items()}
            result.duplicates = find_duplicates(hash_map)

        result.blurry = blur_list
        if self.options.best_photo_ranking:
            result.rankings = rank_photos(quality_scores)

        if self.options.create_zip and result.processed > 0:
            zip_path = output_dir.parent / f"{output_dir.name}.zip"
            try:
                create_zip(output_dir, zip_path)
                result.zip_path = zip_path
            except Exception as exc:
                result.errors.append(f"ZIP creation failed: {exc}")

        result.elapsed_seconds = time.time() - start_time
        logger.info(
            "Processing complete: %d/%d processed, %d failed in %.1fs",
            result.processed,
            result.total,
            result.failed,
            result.elapsed_seconds,
        )
        return result
