"""Gradio desktop GUI for Photo Enhancer Pro."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import gradio as gr
import cv2
import numpy as np

from config import get_config
from pipeline import ProcessingOptions, ProcessingPipeline, ProgressInfo
from styles import list_presets
from utils.hardware import get_gpu_usage, get_system_info
from utils.image_io import compute_histogram, resize_for_preview

logger = logging.getLogger("photo_enhancer.gui")

CUSTOM_CSS = """
:root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --accent: #58a6ff;
    --text: #e6edf3;
}
.gradio-container {
    background: var(--bg-primary) !important;
    color: var(--text) !important;
    max-width: 1400px !important;
}
.main-header {
    text-align: center;
    padding: 1rem 0;
}
.main-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent);
    margin: 0;
}
.main-header p {
    color: #8b949e;
    margin: 0.25rem 0 0;
}
.drop-zone {
    border: 2px dashed #30363d !important;
    border-radius: 12px !important;
    background: var(--bg-secondary) !important;
    min-height: 120px !important;
}
footer { display: none !important; }
"""


class PhotoEnhancerApp:
    """Gradio application controller."""

    def __init__(self) -> None:
        self.config = get_config()
        self.pipeline: ProcessingPipeline | None = None
        self._processing = False
        self._last_output: Path | None = None
        self._last_zip: Path | None = None
        self._progress_state = {"current": 0, "total": 0, "filename": "", "eta": 0.0}

    def _format_time(self, seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.0f}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"

    def _on_progress(self, info: ProgressInfo) -> None:
        self._progress_state = {
            "current": info.current,
            "total": info.total,
            "filename": info.filename,
            "eta": info.estimated_remaining,
        }

    def start_processing(
        self,
        input_folder: str,
        input_zip: str,
        output_folder: str,
        preset: str,
        keep_exif: bool,
        create_zip: bool,
        overwrite: bool,
        resize: bool,
        upscale: bool,
        preview_save: bool,
        duplicate_det: bool,
        blur_det: bool,
    ) -> tuple[
        str, float, str,
        np.ndarray | None, np.ndarray | None, tuple | None, np.ndarray | None,
    ]:
        """Start batch processing."""
        if self._processing:
            return "Already processing...", 0.0, "", None, None, None, None

        input_path: Path | None = None
        if input_zip and Path(input_zip).exists():
            input_path = Path(input_zip)
        elif input_folder and Path(input_folder).exists():
            input_path = Path(input_folder)

        if input_path is None:
            return "Please select a folder or ZIP file.", 0.0, "", None, None, None, None

        options = ProcessingOptions(
            preset_name=preset,
            output_dir=Path(output_folder) if output_folder else None,
            keep_exif=keep_exif,
            create_zip=create_zip,
            overwrite_existing=overwrite,
            resize=resize,
            upscale=upscale,
            preview_before_save=preview_save,
            duplicate_detection=duplicate_det,
            blur_detection=blur_det,
            best_photo_ranking=True,
        )

        self._processing = True
        preview_before = None
        preview_after = None
        histogram = None
        status = ""
        progress = 0.0
        eta_str = ""

        def run() -> None:
            nonlocal preview_before, preview_after, histogram, status, progress, eta_str
            try:
                self.pipeline = ProcessingPipeline(options)

                def callback(info: ProgressInfo) -> None:
                    self._on_progress(info)
                    if info.preview_before is not None:
                        preview_before = cv2_to_rgb(info.preview_before)
                    if info.preview_after is not None:
                        preview_after = cv2_to_rgb(info.preview_after)
                        histogram = compute_histogram(info.preview_after)

                result = self.pipeline.run(input_path, progress_callback=callback)
                self._last_output = result.output_folder
                self._last_zip = result.zip_path

                status = (
                    f"Done! Processed {result.processed}/{result.total} images "
                    f"in {self._format_time(result.elapsed_seconds)}. "
                    f"Failed: {result.failed}. Skipped: {result.skipped}."
                )
                if result.duplicates:
                    status += f" Found {len(result.duplicates)} duplicate pairs."
                if result.blurry:
                    status += f" {len(result.blurry)} blurry images detected."
                progress = 1.0
                eta_str = "Complete"
            except Exception as exc:
                status = f"Error: {exc}"
                logger.exception("Processing failed")
            finally:
                self._processing = False

        def cv2_to_rgb(bgr: np.ndarray) -> np.ndarray:
            return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

        # Poll until complete (Gradio sync handler)
        while thread.is_alive():
            state = self._progress_state
            if state["total"] > 0:
                progress = state["current"] / state["total"]
                eta_str = self._format_time(state["eta"])
            time.sleep(0.3)

        return status, progress, eta_str, preview_before, preview_after, (
            (preview_before, preview_after)
            if preview_before is not None and preview_after is not None
            else None
        ), histogram

    def get_live_progress(self) -> tuple[float, str, str]:
        """Get current progress for live updates."""
        state = self._progress_state
        if state["total"] == 0:
            return 0.0, "", "Ready"
        progress = state["current"] / state["total"]
        return progress, state["filename"], self._format_time(state["eta"])

    def open_folder(self) -> str:
        """Open output folder in file explorer."""
        if self._last_output and self._last_output.exists():
            if sys.platform == "win32":
                os.startfile(self._last_output)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self._last_output)], check=False)
            else:
                subprocess.run(["xdg-open", str(self._last_output)], check=False)
            return f"Opened: {self._last_output}"
        return "No output folder available."

    def open_zip(self) -> str:
        """Open ZIP file location."""
        if self._last_zip and self._last_zip.exists():
            if sys.platform == "win32":
                os.startfile(self._last_zip.parent)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self._last_zip.parent)], check=False)
            else:
                subprocess.run(["xdg-open", str(self._last_zip.parent)], check=False)
            return f"ZIP: {self._last_zip}"
        return "No ZIP file available."

    def get_system_status(self) -> str:
        """Get system and GPU status."""
        info = get_system_info()
        gpu = get_gpu_usage()
        lines = [
            f"CPU Cores: {info.cpu_count}",
            f"Memory Available: {info.memory_gb:.1f} GB",
            f"CUDA: {'Yes' if info.cuda_available else 'No'}",
        ]
        if info.gpu_name:
            lines.append(f"GPU: {info.gpu_name}")
        lines.append(f"GPU Memory: {gpu['memory_percent']:.1f}%")
        return "\n".join(lines)

    def build(self) -> gr.Blocks:
        """Build Gradio interface."""
        app = self
        presets = list_presets()
        preset_labels = [p.replace("_", " ").title() for p in presets]

        with gr.Blocks(
            title="Photo Enhancer Pro",
            css=CUSTOM_CSS,
            theme=gr.themes.Base(
                primary_hue="blue",
                neutral_hue="slate",
            ).set(
                body_background_fill="#0d1117",
                block_background_fill="#161b22",
                block_border_color="#30363d",
                body_text_color="#e6edf3",
                button_primary_background_fill="#238636",
                button_primary_text_color="#ffffff",
            ),
        ) as demo:
            gr.HTML(
                """
                <div class="main-header">
                    <h1>Photo Enhancer Pro</h1>
                    <p>Automatic iPhone Pro style enhancement — offline, batch, production-ready</p>
                </div>
                """
            )

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Input")
                    drop_zone = gr.File(
                        label="Drag & Drop Folder or ZIP",
                        file_count="multiple",
                        type="filepath",
                    )
                    input_folder = gr.Textbox(
                        label="Input Folder Path",
                        placeholder="C:\\Photos\\Vacation",
                    )
                    input_zip = gr.Textbox(
                        label="Input ZIP Path",
                        placeholder="C:\\Photos\\Vacation.zip",
                    )
                    output_folder = gr.Textbox(
                        label="Output Folder",
                        placeholder="Leave empty for same directory",
                    )

                    preset = gr.Dropdown(
                        choices=presets,
                        value=self.config.default_preset,
                        label="Processing Preset",
                        info="iPhone Pro is the default natural style",
                    )

                    gr.Markdown("### Advanced Options")
                    with gr.Row():
                        keep_exif = gr.Checkbox(value=True, label="Keep EXIF")
                        create_zip = gr.Checkbox(value=True, label="Create ZIP")
                        overwrite = gr.Checkbox(value=False, label="Overwrite Existing")
                    with gr.Row():
                        resize = gr.Checkbox(value=False, label="Resize")
                        upscale = gr.Checkbox(value=False, label="Upscale")
                        preview_save = gr.Checkbox(value=False, label="Preview Before Save")
                    with gr.Row():
                        duplicate_det = gr.Checkbox(value=True, label="Duplicate Detection")
                        blur_det = gr.Checkbox(value=True, label="Blur Detection")

                    start_btn = gr.Button("Start Processing", variant="primary", size="lg")
                    with gr.Row():
                        open_folder_btn = gr.Button("Open Folder")
                        open_zip_btn = gr.Button("Open ZIP")

                with gr.Column(scale=2):
                    gr.Markdown("### Progress")
                    progress_bar = gr.Slider(
                        minimum=0, maximum=1, value=0, label="Progress", interactive=False
                    )
                    eta_display = gr.Textbox(label="Estimated Remaining Time", value="Ready")
                    status_display = gr.Textbox(label="Status", lines=3)

                    gr.Markdown("### Live Preview")
                    with gr.Row():
                        preview_before = gr.Image(label="Before", type="numpy")
                        preview_after = gr.Image(label="After", type="numpy")
                    comparison_slider = gr.ImageSlider(
                        label="Before / After Comparison",
                        type="numpy",
                        height=400,
                    )
                    histogram = gr.Image(label="Histogram", type="numpy")

                    system_status = gr.Textbox(label="System / GPU Monitor", lines=4)
                    refresh_sys = gr.Button("Refresh System Info")

            start_btn.click(
                fn=app.start_processing,
                inputs=[
                    input_folder, input_zip, output_folder, preset,
                    keep_exif, create_zip, overwrite, resize, upscale,
                    preview_save, duplicate_det, blur_det,
                ],
                outputs=[
                    status_display, progress_bar, eta_display,
                    preview_before, preview_after, comparison_slider, histogram,
                ],
            )

            def handle_drop(files: list[str] | None) -> tuple[str, str]:
                if not files:
                    return "", ""
                first = Path(files[0])
                if first.suffix.lower() == ".zip":
                    return "", str(first)
                folder = str(first.parent if first.is_file() else first)
                return folder, ""

            drop_zone.change(fn=handle_drop, inputs=drop_zone, outputs=[input_folder, input_zip])

            open_folder_btn.click(fn=app.open_folder, outputs=status_display)
            open_zip_btn.click(fn=app.open_zip, outputs=status_display)
            refresh_sys.click(fn=app.get_system_status, outputs=system_status)

            demo.load(fn=app.get_system_status, outputs=system_status)

        return demo


def launch_gui(share: bool = False, server_port: int = 7860) -> None:
    """Launch the Gradio GUI."""
    app = PhotoEnhancerApp()
    demo = app.build()
    demo.launch(
        share=share,
        server_port=server_port,
        inbrowser=True,
        show_error=True,
    )
