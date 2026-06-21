"""Application splash screen."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QColor, QLinearGradient
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class SplashScreen(QWidget):
    """Custom splash screen with branding."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(520, 320)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 30)
        title = QLabel("Photo Enhancer Pro")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #58a6ff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Professional iPhone-style photo enhancement")
        subtitle.setStyleSheet("color: #8b949e; font-size: 14px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(self._progress)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor("#0d1117"))
        grad.setColorAt(1, QColor("#161b22"))
        painter.fillRect(self.rect(), grad)
        painter.setPen(QColor("#30363d"))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 12, 12)

    def finish_loading(self) -> None:
        """Stop indeterminate progress."""
        self._progress.setRange(0, 100)
        self._progress.setValue(100)
