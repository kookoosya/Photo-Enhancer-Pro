"""GUI smoke tests."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from app.controller import BatchController
from ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_main_window_creates(qapp) -> None:
    window = MainWindow(BatchController())
    assert window.windowTitle() == "Photo Enhancer Pro"
    window.close()


def test_main_window_has_panels(qapp) -> None:
    window = MainWindow()
    assert hasattr(window, "_preview")
    assert hasattr(window, "_preset_combo")
    assert hasattr(window, "_progress")
    window.close()
