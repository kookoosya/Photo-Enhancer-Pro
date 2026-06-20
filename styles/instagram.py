"""Instagram-style enhancement preset."""

from styles.base import EnhancementPreset

INSTAGRAM = EnhancementPreset(
    name="instagram",
    display_name="Instagram",
    exposure=0.18,
    contrast=12.0,
    highlights=-28.0,
    shadows=32.0,
    whites=10.0,
    blacks=-8.0,
    texture=8.0,
    clarity=6.0,
    dehaze=4.0,
    vibrance=20.0,
    saturation=8.0,
    sharpen=28.0,
    noise_reduction=8.0,
    sky_boost=0.12,
    grass_boost=0.10,
    water_boost=0.12,
    skin_protection=0.88,
)
