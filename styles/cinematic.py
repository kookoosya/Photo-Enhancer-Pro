"""Cinematic enhancement preset."""

from styles.base import EnhancementPreset

CINEMATIC = EnhancementPreset(
    name="cinematic",
    display_name="Cinematic",
    exposure=-0.05,
    contrast=20.0,
    highlights=-40.0,
    shadows=20.0,
    whites=0.0,
    blacks=-20.0,
    texture=8.0,
    clarity=12.0,
    dehaze=6.0,
    vibrance=5.0,
    saturation=-5.0,
    sharpen=20.0,
    noise_reduction=12.0,
    sky_boost=0.08,
    grass_boost=0.06,
    water_boost=0.10,
    skin_protection=0.85,
)
