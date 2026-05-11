from __future__ import annotations

import cv2
import numpy as np


def estimate_hydration_and_richness(image_bgr: np.ndarray, soil_mask: np.ndarray | None) -> tuple[float, float, list[str]]:
    if soil_mask is None:
        pixels = image_bgr
    else:
        pixels = image_bgr[soil_mask > 0]
        if pixels.size == 0:
            pixels = image_bgr

    hsv = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)

    v = hsv[:, 2].astype(np.float32) / 255.0
    s = hsv[:, 1].astype(np.float32) / 255.0
    hydration_proxy = (1.0 - v) * 0.7 + s * 0.3
    hydration_pct = float(np.clip(np.mean(hydration_proxy) * 100.0, 0.0, 100.0))

    gray = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2GRAY).reshape(-1)
    contrast = float(np.std(gray) / 64.0)
    darkness = float(1.0 - np.mean(gray) / 255.0)
    richness_proxy = float(np.clip((darkness * 0.6 + contrast * 0.4) * 100.0, 0.0, 100.0))

    notes: list[str] = []
    if hydration_pct < 30:
        notes.append('Low moisture proxy; irrigation may be needed.')
    elif hydration_pct > 70:
        notes.append('High moisture proxy; verify drainage and root oxygenation.')
    else:
        notes.append('Moderate moisture proxy.')

    if richness_proxy < 35:
        notes.append('Low richness proxy from color/texture; consider organic amendment.')
    elif richness_proxy > 70:
        notes.append('High richness proxy from color/texture.')
    else:
        notes.append('Medium richness proxy from color/texture.')

    return hydration_pct, richness_proxy, notes
