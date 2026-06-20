"""EXIF metadata handling."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import piexif
from PIL import Image


def read_exif_bytes(image_path: Path) -> bytes | None:
    """Read raw EXIF bytes from image file."""
    try:
        with Image.open(image_path) as img:
            if "exif" in img.info:
                return img.info["exif"]
    except Exception:
        return None
    return None


def transfer_exif(source_path: Path, dest_image: Image.Image, quality: int = 95) -> bytes:
    """Transfer EXIF from source to destination image bytes."""
    exif_bytes = read_exif_bytes(source_path)
    buffer = io.BytesIO()
    if exif_bytes:
        dest_image.save(buffer, format="JPEG", quality=quality, exif=exif_bytes)
    else:
        dest_image.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()


def get_orientation(image_path: Path) -> int:
    """Get EXIF orientation tag value."""
    exif_bytes = read_exif_bytes(image_path)
    if not exif_bytes:
        return 1
    try:
        exif_dict = piexif.load(exif_bytes)
        return exif_dict.get("0th", {}).get(piexif.ImageIFD.Orientation, 1)
    except Exception:
        return 1


def apply_orientation(image: Image.Image, orientation: int) -> Image.Image:
    """Apply EXIF orientation to PIL image."""
    transforms = {
        2: Image.Transpose.FLIP_LEFT_RIGHT,
        3: Image.Transpose.ROTATE_180,
        4: Image.Transpose.FLIP_TOP_BOTTOM,
        5: Image.Transpose.TRANSPOSE,
        6: Image.Transpose.ROTATE_270,
        7: Image.Transpose.TRANSVERSE,
        8: Image.Transpose.ROTATE_90,
    }
    if orientation in transforms:
        return image.transpose(transforms[orientation])
    return image


def auto_orient_from_exif(image: Image.Image, source_path: Path) -> Image.Image:
    """Auto-orient image based on EXIF data."""
    orientation = get_orientation(source_path)
    return apply_orientation(image, orientation)
