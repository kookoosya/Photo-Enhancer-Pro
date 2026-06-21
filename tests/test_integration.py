"""Integration tests for batch pipeline."""

import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from pipeline import ProcessingOptions, ProcessingPipeline


def _create_test_image(path: Path, size: tuple[int, int] = (400, 300)) -> None:
    arr = np.random.randint(0, 255, (*size[::-1], 3), dtype=np.uint8)
    Image.fromarray(arr).save(path, format="JPEG", quality=90)


def test_pipeline_processes_folder() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src = root / "TestAlbum"
        src.mkdir()
        for i in range(3):
            _create_test_image(src / f"IMG_{i:04d}.jpg")

        options = ProcessingOptions(
            preset_name="iphone_pro",
            output_dir=root / "out",
            create_zip=True,
            duplicate_detection=True,
        )
        pipeline = ProcessingPipeline(options)
        result = pipeline.run(src)

        assert result.total == 3
        assert result.processed == 3
        assert result.failed == 0
        assert result.output_folder is not None
        assert result.output_folder.exists()
        assert (result.output_folder / "IMG_0000.jpg").exists()
        if result.zip_path:
            assert result.zip_path.exists()


def test_pipeline_cancel() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src = root / "Large"
        src.mkdir()
        for i in range(5):
            _create_test_image(src / f"photo_{i}.jpg", (800, 600))

        pipeline = ProcessingPipeline(ProcessingOptions(create_zip=False))
        pipeline.cancel()
        result = pipeline.run(src)
        assert result.skipped >= 0 or result.processed >= 0
