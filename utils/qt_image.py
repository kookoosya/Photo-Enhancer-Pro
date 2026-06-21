"""Qt image conversion utilities."""

from __future__ import annotations

import numpy as np
from PySide6.QtGui import QImage, QPixmap


def numpy_bgr_to_qimage(bgr: np.ndarray) -> QImage:
    """Convert BGR numpy array to QImage (RGB)."""
    if bgr is None or bgr.size == 0:
        return QImage()
    rgb = bgr[:, :, ::-1].copy()
    h, w, ch = rgb.shape
    bytes_per_line = ch * w
    return QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()


def numpy_bgr_to_qpixmap(bgr: np.ndarray) -> QPixmap:
    """Convert BGR numpy array to QPixmap."""
    return QPixmap.fromImage(numpy_bgr_to_qimage(bgr))


def numpy_rgb_to_qpixmap(rgb: np.ndarray) -> QPixmap:
    """Convert RGB numpy array to QPixmap."""
    if rgb is None or rgb.size == 0:
        return QPixmap()
    img = rgb.copy()
    h, w, ch = img.shape
    bytes_per_line = ch * w
    qimg = QImage(img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
    return QPixmap.fromImage(qimg)
