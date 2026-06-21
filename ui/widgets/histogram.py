"""Histogram widget."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

import cv2


class HistogramWidget(QWidget):
    """RGB histogram display."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._hist: np.ndarray | None = None
        self.setMinimumHeight(120)
        self.setStyleSheet("background: #12151c; border-radius: 6px;")

    def set_image(self, bgr: np.ndarray | None) -> None:
        """Compute and display histogram from BGR image."""
        if bgr is None:
            self._hist = None
            self.update()
            return
        hist_img = np.zeros((100, 256, 3), dtype=np.uint8)
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        for i, color in enumerate(colors):
            hist = cv2.calcHist([bgr], [i], None, [256], [0, 256])
            cv2.normalize(hist, hist, 0, 99, cv2.NORM_MINMAX)
            for x in range(256):
                cv2.line(hist_img, (x, 99), (x, 99 - int(hist[x])), color, 1)
        self._hist = hist_img
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        if self._hist is None:
            painter.setPen(Qt.GlobalColor.gray)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Histogram")
            return
        rgb = self._hist[:, :, ::-1].copy()
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        scaled = qimg.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawImage(x, y, scaled)
