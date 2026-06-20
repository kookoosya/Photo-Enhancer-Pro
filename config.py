"""Application configuration management."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config.json"


@dataclass
class ProcessingConfig:
    """Processing-related settings."""

    max_workers: int = 4
    use_gpu: bool = True
    chunk_size: int = 10
    jpeg_quality: int = 95
    preview_max_size: int = 1200


@dataclass
class PathConfig:
    """Path-related settings."""

    models_dir: str = "models"
    logs_dir: str = "logs"
    output_suffix: str = "_Enhanced"


@dataclass
class FeatureConfig:
    """Feature toggle settings."""

    keep_exif: bool = True
    create_zip: bool = True
    overwrite_existing: bool = False
    preview_before_save: bool = False
    duplicate_detection: bool = True
    blur_detection: bool = True
    best_photo_ranking: bool = True


@dataclass
class SegmentationConfig:
    """Segmentation model settings."""

    use_yolo: bool = False
    use_sam: bool = False
    fallback_color_based: bool = True


@dataclass
class UpscaleConfig:
    """Upscale settings."""

    enabled: bool = False
    scale: int = 2
    model: str = "realesrgan"


@dataclass
class AppConfig:
    """Root application configuration."""

    app_name: str = "Photo Enhancer Pro"
    version: str = "1.0.0"
    default_preset: str = "iphone_pro"
    supported_formats: list[str] = field(
        default_factory=lambda: ["jpg", "jpeg", "png", "webp", "heic", "tiff", "tif"]
    )
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    segmentation: SegmentationConfig = field(default_factory=SegmentationConfig)
    upscale: UpscaleConfig = field(default_factory=UpscaleConfig)

    @property
    def models_path(self) -> Path:
        return PROJECT_ROOT / self.paths.models_dir

    @property
    def logs_path(self) -> Path:
        return PROJECT_ROOT / self.paths.logs_dir


def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: Path | None = None) -> AppConfig:
    """Load configuration from JSON file with defaults."""
    config_path = path or CONFIG_PATH
    data: dict[str, Any] = {}
    if config_path.exists():
        with config_path.open(encoding="utf-8") as fh:
            data = json.load(fh)

    return AppConfig(
        app_name=data.get("app_name", "Photo Enhancer Pro"),
        version=data.get("version", "1.0.0"),
        default_preset=data.get("default_preset", "iphone_pro"),
        supported_formats=data.get(
            "supported_formats",
            ["jpg", "jpeg", "png", "webp", "heic", "tiff", "tif"],
        ),
        processing=ProcessingConfig(**data.get("processing", {})),
        paths=PathConfig(**data.get("paths", {})),
        features=FeatureConfig(**data.get("features", {})),
        segmentation=SegmentationConfig(**data.get("segmentation", {})),
        upscale=UpscaleConfig(**data.get("upscale", {})),
    )


def save_config(config: AppConfig, path: Path | None = None) -> None:
    """Persist configuration to JSON file."""
    config_path = path or CONFIG_PATH
    payload = {
        "app_name": config.app_name,
        "version": config.version,
        "default_preset": config.default_preset,
        "supported_formats": config.supported_formats,
        "processing": {
            "max_workers": config.processing.max_workers,
            "use_gpu": config.processing.use_gpu,
            "chunk_size": config.processing.chunk_size,
            "jpeg_quality": config.processing.jpeg_quality,
            "preview_max_size": config.processing.preview_max_size,
        },
        "paths": {
            "models_dir": config.paths.models_dir,
            "logs_dir": config.paths.logs_dir,
            "output_suffix": config.paths.output_suffix,
        },
        "features": {
            "keep_exif": config.features.keep_exif,
            "create_zip": config.features.create_zip,
            "overwrite_existing": config.features.overwrite_existing,
            "preview_before_save": config.features.preview_before_save,
            "duplicate_detection": config.features.duplicate_detection,
            "blur_detection": config.features.blur_detection,
            "best_photo_ranking": config.features.best_photo_ranking,
        },
        "segmentation": {
            "use_yolo": config.segmentation.use_yolo,
            "use_sam": config.segmentation.use_sam,
            "fallback_color_based": config.segmentation.fallback_color_based,
        },
        "upscale": {
            "enabled": config.upscale.enabled,
            "scale": config.upscale.scale,
            "model": config.upscale.model,
        },
    }
    with config_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


# Global singleton
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get or load global configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
