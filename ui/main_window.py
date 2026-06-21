"""Main application window."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.controller import BatchController
from app.workers.pipeline_worker import PipelineWorker
from config import get_config
from pipeline import ProcessingOptions, ProcessingResult, ProgressInfo
from styles import list_presets
from ui.widgets.histogram import HistogramWidget
from ui.widgets.loading_spinner import LoadingSpinner
from ui.widgets.preview_canvas import PreviewCanvas
from utils.hardware import get_gpu_usage, get_system_info
from utils.image_io import load_image

logger = logging.getLogger("photo_enhancer.ui")


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self, controller: BatchController | None = None) -> None:
        super().__init__()
        self._config = get_config()
        self._controller = controller or BatchController()
        self._worker: PipelineWorker | None = None
        self._input_path: Path | None = None
        self._current_before: np.ndarray | None = None
        self._current_after: np.ndarray | None = None

        self.setWindowTitle("Photo Enhancer Pro")
        self.setMinimumSize(1280, 800)
        self.resize(1440, 900)
        self.setAcceptDrops(True)

        self._build_menus()
        self._build_toolbar()
        self._build_ui()
        self._build_status_bar()
        self._setup_shortcuts()
        self._load_history()
        self._start_monitor_timer()

    def _build_menus(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        open_folder = QAction("Open &Folder...", self)
        open_folder.triggered.connect(self._browse_folder)
        open_zip = QAction("Open &ZIP...", self)
        open_zip.triggered.connect(self._browse_zip)
        file_menu.addAction(open_folder)
        file_menu.addAction(open_zip)
        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        process_menu = menu.addMenu("&Process")
        start_action = QAction("&Start Processing", self)
        start_action.setShortcut("Ctrl+Return")
        start_action.triggered.connect(self._start_processing)
        cancel_action = QAction("&Cancel", self)
        cancel_action.setShortcut("Escape")
        cancel_action.triggered.connect(self._cancel_processing)
        process_menu.addAction(start_action)
        process_menu.addAction(cancel_action)

        view_menu = menu.addMenu("&View")
        for mode, label in [("compare", "Compare"), ("before", "Before"), ("after", "After")]:
            action = QAction(label, self)
            action.triggered.connect(lambda checked=False, m=mode: self._preview.set_mode(m))
            view_menu.addAction(action)

        help_menu = menu.addMenu("&Help")
        about = QAction("&About", self)
        about.triggered.connect(self._show_about)
        help_menu.addAction(about)

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)
        tb.addAction("Open Folder", self._browse_folder)
        tb.addAction("Open ZIP", self._browse_zip)
        tb.addAction("Start", self._start_processing)
        tb.addAction("Cancel", self._cancel_processing)
        tb.addSeparator()
        tb.addAction("Open Output", self._open_output)
        tb.addAction("Open ZIP", self._open_zip)

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter)

        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_center_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([280, 760, 300])

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        title = QLabel("Project")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self._input_edit = QLineEdit()
        self._input_edit.setPlaceholderText("Folder or ZIP path...")
        layout.addWidget(self._input_edit)

        btn_row = QHBoxLayout()
        folder_btn = QPushButton("Folder")
        folder_btn.clicked.connect(self._browse_folder)
        zip_btn = QPushButton("ZIP")
        zip_btn.clicked.connect(self._browse_zip)
        btn_row.addWidget(folder_btn)
        btn_row.addWidget(zip_btn)
        layout.addLayout(btn_row)

        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("Output folder (optional)")
        layout.addWidget(QLabel("Output"))
        layout.addWidget(self._output_edit)

        settings = QGroupBox("Settings")
        s_layout = QVBoxLayout(settings)
        self._keep_exif = QCheckBox("Keep EXIF")
        self._keep_exif.setChecked(True)
        self._create_zip = QCheckBox("Create ZIP")
        self._create_zip.setChecked(True)
        self._overwrite = QCheckBox("Overwrite Existing")
        self._resize = QCheckBox("Resize")
        self._upscale = QCheckBox("Upscale")
        self._dup_det = QCheckBox("Duplicate Detection")
        self._dup_det.setChecked(True)
        self._blur_det = QCheckBox("Blur Detection")
        self._blur_det.setChecked(True)
        for cb in [self._keep_exif, self._create_zip, self._overwrite,
                   self._resize, self._upscale, self._dup_det, self._blur_det]:
            s_layout.addWidget(cb)
        layout.addWidget(settings)

        history_box = QGroupBox("History")
        h_layout = QVBoxLayout(history_box)
        self._history_list = QListWidget()
        self._history_list.itemDoubleClicked.connect(self._open_history_item)
        h_layout.addWidget(self._history_list)
        layout.addWidget(history_box, 1)

        self._start_btn = QPushButton("Start Processing")
        self._start_btn.setObjectName("primaryButton")
        self._start_btn.clicked.connect(self._start_processing)
        layout.addWidget(self._start_btn)
        return panel

    def _build_center_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        self._preview = PreviewCanvas()

        toolbar = QHBoxLayout()
        self._compare_slider = QSlider(Qt.Orientation.Horizontal)
        self._compare_slider.setRange(0, 100)
        self._compare_slider.setValue(50)
        self._compare_slider.valueChanged.connect(
            lambda v: self._preview.set_compare(v / 100.0)
        )
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self._preview.reset_view)
        toolbar.addWidget(QLabel("Compare"))
        toolbar.addWidget(self._compare_slider, 1)
        toolbar.addWidget(reset_btn)
        layout.addLayout(toolbar)

        preview_container = QWidget()
        pv_layout = QVBoxLayout(preview_container)
        pv_layout.setContentsMargins(0, 0, 0, 0)
        self._spinner = LoadingSpinner(self._preview)
        pv_layout.addWidget(self._preview)
        layout.addWidget(preview_container, 1)

        bottom = QHBoxLayout()
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._eta_label = QLabel("Ready")
        self._file_label = QLabel("")
        bottom.addWidget(self._progress, 1)
        bottom.addWidget(self._eta_label)
        layout.addLayout(bottom)
        layout.addWidget(self._file_label)
        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        title = QLabel("Preset")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self._preset_combo = QComboBox()
        for name in list_presets():
            self._preset_combo.addItem(name.replace("_", " ").title(), name)
        layout.addWidget(self._preset_combo)

        info_box = QGroupBox("Image Info")
        info_layout = QFormLayout(info_box)
        self._info_name = QLabel("—")
        self._info_size = QLabel("—")
        self._info_format = QLabel("—")
        info_layout.addRow("File:", self._info_name)
        info_layout.addRow("Size:", self._info_size)
        info_layout.addRow("Format:", self._info_format)
        layout.addWidget(info_box)

        layout.addWidget(QLabel("Histogram"))
        self._histogram = HistogramWidget()
        layout.addWidget(self._histogram)

        queue_box = QGroupBox("Queue")
        q_layout = QVBoxLayout(queue_box)
        self._queue_list = QListWidget()
        q_layout.addWidget(self._queue_list)
        layout.addWidget(queue_box, 1)
        return panel

    def _build_status_bar(self) -> None:
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_gpu = QLabel("GPU: —")
        self._status_ram = QLabel("RAM: —")
        sb.addPermanentWidget(self._status_gpu)
        sb.addPermanentWidget(self._status_ram)
        sb.showMessage("Ready")

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+O"), self, self._browse_folder)
        QShortcut(QKeySequence("Ctrl+R"), self, self._preview.reset_view)

    def _start_monitor_timer(self) -> None:
        self._monitor = QTimer(self)
        self._monitor.timeout.connect(self._update_system_stats)
        self._monitor.start(2000)
        self._update_system_stats()

    def _update_system_stats(self) -> None:
        info = get_system_info()
        gpu = get_gpu_usage()
        self._status_gpu.setText(
            f"GPU: {info.gpu_name or 'CPU'} ({gpu['memory_percent']:.0f}%)"
        )
        self._status_ram.setText(f"RAM: {info.memory_gb:.1f} GB free")

    def _load_history(self) -> None:
        self._history_list.clear()
        for entry in self._controller.load_history():
            item = QListWidgetItem(
                f"{entry.name} — {entry.processed}/{entry.total} ({entry.preset})"
            )
            item.setData(Qt.ItemDataRole.UserRole, entry.input_path)
            self._history_list.addItem(item)

    def _open_history_item(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self._input_edit.setText(path)
            self._input_path = Path(path)

    def _browse_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if path:
            self._set_input(Path(path))

    def _browse_zip(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select ZIP", "", "ZIP (*.zip)")
        if path:
            self._set_input(Path(path))

    def _set_input(self, path: Path) -> None:
        self._input_path = path
        self._input_edit.setText(str(path))
        self.statusBar().showMessage(f"Input: {path.name}")

    def _build_options(self) -> ProcessingOptions:
        return ProcessingOptions(
            preset_name=self._preset_combo.currentData(),
            output_dir=Path(self._output_edit.text()) if self._output_edit.text() else None,
            keep_exif=self._keep_exif.isChecked(),
            create_zip=self._create_zip.isChecked(),
            overwrite_existing=self._overwrite.isChecked(),
            resize=self._resize.isChecked(),
            upscale=self._upscale.isChecked(),
            duplicate_detection=self._dup_det.isChecked(),
            blur_detection=self._blur_det.isChecked(),
        )

    def _start_processing(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        text = self._input_edit.text().strip()
        path = self._input_path or (Path(text) if text else None)
        if not path or not path.exists():
            QMessageBox.warning(self, "Input Required", "Select a folder or ZIP file.")
            return

        self._start_btn.setEnabled(False)
        self._spinner.start()
        self._progress.setValue(0)
        self._queue_list.clear()

        options = self._build_options()
        self._worker = PipelineWorker(path, options, self._controller, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _cancel_processing(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.statusBar().showMessage("Cancelling...")

    def _on_progress(self, info: ProgressInfo) -> None:
        pct = int(info.current / max(1, info.total) * 100)
        self._progress.setValue(pct)
        self._file_label.setText(info.filename)
        mins = int(info.estimated_remaining // 60)
        secs = int(info.estimated_remaining % 60)
        self._eta_label.setText(f"ETA {mins:02d}:{secs:02d}")
        self.statusBar().showMessage(f"Processing {info.current}/{info.total}: {info.filename}")

        if info.preview_before is not None:
            self._current_before = info.preview_before
        if info.preview_after is not None:
            self._current_after = info.preview_after
        self._preview.set_images(self._current_before, self._current_after)
        if info.preview_after is not None:
            self._histogram.set_image(info.preview_after)
            h, w = info.preview_after.shape[:2]
            self._info_size.setText(f"{w} × {h}")
            self._info_name.setText(info.filename)
            self._info_format.setText(Path(info.filename).suffix.upper())

        item = QListWidgetItem(f"✓ {info.filename}")
        self._queue_list.insertItem(0, item)

    def _on_finished(self, result: ProcessingResult) -> None:
        self._spinner.stop()
        self._start_btn.setEnabled(True)
        self._progress.setValue(100)
        self._eta_label.setText("Complete")
        self._load_history()
        msg = f"Done: {result.processed}/{result.total} processed, {result.failed} failed"
        self.statusBar().showMessage(msg)
        if result.errors:
            QMessageBox.warning(self, "Completed with errors", "\n".join(result.errors[:10]))

    def _on_failed(self, error: str) -> None:
        self._spinner.stop()
        self._start_btn.setEnabled(True)
        QMessageBox.critical(self, "Processing Failed", error)

    def _open_output(self) -> None:
        out = self._controller.last_output
        if out and self._controller.open_path(out):
            return
        QMessageBox.information(self, "Output", "No output folder available.")

    def _open_zip(self) -> None:
        z = self._controller.last_zip
        if z and self._controller.open_path(z.parent):
            return
        QMessageBox.information(self, "ZIP", "No ZIP file available.")

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "Photo Enhancer Pro",
            "Photo Enhancer Pro v1.0\n\n"
            "Professional offline photo enhancement\n"
            "iPhone Pro style processing pipeline",
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if not paths:
            return
        path = Path(paths[0])
        if path.is_dir() or path.suffix.lower() == ".zip":
            self._set_input(path)
        elif path.is_file():
            self._set_input(path.parent)
            try:
                bgr, _ = load_image(path)
                self._preview.set_images(bgr, bgr)
                self._histogram.set_image(bgr)
                self._info_name.setText(path.name)
                h, w = bgr.shape[:2]
                self._info_size.setText(f"{w} × {h}")
                self._info_format.setText(path.suffix.upper())
            except Exception as exc:
                logger.warning("Preview load failed: %s", exc)
        event.acceptProposedAction()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_spinner") and hasattr(self, "_preview"):
            self._spinner.move(
                max(0, self._preview.width() // 2 - 24),
                max(0, self._preview.height() // 2 - 24),
            )
