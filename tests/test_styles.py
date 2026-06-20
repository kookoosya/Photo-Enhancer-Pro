"""Tests for enhancement presets."""

from styles import get_preset, list_presets, PRESETS
from styles.iphone import IPHONE_PRO


def test_list_presets() -> None:
    presets = list_presets()
    assert "iphone_pro" in presets
    assert "dslr" in presets
    assert len(presets) >= 7


def test_iphone_pro_preset_values() -> None:
    assert IPHONE_PRO.exposure == 0.20
    assert IPHONE_PRO.contrast == 10.0
    assert IPHONE_PRO.highlights == -35.0
    assert IPHONE_PRO.shadows == 40.0
    assert IPHONE_PRO.sharpen == 35.0


def test_get_preset_default() -> None:
    preset = get_preset("unknown_preset")
    assert preset.name == "iphone_pro"


def test_preset_to_dict() -> None:
    data = IPHONE_PRO.to_dict()
    assert data["name"] == "iphone_pro"
    assert "exposure" in data
