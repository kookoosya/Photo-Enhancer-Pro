"""Tests for configuration module."""

from config import AppConfig, load_config, get_config


def test_load_config_defaults() -> None:
    config = load_config()
    assert config.app_name == "Photo Enhancer Pro"
    assert config.default_preset == "iphone_pro"
    assert "jpg" in config.supported_formats


def test_get_config_singleton() -> None:
    c1 = get_config()
    c2 = get_config()
    assert c1 is c2


def test_processing_config() -> None:
    config = AppConfig()
    assert config.processing.jpeg_quality == 95
    assert config.processing.max_workers >= 1
