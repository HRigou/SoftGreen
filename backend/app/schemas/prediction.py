from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class PredictionCreatePayload(BaseModel):
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    sampledAt: date | None = None


class PredictionResponse(BaseModel):
    id: int
    created_at: datetime
    segmentation_mask_url: str
    classes_detected: list[str]
    soil_hydration_pct_estimate: float
    soil_richness_score_estimate: float
    soil_quality_notes: list[str]
    warning: str


class PredictionListItem(BaseModel):
    id: int
    created_at: datetime
    image_name: str
    classes_detected: list[str]
    soil_hydration_pct_estimate: float
    soil_richness_score_estimate: float
    output_visual_url: str


class VideoFrameMetric(BaseModel):
    frame_index: int
    timestamp_sec: float
    hydration_pct: float
    richness_score: float
    classes_detected: list[str]


class VideoReportResponse(BaseModel):
    video_name: str
    fps: float
    duration_sec: float
    frame_interval_sec: float
    frames_analyzed: int
    hydration_avg: float
    hydration_min: float
    hydration_max: float
    richness_avg: float
    richness_min: float
    richness_max: float
    hydration_trend: str
    richness_trend: str
    classes_frequency: dict[str, int]
    preview_visual_urls: list[str]
    frame_metrics: list[VideoFrameMetric]
    warning: str
    notes: list[str]
