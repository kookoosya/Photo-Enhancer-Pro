"""Portrait enhancement preset."""

from styles.base import EnhancementPreset

PORTRAIT = EnhancementPreset(
    name="portrait",
    display_name="Portrait",
    exposure=0.15,
    contrast=5.0,
    highlights=-20.0,
    shadows=25.0,
    whites=5.0,
    blacks=-5.0,
    texture=5.0,
    clarity=3.0,
    dehaze=2.0,
    vibrance=8.0,
    saturation=2.0,
    sharpen=25.0,
    noise_reduction=15.0,
    sky_boost=0.05,
    grass_boost=0.05,
    water_boost=0.05,
    skin_protection=0.95,
)
