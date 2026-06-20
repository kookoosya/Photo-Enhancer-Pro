"""Core image enhancement engine."""

from __future__ import annotations

import logging
from typing import Any

import cv2
import numpy as np

from noise.reducer import reduce_noise
from segmentation.segmenter import SceneMasks, SceneSegmenter
from styles.base import EnhancementPreset
from upscale.upscaler import upscale_image

logger = logging.getLogger("photo_enhancer.enhancer")


class ImageEnhancer:
    """Production image enhancer with iPhone Pro style pipeline."""

    def __init__(self, preset: EnhancementPreset) -> None:
        self.preset = preset
        self.segmenter = SceneSegmenter()

    def enhance(self, bgr: np.ndarray, masks: SceneMasks | None = None) -> np.ndarray:
        """Run full enhancement pipeline on BGR image."""
        original = bgr.copy()
        masks = masks or self.segmenter.segment(bgr)

        # Pipeline steps 3-20
        result = self._lens_distortion_correction(bgr)
        result = self._auto_white_balance(result)
        result = self._auto_exposure(result)
        result = self._highlight_recovery(result)
        result = self._shadow_lifting(result)
        result = self._tone_mapping(result)
        result = self._local_contrast(result)
        result = self._micro_contrast(result)
        result = self._texture_enhancement(result)
        result = self._dehaze(result)
        result = self._color_balancing(result)
        result = self._apply_regional_enhancements(result, masks)
        result = reduce_noise(result, self.preset.noise_reduction, masks.skin)
        result = self._smart_sharpening(result, masks.skin)
        result = self._jpeg_optimization(result)

        # Safety: blend with original to prevent over-processing
        blend = 0.92
        result = cv2.addWeighted(result, blend, original, 1 - blend, 0)
        return np.clip(result, 0, 255).astype(np.uint8)

    def _lens_distortion_correction(self, bgr: np.ndarray) -> np.ndarray:
        """Step 3: Mild lens distortion correction."""
        h, w = bgr.shape[:2]
        focal = w
        center = (w / 2, h / 2)
        k1 = -0.05
        camera_matrix = np.array(
            [[focal, 0, center[0]], [0, focal, center[1]], [0, 0, 1]], dtype=np.float64
        )
        dist_coeffs = np.array([k1, 0, 0, 0], dtype=np.float64)
        return cv2.undistort(bgr, camera_matrix, dist_coeffs)

    def _auto_white_balance(self, bgr: np.ndarray) -> np.ndarray:
        """Step 4: Gray world auto white balance."""
        if self.preset.color_temperature != "auto":
            return bgr
        result = bgr.astype(np.float32)
        avg_b = np.mean(result[:, :, 0])
        avg_g = np.mean(result[:, :, 1])
        avg_r = np.mean(result[:, :, 2])
        avg_gray = (avg_b + avg_g + avg_r) / 3.0
        result[:, :, 0] *= avg_gray / (avg_b + 1e-6)
        result[:, :, 1] *= avg_gray / (avg_g + 1e-6)
        result[:, :, 2] *= avg_gray / (avg_r + 1e-6)
        return np.clip(result, 0, 255).astype(np.uint8)

    def _auto_exposure(self, bgr: np.ndarray) -> np.ndarray:
        """Step 5: Exposure adjustment."""
        gamma = 1.0 - self.preset.exposure * 0.15
        gamma = max(0.5, min(gamma, 2.0))
        inv_gamma = 1.0 / gamma
        table = np.array(
            [((i / 255.0) ** inv_gamma) * 255 for i in range(256)]
        ).astype(np.uint8)
        return cv2.LUT(bgr, table)

    def _highlight_recovery(self, bgr: np.ndarray) -> np.ndarray:
        """Step 6: Recover blown highlights."""
        strength = abs(self.preset.highlights) / 100.0
        if strength < 0.01:
            return bgr
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        bright_mask = (l_ch > 200).astype(np.float32)
        l_float = l_ch.astype(np.float32)
        reduction = strength * 40.0
        l_float = l_float - bright_mask * reduction
        l_ch = np.clip(l_float, 0, 255).astype(np.uint8)
        lab = cv2.merge([l_ch, a_ch, b_ch])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def _shadow_lifting(self, bgr: np.ndarray) -> np.ndarray:
        """Step 7: Lift shadows."""
        strength = self.preset.shadows / 100.0
        if strength < 0.01:
            return bgr
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        l_float = l_ch.astype(np.float32)
        dark_mask = (l_ch < 80).astype(np.float32)
        lift = strength * 50.0
        l_float = l_float + dark_mask * lift
        l_ch = np.clip(l_float, 0, 255).astype(np.uint8)
        lab = cv2.merge([l_ch, a_ch, b_ch])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def _tone_mapping(self, bgr: np.ndarray) -> np.ndarray:
        """Step 8: Natural tone mapping."""
        contrast = self.preset.contrast / 100.0
        whites = self.preset.whites / 100.0
        blacks = self.preset.blacks / 100.0

        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        l_float = l_ch.astype(np.float32)

        l_float = (l_float - 128) * (1 + contrast) + 128
        l_float += whites * 15.0
        l_float += blacks * 10.0
        l_ch = np.clip(l_float, 0, 255).astype(np.uint8)

        lab = cv2.merge([l_ch, a_ch, b_ch])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def _local_contrast(self, bgr: np.ndarray) -> np.ndarray:
        """Step 9: CLAHE local contrast."""
        clarity = self.preset.clarity / 100.0
        if clarity < 0.01:
            return bgr
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=1.0 + clarity * 2.0, tileGridSize=(8, 8))
        l_ch = clahe.apply(l_ch)
        lab = cv2.merge([l_ch, a_ch, b_ch])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def _micro_contrast(self, bgr: np.ndarray) -> np.ndarray:
        """Step 10: Micro contrast via unsharp on luminance."""
        texture = self.preset.texture / 100.0
        if texture < 0.01:
            return bgr
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        blurred = cv2.GaussianBlur(l_ch, (0, 0), 3)
        detail = cv2.addWeighted(l_ch, 1 + texture, blurred, -texture, 0)
        lab = cv2.merge([detail, a_ch, b_ch])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def _texture_enhancement(self, bgr: np.ndarray) -> np.ndarray:
        """Step 11: Texture enhancement."""
        texture = self.preset.texture / 200.0
        if texture < 0.01:
            return bgr
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]) * texture
        sharpened = cv2.filter2D(bgr, -1, kernel)
        return cv2.addWeighted(bgr, 1 - texture, sharpened, texture, 0)

    def _dehaze(self, bgr: np.ndarray) -> np.ndarray:
        """Step 12: Dehaze using dark channel prior approximation."""
        strength = self.preset.dehaze / 100.0
        if strength < 0.01:
            return bgr
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=1.0 + strength * 3.0, tileGridSize=(16, 16))
        l_ch = clahe.apply(l_ch)
        lab = cv2.merge([l_ch, a_ch, b_ch])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        return cv2.addWeighted(bgr, 1 - strength * 0.5, result, strength * 0.5, 0)

    def _color_balancing(self, bgr: np.ndarray) -> np.ndarray:
        """Step 13: Vibrance and saturation."""
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        vibrance = self.preset.vibrance / 100.0
        saturation = self.preset.saturation / 100.0

        s_ch = hsv[:, :, 1]
        v_ch = hsv[:, :, 2]
        # Vibrance: boost less-saturated pixels more
        sat_factor = 1.0 + vibrance * (1.0 - s_ch / 255.0)
        s_ch = s_ch * sat_factor
        s_ch = s_ch * (1.0 + saturation)
        hsv[:, :, 1] = np.clip(s_ch, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    def _apply_regional_enhancements(
        self, bgr: np.ndarray, masks: SceneMasks
    ) -> np.ndarray:
        """Steps 14-17: Regional enhancements with protection."""
        result = bgr.astype(np.float32)
        skin_protect = masks.skin * self.preset.skin_protection

        # Sky enhancement (step 15)
        if self.preset.sky_boost > 0:
            sky_enhanced = self._enhance_sky(bgr)
            sky_mask = masks.sky * (1.0 - skin_protect)
            result = self._blend_region(result, sky_enhanced, sky_mask, self.preset.sky_boost)

        # Grass protection and enhancement (step 16)
        if self.preset.grass_boost > 0:
            grass_enhanced = self._enhance_grass(bgr)
            grass_mask = masks.grass * (1.0 - skin_protect)
            result = self._blend_region(
                result, grass_enhanced, grass_mask, self.preset.grass_boost
            )

        # Water enhancement (step 17)
        if self.preset.water_boost > 0:
            water_enhanced = self._enhance_water(bgr)
            water_mask = masks.water * (1.0 - skin_protect)
            result = self._blend_region(
                result, water_enhanced, water_mask, self.preset.water_boost
            )

        return np.clip(result, 0, 255).astype(np.uint8)

    def _enhance_sky(self, bgr: np.ndarray) -> np.ndarray:
        """Enhance sky: deeper blues, natural look."""
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.08, 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.05, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    def _enhance_grass(self, bgr: np.ndarray) -> np.ndarray:
        """Enhance grass: richer greens without oversaturation."""
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.10, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    def _enhance_water(self, bgr: np.ndarray) -> np.ndarray:
        """Enhance water: clearer blues."""
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        lab[:, :, 2] = np.clip(lab[:, :, 2] - 5, 0, 255)
        lab[:, :, 1] = np.clip(lab[:, :, 1] * 1.05, 0, 255)
        return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

    def _blend_region(
        self,
        base: np.ndarray,
        enhanced: np.ndarray,
        mask: np.ndarray,
        strength: float,
    ) -> np.ndarray:
        """Blend enhanced region using soft mask."""
        if mask.ndim == 2:
            mask_3 = np.stack([mask, mask, mask], axis=-1)
        else:
            mask_3 = mask
        alpha = mask_3 * strength
        return base * (1 - alpha) + enhanced.astype(np.float32) * alpha

    def _smart_sharpening(self, bgr: np.ndarray, skin_mask: np.ndarray) -> np.ndarray:
        """Step 19: Adaptive sharpening with skin protection."""
        strength = self.preset.sharpen / 100.0
        if strength < 0.01:
            return bgr

        blurred = cv2.GaussianBlur(bgr, (0, 0), 2)
        sharpened = cv2.addWeighted(bgr, 1 + strength, blurred, -strength, 0)

        if skin_mask is not None and skin_mask.max() > 0:
            mask = skin_mask.astype(np.float32)
            if mask.max() > 1:
                mask = mask / 255.0
            mask_3 = np.stack([mask, mask, mask], axis=-1)
            reduced_sharp = cv2.addWeighted(bgr, 1 + strength * 0.3, blurred, -strength * 0.3, 0)
            sharpened = sharpened.astype(np.float32) * (1 - mask_3 * 0.7) + (
                reduced_sharp.astype(np.float32) * mask_3 * 0.7
            )
            return np.clip(sharpened, 0, 255).astype(np.uint8)

        return sharpened

    def _jpeg_optimization(self, bgr: np.ndarray) -> np.ndarray:
        """Step 20: Final optimization pass."""
        # Slight contrast curve for natural output
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        l_float = l_ch.astype(np.float32)
        l_float = 255.0 * (l_float / 255.0) ** 0.98
        l_ch = np.clip(l_float, 0, 255).astype(np.uint8)
        lab = cv2.merge([l_ch, a_ch, b_ch])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def upscale_if_requested(self, bgr: np.ndarray, scale: int, use_ai: bool = False) -> np.ndarray:
        """Optional upscaling."""
        return upscale_image(bgr, scale=scale, use_ai=use_ai)
