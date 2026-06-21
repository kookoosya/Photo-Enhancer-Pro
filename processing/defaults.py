"""Default pipeline configuration constants."""

DEFAULT_STAGE_ORDER: list[str] = [
    "segmentation",
    "lens_correction",
    "white_balance",
    "exposure",
    "highlight_recovery",
    "shadow_recovery",
    "tone_mapping",
    "local_contrast",
    "micro_contrast",
    "texture",
    "dehaze",
    "color_balance",
    "regional_enhance",
    "noise_reduction",
    "sharpening",
    "final_optimization",
    "safety_blend",
]


def get_default_stage_order() -> list[str]:
    """Return a copy of the default stage order."""
    return list(DEFAULT_STAGE_ORDER)
