"""Loading spinner widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget


class LoadingSpinner(QWidget):
    """Animated loading indicator."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self.setFixedSize(48, 48)
        self.hide()

    def start(self) -> None:
        self._timer.start(50)
        self.show()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _rotate(self) -> None:
        self._angle = (self._angle + 30) % 360
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)
        for i in range(12):
            painter.setOpacity(1.0 - i * 0.07)
            painter.setBrush(QColor("#58a6ff"))
            painter.drawRoundedRect(-3, -18, 6, 10, 2, 2)
            painter.rotate(30)
