"""Scene segmentation for localized enhancement."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger("photo_enhancer.segmentation")


@dataclass
class SceneMasks:
    """Binary masks for scene regions (float32, 0-1)."""

    sky: np.ndarray
    water: np.ndarray
    grass: np.ndarray
    trees: np.ndarray
    people: np.ndarray
    skin: np.ndarray
    sand: np.ndarray
    buildings: np.ndarray

    def as_dict(self) -> dict[str, np.ndarray]:
        return {
            "sky": self.sky,
            "water": self.water,
            "grass": self.grass,
            "trees": self.trees,
            "people": self.people,
            "skin": self.skin,
            "sand": self.sand,
            "buildings": self.buildings,
        }


class SceneSegmenter:
    """Detect scene regions using color heuristics and optional AI models."""

    def __init__(self) -> None:
        from config import get_config

        self.config = get_config()
        self._yolo_model = None
        if self.config.segmentation.use_yolo:
            self._init_yolo()

    def _init_yolo(self) -> None:
        try:
            from ultralytics import YOLO

            model_path = self.config.models_path / "yolo11n.pt"
            self._yolo_model = YOLO(str(model_path) if model_path.exists() else "yolo11n.pt")
            logger.info("YOLO model loaded for segmentation")
        except Exception as exc:
            logger.warning("YOLO not available: %s", exc)
            self._yolo_model = None

    def segment(self, bgr: np.ndarray) -> SceneMasks:
        """Generate scene masks for an image."""
        h, w = bgr.shape[:2]
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        sky_u8 = self._detect_sky(hsv, h, w)
        water_u8 = self._detect_water(hsv, lab)
        grass_u8 = self._detect_grass(hsv, h, w)
        trees_u8 = self._detect_trees(hsv, grass_u8)
        sand_u8 = self._detect_sand(hsv, lab)
        skin_u8 = self._detect_skin(hsv, lab)
        people_u8 = self._detect_people(bgr, skin_u8, h, w)
        buildings_u8 = self._detect_buildings(gray, sky_u8, grass_u8, water_u8)

        if self._yolo_model is not None:
            self._refine_with_yolo(bgr, people_u8, sky_u8, water_u8)

        return SceneMasks(
            sky=self._smooth_mask(sky_u8),
            water=self._smooth_mask(water_u8),
            grass=self._smooth_mask(grass_u8),
            trees=self._smooth_mask(trees_u8),
            people=self._smooth_mask(people_u8),
            skin=self._smooth_mask(skin_u8),
            sand=self._smooth_mask(sand_u8),
            buildings=self._smooth_mask(buildings_u8),
        )

    def _detect_sky(self, hsv: np.ndarray, h: int, w: int) -> np.ndarray:
        """Detect sky using color, luminance gradient, and position."""
        blue_mask = cv2.inRange(hsv, (90, 15, 100), (135, 200, 255))
        light_mask = cv2.inRange(hsv, (0, 0, 170), (180, 70, 255))
        v_ch = hsv[:, :, 2].astype(np.float32)
        grad_y = cv2.Sobel(v_ch, cv2.CV_32F, 0, 1, ksize=3)
        smooth_upper = (grad_y > -5).astype(np.uint8) * 255
        position = np.zeros((h, w), dtype=np.float32)
        position[: max(1, h // 3), :] = 1.0
        position[h // 3 : h // 2, :] = 0.6
        combined = (
            blue_mask.astype(np.float32) * 0.5
            + light_mask.astype(np.float32) * 0.4
            + smooth_upper.astype(np.float32) * 0.3
        )
        combined *= position
        _, mask = cv2.threshold(combined.astype(np.uint8), 70, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    def _detect_water(self, hsv: np.ndarray, lab: np.ndarray) -> np.ndarray:
        """Detect water bodies."""
        blue = cv2.inRange(hsv, (85, 40, 40), (130, 255, 200))
        l_ch = lab[:, :, 0]
        dark_blue = (l_ch < 140).astype(np.uint8) * 255
        return cv2.bitwise_and(blue, dark_blue)

    def _detect_grass(self, hsv: np.ndarray, h: int, w: int) -> np.ndarray:
        """Detect grass and foliage."""
        green1 = cv2.inRange(hsv, (30, 30, 30), (85, 255, 200))
        green2 = cv2.inRange(hsv, (25, 20, 40), (95, 200, 255))
        mask = cv2.bitwise_or(green1, green2)
        position_weight = np.ones((h, w), dtype=np.uint8) * 255
        position_weight[:h // 4, :] = 0
        return cv2.bitwise_and(mask, position_weight)

    def _detect_trees(self, hsv: np.ndarray, grass_mask: np.ndarray) -> np.ndarray:
        """Detect tree regions (darker green areas)."""
        v_ch = hsv[:, :, 2]
        dark = (v_ch < 100).astype(np.uint8) * 255
        return cv2.bitwise_and(grass_mask, dark)

    def _detect_sand(self, hsv: np.ndarray, lab: np.ndarray) -> np.ndarray:
        """Detect sand/beach regions."""
        sand_hsv = cv2.inRange(hsv, (10, 20, 120), (35, 120, 255))
        l_ch = lab[:, :, 0]
        bright = (l_ch > 140).astype(np.uint8) * 255
        return cv2.bitwise_and(sand_hsv, bright)

    def _detect_skin(self, hsv: np.ndarray, lab: np.ndarray) -> np.ndarray:
        """Detect skin tone regions for protection."""
        ycrcb = cv2.cvtColor(cv2.cvtColor(lab, cv2.COLOR_LAB2BGR), cv2.COLOR_BGR2YCrCb)
        skin_ycrcb = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))
        skin_hsv = cv2.inRange(hsv, (0, 20, 60), (25, 180, 255))
        return cv2.bitwise_or(skin_ycrcb, skin_hsv)

    def _detect_people(
        self, bgr: np.ndarray, skin_mask: np.ndarray, h: int, w: int
    ) -> np.ndarray:
        """Detect people regions."""
        mask = np.zeros((h, w), dtype=np.uint8)
        try:
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            rects, _ = hog.detectMultiScale(bgr, winStride=(8, 8), padding=(8, 8), scale=1.05)
            for x, y, rw, rh in rects:
                cv2.rectangle(mask, (x, y), (x + rw, y + rh), 255, -1)
        except Exception as exc:
            logger.debug("HOG people detection skipped: %s", exc)
        return cv2.bitwise_or(mask, skin_mask)

    def _detect_buildings(
        self,
        gray: np.ndarray,
        sky: np.ndarray,
        grass: np.ndarray,
        water: np.ndarray,
    ) -> np.ndarray:
        """Detect building/structure regions via edges."""
        edges = cv2.Canny(gray, 50, 150)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        natural = cv2.bitwise_or(cv2.bitwise_or(sky, grass), water)
        not_natural = cv2.bitwise_not(natural)
        return cv2.bitwise_and(dilated, not_natural)

    def _refine_with_yolo(
        self,
        bgr: np.ndarray,
        people_mask: np.ndarray,
        sky_mask: np.ndarray,
        water_mask: np.ndarray,
    ) -> None:
        """Refine masks using YOLO detections."""
        if self._yolo_model is None:
            return
        try:
            results = self._yolo_model(bgr, verbose=False)
            h, w = bgr.shape[:2]
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    label = result.names.get(cls_id, "")
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w, x2), min(h, y2)
                    if label in ("person", "cat", "dog", "horse", "bird"):
                        cv2.rectangle(people_mask, (x1, y1), (x2, y2), 255, -1)
                    elif label == "boat":
                        cv2.rectangle(water_mask, (x1, y1), (x2, y2), 255, -1)
        except Exception as exc:
            logger.warning("YOLO refinement failed: %s", exc)

    def _smooth_mask(self, mask: np.ndarray) -> np.ndarray:
        """Smooth and normalize mask to float32 0-1."""
        blurred = cv2.GaussianBlur(mask, (15, 15), 0)
        return blurred.astype(np.float32) / 255.0
