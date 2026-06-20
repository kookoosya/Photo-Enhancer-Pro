"""Enhancement preset definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EnhancementPreset:
    """Parameters for a photo enhancement style."""

    name: str
    display_name: str
    exposure: float = 0.0
    contrast: float = 0.0
    highlights: float = 0.0
    shadows: float = 0.0
    whites: float = 0.0
    blacks: float = 0.0
    texture: float = 0.0
    clarity: float = 0.0
    dehaze: float = 0.0
    vibrance: float = 0.0
    saturation: float = 0.0
    sharpen: float = 0.0
    noise_reduction: float = 0.0
    color_temperature: str = "auto"
    tint: str = "auto"
    sky_boost: float = 0.0
    grass_boost: float = 0.0
    water_boost: float = 0.0
    skin_protection: float = 1.0

    def to_dict(self) -> dict[str, float | str]:
        """Serialize preset to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "exposure": self.exposure,
            "contrast": self.contrast,
            "highlights": self.highlights,
            "shadows": self.shadows,
            "whites": self.whites,
            "blacks": self.blacks,
            "texture": self.texture,
            "clarity": self.clarity,
            "dehaze": self.dehaze,
            "vibrance": self.vibrance,
            "saturation": self.saturation,
            "sharpen": self.sharpen,
            "noise_reduction": self.noise_reduction,
            "color_temperature": self.color_temperature,
            "tint": self.tint,
            "sky_boost": self.sky_boost,
            "grass_boost": self.grass_boost,
            "water_boost": self.water_boost,
            "skin_protection": self.skin_protection,
        }
