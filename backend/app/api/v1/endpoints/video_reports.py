from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.prediction import VideoFrameMetric, VideoReportResponse
from app.services.thinker_inference import ThinkerInferenceService

router = APIRouter(prefix='/video-reports', tags=['video-reports'])
settings = get_settings()
inference_service = ThinkerInferenceService()


def _compute_trend(values: list[float]) -> str:
    if len(values) < 3:
        return 'insufficient_data'

    x = np.arange(len(values), dtype=np.float32)
    y = np.array(values, dtype=np.float32)
    slope = float(np.polyfit(x, y, 1)[0])

    if slope > 0.08:
        return 'increasing'
    if slope < -0.08:
        return 'decreasing'
    return 'stable'


@router.post('', response_model=VideoReportResponse)
async def create_video_report(
    video: UploadFile = File(...),
    frameIntervalSec: float = Form(default=1.0),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    sampledAt: date | None = Form(default=None),
) -> VideoReportResponse:
    if frameIntervalSec <= 0:
        raise HTTPException(status_code=400, detail='frameIntervalSec must be > 0')

    if latitude is not None and (latitude < -90 or latitude > 90):
        raise HTTPException(status_code=400, detail='latitude must be between -90 and 90')

    if longitude is not None and (longitude < -180 or longitude > 180):
        raise HTTPException(status_code=400, detail='longitude must be between -180 and 180')

    suffix = Path(video.filename or 'upload.mp4').suffix or '.mp4'
    temp_name = f'video_{uuid4().hex}{suffix}'
    temp_path = Path(settings.uploads_dir) / temp_name

    content = await video.read()
    temp_path.write_bytes(content)

    cap = cv2.VideoCapture(str(temp_path))
    if not cap.isOpened():
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail='Unable to open video file')

    fps = float(cap.get(cv2.CAP_PROP_FPS))
    if fps <= 0:
        fps = 25.0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration_sec = float(total_frames / fps) if total_frames > 0 else 0.0

    step = max(1, int(round(fps * frameIntervalSec)))

    frame_index = 0
    frame_metrics: list[VideoFrameMetric] = []
    hydration_values: list[float] = []
    richness_values: list[float] = []
    class_counter: Counter[str] = Counter()
    preview_visual_urls: list[str] = []

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_index % step == 0:
                save_preview = len(preview_visual_urls) < 3
                analysis = inference_service.analyze_frame(
                    frame,
                    save_visual=save_preview,
                    visual_prefix='video_frame',
                )

                if save_preview and analysis['output_visual_name']:
                    preview_visual_urls.append(f"/outputs/{analysis['output_visual_name']}")

                hydration = float(analysis['soil_hydration_pct_estimate'])
                richness = float(analysis['soil_richness_score_estimate'])
                classes_detected = analysis['classes_detected']

                hydration_values.append(hydration)
                richness_values.append(richness)
                class_counter.update(classes_detected)

                frame_metrics.append(
                    VideoFrameMetric(
                        frame_index=frame_index,
                        timestamp_sec=round(frame_index / fps, 3),
                        hydration_pct=round(hydration, 4),
                        richness_score=round(richness, 4),
                        classes_detected=classes_detected,
                    )
                )

            frame_index += 1
    finally:
        cap.release()
        temp_path.unlink(missing_ok=True)

    if not frame_metrics:
        raise HTTPException(status_code=400, detail='No frame could be analyzed from this video')

    notes = [
        f'Analyzed 1 frame every {frameIntervalSec:.2f}s.',
        'Hydration/richness are visual proxies and not laboratory soil measurements.',
    ]

    if latitude is not None and longitude is not None:
        notes.append(f'Geo context received ({latitude:.5f}, {longitude:.5f}).')

    if sampledAt is not None:
        notes.append(f'Sample date: {sampledAt.isoformat()}')

    hydration_avg = float(np.mean(hydration_values))
    richness_avg = float(np.mean(richness_values))

    return VideoReportResponse(
        video_name=video.filename or temp_name,
        fps=round(fps, 4),
        duration_sec=round(duration_sec, 3),
        frame_interval_sec=frameIntervalSec,
        frames_analyzed=len(frame_metrics),
        hydration_avg=round(hydration_avg, 4),
        hydration_min=round(float(np.min(hydration_values)), 4),
        hydration_max=round(float(np.max(hydration_values)), 4),
        richness_avg=round(richness_avg, 4),
        richness_min=round(float(np.min(richness_values)), 4),
        richness_max=round(float(np.max(richness_values)), 4),
        hydration_trend=_compute_trend(hydration_values),
        richness_trend=_compute_trend(richness_values),
        classes_frequency=dict(sorted(class_counter.items())),
        preview_visual_urls=preview_visual_urls,
        frame_metrics=frame_metrics,
        warning='Video report uses visual proxy indicators; validate with sensor/lab data.',
        notes=notes,
    )
