"""Landscape enhancement preset."""

from styles.base import EnhancementPreset

LANDSCAPE = EnhancementPreset(
    name="landscape",
    display_name="Landscape",
    exposure=0.15,
    contrast=14.0,
    highlights=-32.0,
    shadows=38.0,
    whites=7.0,
    blacks=-12.0,
    texture=14.0,
    clarity=10.0,
    dehaze=12.0,
    vibrance=16.0,
    saturation=4.0,
    sharpen=32.0,
    noise_reduction=10.0,
    sky_boost=0.18,
    grass_boost=0.15,
    water_boost=0.16,
    skin_protection=0.70,
)
