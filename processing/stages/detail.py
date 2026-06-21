"""Detail, regional, and finishing processing stages."""

from __future__ import annotations

import cv2
import numpy as np

from noise.reducer import reduce_noise
from processing.context import ProcessingContext
from processing.stages.base import ProcessingStage
from segmentation.segmenter import SceneMasks


class TextureStage(ProcessingStage):
    """Subtle texture enhancement via unsharp mask."""

    name = "texture"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        amount = ctx.preset.texture / 250.0
        if amount < 0.01:
            return ctx
        blurred = cv2.GaussianBlur(ctx.bgr, (0, 0), 1.2)
        sharp = cv2.addWeighted(ctx.bgr, 1.0 + amount, blurred, -amount, 0)
        ctx.bgr = np.clip(sharp, 0, 255).astype(np.uint8)
        return ctx


class RegionalEnhanceStage(ProcessingStage):
    """Sky, grass, water with skin protection."""

    name = "regional_enhance"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        if ctx.masks is None:
            return ctx
        result = ctx.bgr.astype(np.float32)
        masks = ctx.masks
        preset = ctx.preset
        skin_protect = masks.skin * preset.skin_protection

        if preset.sky_boost > 0:
            sky = self._enhance_sky(ctx.bgr)
            sky_mask = masks.sky * (1.0 - skin_protect)
            result = self._blend(result, sky, sky_mask, preset.sky_boost)

        if preset.grass_boost > 0:
            grass = self._enhance_grass(ctx.bgr)
            grass_mask = masks.grass * (1.0 - skin_protect)
            result = self._blend(result, grass, grass_mask, preset.grass_boost)

        if preset.water_boost > 0:
            water = self._enhance_water(ctx.bgr)
            water_mask = masks.water * (1.0 - skin_protect)
            result = self._blend(result, water, water_mask, preset.water_boost)

        ctx.bgr = np.clip(result, 0, 255).astype(np.uint8)
        return ctx

    def _enhance_sky(self, bgr: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        lab[:, :, 2] = np.clip(lab[:, :, 2] - 3.0, 0, 255)
        lab[:, :, 0] = np.clip(lab[:, :, 0] * 1.02, 0, 255)
        return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

    def _enhance_grass(self, bgr: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        h, s, v = cv2.split(hsv)
        green_mask = ((h > 25) & (h < 95)).astype(np.float32)
        s = s + green_mask * 8.0
        v = v + green_mask * 4.0
        hsv = cv2.merge([h, np.clip(s, 0, 255), np.clip(v, 0, 255)])
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    def _enhance_water(self, bgr: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        lab[:, :, 2] = np.clip(lab[:, :, 2] - 6.0, 0, 255)
        lab[:, :, 0] = np.clip(lab[:, :, 0] * 1.03, 0, 255)
        return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

    def _blend(
        self,
        base: np.ndarray,
        enhanced: np.ndarray,
        mask: np.ndarray,
        strength: float,
    ) -> np.ndarray:
        mask_3 = np.stack([mask, mask, mask], axis=-1)
        alpha = np.clip(mask_3 * strength, 0, 1)
        return base * (1.0 - alpha) + enhanced.astype(np.float32) * alpha


class NoiseReductionStage(ProcessingStage):
    """Adaptive noise reduction."""

    name = "noise_reduction"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        skin = ctx.masks.skin if ctx.masks else None
        ctx.bgr = reduce_noise(ctx.bgr, ctx.preset.noise_reduction, skin)
        return ctx


class SharpeningStage(ProcessingStage):
    """Edge-aware sharpening with skin protection."""

    name = "sharpening"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        strength = ctx.preset.sharpen / 100.0
        if strength < 0.01:
            return ctx
        bgr = ctx.bgr
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 40, 120).astype(np.float32) / 255.0
        edge_mask = cv2.GaussianBlur(edges, (5, 5), 0)
        edge_3 = np.stack([edge_mask, edge_mask, edge_mask], axis=-1)

        blurred = cv2.GaussianBlur(bgr, (0, 0), 1.8)
        sharpened = cv2.addWeighted(bgr, 1.0 + strength * 0.8, blurred, -strength * 0.8, 0)
        result = bgr.astype(np.float32) * (1.0 - edge_3 * strength) + sharpened.astype(
            np.float32
        ) * (edge_3 * strength)

        if ctx.masks is not None and ctx.masks.skin.max() > 0:
            skin = ctx.masks.skin
            skin_3 = np.stack([skin, skin, skin], axis=-1)
            soft_sharp = cv2.addWeighted(bgr, 1.0 + strength * 0.25, blurred, -strength * 0.25, 0)
            result = result * (1.0 - skin_3 * 0.75) + soft_sharp.astype(np.float32) * (
                skin_3 * 0.75
            )

        ctx.bgr = np.clip(result, 0, 255).astype(np.uint8)
        return ctx


class FinalOptimizationStage(ProcessingStage):
    """Final gentle contrast curve."""

    name = "final_optimization"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        lab = cv2.cvtColor(ctx.bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        l_float = l_ch.astype(np.float32)
        l_float = 255.0 * (l_float / 255.0) ** 0.99
        l_ch = np.clip(l_float, 0, 255).astype(np.uint8)
        ctx.bgr = cv2.cvtColor(cv2.merge([l_ch, a_ch, b_ch]), cv2.COLOR_LAB2BGR)
        return ctx


class SafetyBlendStage(ProcessingStage):
    """Blend with original to prevent over-processing."""

    name = "safety_blend"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        blend = 0.93
        ctx.bgr = cv2.addWeighted(ctx.bgr, blend, ctx.original, 1.0 - blend, 0)
        ctx.bgr = np.clip(ctx.bgr, 0, 255).astype(np.uint8)
        return ctx
