"""Preview canvas with zoom, pan, and before/after compare."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QPoint, QPointF, Qt, Signal
from PySide6.QtGui import QMouseEvent, QPainter, QPaintEvent, QWheelEvent
from PySide6.QtWidgets import QWidget

from utils.qt_image import numpy_bgr_to_qpixmap


class PreviewCanvas(QWidget):
    """Interactive image preview with compare slider."""

    compare_changed = Signal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._before: np.ndarray | None = None
        self._after: np.ndarray | None = None
        self._zoom = 1.0
        self._pan = QPointF(0, 0)
        self._compare = 0.5
        self._dragging = False
        self._panning = False
        self._last_pos = QPoint()
        self._mode = "compare"
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        self.setAcceptDrops(False)
        self.setStyleSheet("background: #0a0c10; border-radius: 8px;")

    def set_images(self, before: np.ndarray | None, after: np.ndarray | None) -> None:
        """Set before/after images."""
        self._before = before
        self._after = after if after is not None else before
        self._zoom = 1.0
        self._pan = QPointF(0, 0)
        self.update()

    def set_mode(self, mode: str) -> None:
        """Set view mode: compare, before, after."""
        self._mode = mode
        self.update()

    def set_compare(self, value: float) -> None:
        """Set compare slider position 0-1."""
        self._compare = max(0.0, min(1.0, value))
        self.update()

    def reset_view(self) -> None:
        """Reset zoom and pan."""
        self._zoom = 1.0
        self._pan = QPointF(0, 0)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)

        img = self._after if self._mode == "after" else self._before
        if self._mode == "compare" and self._before is not None and self._after is not None:
            self._paint_compare(painter)
            return
        if img is None:
            painter.setPen(Qt.GlobalColor.gray)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Drop photos or select a folder")
            return
        self._paint_single(painter, img)

    def _paint_single(self, painter: QPainter, bgr: np.ndarray) -> None:
        pix = numpy_bgr_to_qpixmap(bgr)
        self._draw_pixmap(painter, pix)

    def _paint_compare(self, painter: QPainter) -> None:
        assert self._before is not None and self._after is not None
        w, h = self.width(), self.height()
        split_x = int(w * self._compare)
        painter.save()
        painter.setClipRect(0, 0, split_x, h)
        self._draw_pixmap(painter, numpy_bgr_to_qpixmap(self._before))
        painter.restore()
        painter.save()
        painter.setClipRect(split_x, 0, w - split_x, h)
        self._draw_pixmap(painter, numpy_bgr_to_qpixmap(self._after))
        painter.restore()
        painter.setPen(Qt.GlobalColor.white)
        painter.drawLine(split_x, 0, split_x, h)

    def _draw_pixmap(self, painter: QPainter, pix) -> None:
        if pix.isNull():
            return
        avail = self.rect()
        scale = min(avail.width() / pix.width(), avail.height() / pix.height()) * self._zoom
        sw, sh = int(pix.width() * scale), int(pix.height() * scale)
        x = (avail.width() - sw) // 2 + int(self._pan.x())
        y = (avail.height() - sh) // 2 + int(self._pan.y())
        painter.drawPixmap(x, y, sw, sh, pix)

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9
        self._zoom = max(0.2, min(8.0, self._zoom * factor))
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._mode == "compare":
                self._dragging = True
            else:
                self._panning = True
            self._last_pos = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        if self._dragging and self._mode == "compare":
            self._compare = pos.x() / max(1, self.width())
            self.compare_changed.emit(self._compare)
            self.update()
        elif self._panning:
            delta = pos - self._last_pos
            self._pan += QPointF(delta.x(), delta.y())
            self._last_pos = pos
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging = False
        self._panning = False
