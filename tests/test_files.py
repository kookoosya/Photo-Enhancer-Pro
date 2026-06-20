"""Tests for file utilities."""

import tempfile
from pathlib import Path

from utils.files import create_zip, extract_zip, get_output_folder_name, is_supported_image


def test_is_supported_image() -> None:
    assert is_supported_image(Path("photo.jpg"))
    assert is_supported_image(Path("photo.JPEG"))
    assert is_supported_image(Path("photo.heic"))
    assert not is_supported_image(Path("document.pdf"))


def test_get_output_folder_name() -> None:
    assert get_output_folder_name("Vacation") == "Vacation_Enhanced"
    assert get_output_folder_name("Vacation.zip") == "Vacation_Enhanced"


def test_zip_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.jpg").write_bytes(b"fake")

        zip_path = tmp_path / "test.zip"
        create_zip(source, zip_path)

        dest = tmp_path / "extracted"
        extract_zip(zip_path, dest)
        assert (dest / "test.jpg").exists()
