"""File and archive utilities."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path
from typing import Iterator

from config import get_config


def ensure_dir(path: Path) -> Path:
    """Create directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_supported_image(path: Path) -> bool:
    """Check if file extension is a supported image format."""
    config = get_config()
    return path.suffix.lower().lstrip(".") in config.supported_formats


def collect_images(directory: Path) -> list[Path]:
    """Collect all supported images recursively from directory."""
    images: list[Path] = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and is_supported_image(path):
            images.append(path)
    return images


def iter_images(directory: Path) -> Iterator[Path]:
    """Yield supported images from directory."""
    for path in sorted(directory.rglob("*")):
        if path.is_file() and is_supported_image(path):
            yield path


def extract_zip(zip_path: Path, dest: Path) -> Path:
    """Extract ZIP archive to destination directory."""
    ensure_dir(dest)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)
    return dest


def create_zip(source_dir: Path, zip_path: Path) -> Path:
    """Create ZIP archive from directory contents."""
    ensure_dir(zip_path.parent)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file():
                arcname = file_path.relative_to(source_dir).as_posix()
                zf.write(file_path, arcname)
    return zip_path


def copy_tree_structure(src_root: Path, dst_root: Path, rel_path: Path) -> Path:
    """Mirror relative path structure in destination."""
    target = dst_root / rel_path
    ensure_dir(target.parent)
    return target


def safe_remove(path: Path) -> None:
    """Remove file or directory safely."""
    if path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def get_output_folder_name(input_name: str, suffix: str | None = None) -> str:
    """Generate enhanced folder name."""
    config = get_config()
    sfx = suffix or config.paths.output_suffix
    base = input_name.rstrip("/\\")
    if base.lower().endswith(".zip"):
        base = Path(base).stem
    return f"{base}{sfx}"
