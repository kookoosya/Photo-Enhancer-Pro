"""Preset registry."""

from __future__ import annotations

from styles.base import EnhancementPreset
from styles.cinematic import CINEMATIC
from styles.dslr import DSLR
from styles.instagram import INSTAGRAM
from styles.iphone import IPHONE_PRO
from styles.landscape import LANDSCAPE
from styles.nature import NATURE
from styles.portrait import PORTRAIT

PRESETS: dict[str, EnhancementPreset] = {
    "iphone_pro": IPHONE_PRO,
    "dslr": DSLR,
    "landscape": LANDSCAPE,
    "portrait": PORTRAIT,
    "nature": NATURE,
    "instagram": INSTAGRAM,
    "cinematic": CINEMATIC,
}


def get_preset(name: str) -> EnhancementPreset:
    """Get preset by name, defaulting to iPhone Pro."""
    return PRESETS.get(name, IPHONE_PRO)


def list_presets() -> list[str]:
    """List available preset names."""
    return list(PRESETS.keys())
