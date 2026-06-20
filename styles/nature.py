"""Nature / landscape enhancement preset."""

from styles.base import EnhancementPreset

NATURE = EnhancementPreset(
    name="nature",
    display_name="Nature",
    exposure=0.12,
    contrast=12.0,
    highlights=-30.0,
    shadows=35.0,
    whites=6.0,
    blacks=-8.0,
    texture=12.0,
    clarity=8.0,
    dehaze=10.0,
    vibrance=18.0,
    saturation=5.0,
    sharpen=30.0,
    noise_reduction=10.0,
    sky_boost=0.20,
    grass_boost=0.18,
    water_boost=0.15,
    skin_protection=0.75,
)
