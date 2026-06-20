"""Shared utilities for Photo Enhancer Pro."""

from utils.files import collect_images, create_zip, extract_zip, get_output_folder_name
from utils.hardware import get_system_info
from utils.image_io import load_image, save_image
from utils.quality import blur_score, quality_score

import logging
import sys
from datetime import datetime
from pathlib import Path

from config import get_config


def setup_logging(name: str = "photo_enhancer", level: int = logging.INFO) -> logging.Logger:
    """Configure application logger with file and console handlers."""
    config = get_config()
    logs_dir = config.logs_path
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / f"{name}_{datetime.now():%Y%m%d}.log"
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
