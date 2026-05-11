from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np

from app.core.config import get_settings
from app.services.quality import estimate_hydration_and_richness

settings = get_settings()


class ThinkerInferenceService:
    """Lightweight heuristic analyzer used as a placeholder for imported thinker models.

    Replace this class with your real PyTorch model loader/inference pipeline.
    """

    def __init__(self) -> None:
        self.mode = settings.thinker_mode

    def _extract_classes(self, image_bgr: np.ndarray) -> list[str]:
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        # crude vegetation proxy by hue/saturation mask
        veg_mask = cv2.inRange(hsv, (25, 40, 20), (95, 255, 255))
        veg_ratio = float(np.mean(veg_mask > 0))

        classes: list[str] = ['soil_zone']
        if veg_ratio > 0.03:
            classes.append('plant_presence')
        if veg_ratio > 0.18:
            classes.append('dense_vegetation')
        return classes

    def _render_overlay(self, image_bgr: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        veg_mask = cv2.inRange(hsv, (25, 40, 20), (95, 255, 255))

        overlay = image_bgr.copy()
        overlay[veg_mask > 0] = (40, 190, 40)
        return cv2.addWeighted(image_bgr, 0.75, overlay, 0.25, 0)

    def predict(self, image_path: Path) -> dict:
        raw_image = cv2.imread(str(image_path))
        if raw_image is None:
            raise ValueError('Unable to read uploaded image')

        rendered = self._render_overlay(raw_image)
        output_name = f'thinker_{uuid4().hex}.jpg'
        output_path = Path(settings.outputs_dir) / output_name
        cv2.imwrite(str(output_path), rendered)

        classes_detected = self._extract_classes(raw_image)
        hydration, richness, notes = estimate_hydration_and_richness(raw_image, soil_mask=None)

        notes.insert(0, f'Thinker mode: {self.mode}')

        return {
            'output_visual_name': output_name,
            'classes_detected': classes_detected,
            'soil_hydration_pct_estimate': hydration,
            'soil_richness_score_estimate': richness,
            'soil_quality_notes': notes,
            'warning': 'Current thinker is heuristic-only. Plug imported PyTorch models for production reliability.'
        }

    def analyze_frame(self, frame_bgr: np.ndarray, save_visual: bool = False, visual_prefix: str = 'frame') -> dict:
        output_name = ''
        if save_visual:
            rendered = self._render_overlay(frame_bgr)
            output_name = f'{visual_prefix}_{uuid4().hex}.jpg'
            output_path = Path(settings.outputs_dir) / output_name
            cv2.imwrite(str(output_path), rendered)

        classes_detected = self._extract_classes(frame_bgr)
        hydration, richness, notes = estimate_hydration_and_richness(frame_bgr, soil_mask=None)
        notes.insert(0, f'Thinker mode: {self.mode}')

        return {
            'output_visual_name': output_name,
            'classes_detected': classes_detected,
            'soil_hydration_pct_estimate': hydration,
            'soil_richness_score_estimate': richness,
            'soil_quality_notes': notes,
            'warning': 'Current thinker is heuristic-only. Plug imported PyTorch models for production reliability.'
        }
