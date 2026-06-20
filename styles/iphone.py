"""iPhone Pro enhancement preset."""

from styles.base import EnhancementPreset

IPHONE_PRO = EnhancementPreset(
    name="iphone_pro",
    display_name="iPhone Pro",
    exposure=0.20,
    contrast=10.0,
    highlights=-35.0,
    shadows=40.0,
    whites=8.0,
    blacks=-10.0,
    texture=10.0,
    clarity=5.0,
    dehaze=5.0,
    vibrance=15.0,
    saturation=3.0,
    sharpen=35.0,
    noise_reduction=10.0,
    color_temperature="auto",
    tint="auto",
    sky_boost=0.15,
    grass_boost=0.12,
    water_boost=0.18,
    skin_protection=0.85,
)
