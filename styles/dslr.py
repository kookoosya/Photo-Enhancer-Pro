"""DSLR enhancement preset."""

from styles.base import EnhancementPreset

DSLR = EnhancementPreset(
    name="dslr",
    display_name="DSLR",
    exposure=0.10,
    contrast=15.0,
    highlights=-25.0,
    shadows=30.0,
    whites=5.0,
    blacks=-15.0,
    texture=15.0,
    clarity=10.0,
    dehaze=8.0,
    vibrance=10.0,
    saturation=5.0,
    sharpen=40.0,
    noise_reduction=8.0,
    sky_boost=0.10,
    grass_boost=0.08,
    water_boost=0.10,
    skin_protection=0.80,
)
