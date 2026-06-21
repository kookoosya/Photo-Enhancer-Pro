"""PySide6 application bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.controller import BatchController
from ui.main_window import MainWindow
from ui.splash import SplashScreen
from utils import setup_logging


def _load_stylesheet() -> str:
    qss_path = Path(__file__).parent / "styles" / "dark.qss"
    return qss_path.read_text(encoding="utf-8")


def _create_icon() -> QIcon:
    """Create application icon programmatically."""
    from PySide6.QtGui import QPixmap, QPainter, QColor

    pix = QPixmap(64, 64)
    pix.fill(QColor("#0d1117"))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#58a6ff"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(8, 8, 48, 48, 12, 12)
    painter.setBrush(QColor("#238636"))
    painter.drawEllipse(20, 20, 24, 24)
    painter.end()
    return QIcon(pix)


def run_app() -> int:
    """Launch the native desktop application."""
    setup_logging()
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Photo Enhancer Pro")
    app.setOrganizationName("PhotoEnhancerPro")
    app.setStyleSheet(_load_stylesheet())
    app.setWindowIcon(_create_icon())

    splash = SplashScreen()
    splash.show()
    app.processEvents()

    controller = BatchController()
    window = MainWindow(controller)
    splash.finish_loading()
    splash.close()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_app())
