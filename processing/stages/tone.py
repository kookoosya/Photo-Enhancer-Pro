"""Tone and dynamic range processing stages."""

from __future__ import annotations

import cv2
import numpy as np

from processing.context import ProcessingContext
from processing.stages.base import ProcessingStage


class HighlightRecoveryStage(ProcessingStage):
    """Recover blown highlights with smooth rolloff."""

    name = "highlight_recovery"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        strength = abs(ctx.preset.highlights) / 100.0
        if strength < 0.01:
            return ctx
        lab = cv2.cvtColor(ctx.bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        l_float = l_ch.astype(np.float32)
        bright = np.clip((l_float - 170.0) / 85.0, 0.0, 1.0)
        bright = bright ** 1.5
        l_float -= bright * strength * 45.0
        l_ch = np.clip(l_float, 0, 255).astype(np.uint8)
        ctx.bgr = cv2.cvtColor(cv2.merge([l_ch, a_ch, b_ch]), cv2.COLOR_LAB2BGR)
        return ctx


class ShadowRecoveryStage(ProcessingStage):
    """Lift shadows with natural curve."""

    name = "shadow_recovery"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        strength = ctx.preset.shadows / 100.0
        if strength < 0.01:
            return ctx
        lab = cv2.cvtColor(ctx.bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        l_float = l_ch.astype(np.float32)
        dark = np.clip(1.0 - l_float / 90.0, 0.0, 1.0)
        dark = dark ** 2.0
        l_float += dark * strength * 55.0
        l_ch = np.clip(l_float, 0, 255).astype(np.uint8)
        ctx.bgr = cv2.cvtColor(cv2.merge([l_ch, a_ch, b_ch]), cv2.COLOR_LAB2BGR)
        return ctx


class ToneMappingStage(ProcessingStage):
    """Natural tone mapping — contrast, whites, blacks."""

    name = "tone_mapping"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        contrast = ctx.preset.contrast / 100.0
        whites = ctx.preset.whites / 100.0
        blacks = ctx.preset.blacks / 100.0
        lab = cv2.cvtColor(ctx.bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        l_float = l_ch.astype(np.float32)
        l_float = (l_float - 128.0) * (1.0 + contrast * 0.8) + 128.0
        l_float += whites * 12.0
        l_float += blacks * 8.0
        l_ch = np.clip(l_float, 0, 255).astype(np.uint8)
        ctx.bgr = cv2.cvtColor(cv2.merge([l_ch, a_ch, b_ch]), cv2.COLOR_LAB2BGR)
        return ctx


class LocalContrastStage(ProcessingStage):
    """CLAHE local contrast (clarity)."""

    name = "local_contrast"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        clarity = ctx.preset.clarity / 100.0
        if clarity < 0.01:
            return ctx
        lab = cv2.cvtColor(ctx.bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=1.0 + clarity * 1.8, tileGridSize=(8, 8))
        l_ch = clahe.apply(l_ch)
        ctx.bgr = cv2.cvtColor(cv2.merge([l_ch, a_ch, b_ch]), cv2.COLOR_LAB2BGR)
        return ctx


class MicroContrastStage(ProcessingStage):
    """Micro contrast on luminance channel."""

    name = "micro_contrast"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        texture = ctx.preset.texture / 100.0
        if texture < 0.01:
            return ctx
        lab = cv2.cvtColor(ctx.bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        blurred = cv2.GaussianBlur(l_ch, (0, 0), 2.5)
        detail = cv2.addWeighted(l_ch, 1.0 + texture * 0.6, blurred, -texture * 0.6, 0)
        ctx.bgr = cv2.cvtColor(cv2.merge([detail, a_ch, b_ch]), cv2.COLOR_LAB2BGR)
        return ctx


class DehazeStage(ProcessingStage):
    """Natural dehaze without HDR look."""

    name = "dehaze"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        strength = ctx.preset.dehaze / 100.0
        if strength < 0.01:
            return ctx
        lab = cv2.cvtColor(ctx.bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=1.0 + strength * 2.5, tileGridSize=(16, 16))
        enhanced_l = clahe.apply(l_ch)
        l_ch = cv2.addWeighted(l_ch, 1.0 - strength * 0.45, enhanced_l, strength * 0.45, 0)
        ctx.bgr = cv2.cvtColor(cv2.merge([l_ch, a_ch, b_ch]), cv2.COLOR_LAB2BGR)
        return ctx
