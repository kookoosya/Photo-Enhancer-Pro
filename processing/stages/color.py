"""Color and exposure processing stages."""

from __future__ import annotations

import cv2
import numpy as np

from processing.context import ProcessingContext
from processing.stages.base import ProcessingStage


class SegmentationStage(ProcessingStage):
    """Detect scene regions for localized adjustments."""

    name = "segmentation"

    def __init__(self, segmenter) -> None:
        self._segmenter = segmenter

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        if ctx.masks is None:
            ctx.masks = self._segmenter.segment(ctx.bgr)
        return ctx


class LensCorrectionStage(ProcessingStage):
    """Mild lens distortion correction."""

    name = "lens_correction"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        bgr = ctx.bgr
        h, w = bgr.shape[:2]
        focal = float(w)
        center = (w / 2.0, h / 2.0)
        k1 = -0.04
        camera_matrix = np.array(
            [[focal, 0, center[0]], [0, focal, center[1]], [0, 0, 1]], dtype=np.float64
        )
        dist_coeffs = np.array([k1, 0, 0, 0], dtype=np.float64)
        ctx.bgr = cv2.undistort(bgr, camera_matrix, dist_coeffs)
        return ctx


class WhiteBalanceStage(ProcessingStage):
    """Gray-world auto white balance with highlight protection."""

    name = "white_balance"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        if ctx.preset.color_temperature != "auto":
            return ctx
        result = ctx.bgr.astype(np.float32)
        gray = cv2.cvtColor(ctx.bgr, cv2.COLOR_BGR2GRAY)
        weight = np.clip(1.0 - gray.astype(np.float32) / 255.0, 0.2, 1.0)
        weight_3 = np.stack([weight, weight, weight], axis=-1)
        for ch in range(3):
            channel = result[:, :, ch]
            avg = float(np.average(channel, weights=weight))
            global_avg = float(np.mean(result))
            result[:, :, ch] *= global_avg / (avg + 1e-6)
        ctx.bgr = np.clip(result, 0, 255).astype(np.uint8)
        return ctx


class ExposureStage(ProcessingStage):
    """Exposure adjustment via gamma."""

    name = "exposure"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        gamma = 1.0 - ctx.preset.exposure * 0.15
        gamma = max(0.5, min(gamma, 2.0))
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype(
            np.uint8
        )
        ctx.bgr = cv2.LUT(ctx.bgr, table)
        return ctx


class ColorBalanceStage(ProcessingStage):
    """Vibrance and saturation."""

    name = "color_balance"

    def process(self, ctx: ProcessingContext) -> ProcessingContext:
        hsv = cv2.cvtColor(ctx.bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        vibrance = ctx.preset.vibrance / 100.0
        saturation = ctx.preset.saturation / 100.0
        s_ch = hsv[:, :, 1]
        sat_factor = 1.0 + vibrance * (1.0 - s_ch / 255.0)
        s_ch = s_ch * sat_factor * (1.0 + saturation)
        hsv[:, :, 1] = np.clip(s_ch, 0, 255)
        ctx.bgr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        return ctx
