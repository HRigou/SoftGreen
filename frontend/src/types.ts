export type PredictionResponse = {
  id?: number;
  created_at?: string;
  segmentation_mask_url: string;
  classes_detected: string[];
  soil_hydration_pct_estimate: number;
  soil_richness_score_estimate: number;
  soil_quality_notes: string[];
  warning: string;
};

export type VideoFrameMetric = {
  frame_index: number;
  timestamp_sec: number;
  hydration_pct: number;
  richness_score: number;
  classes_detected: string[];
};

export type VideoReportResponse = {
  video_name: string;
  fps: number;
  duration_sec: number;
  frame_interval_sec: number;
  frames_analyzed: number;
  hydration_avg: number;
  hydration_min: number;
  hydration_max: number;
  richness_avg: number;
  richness_min: number;
  richness_max: number;
  hydration_trend: string;
  richness_trend: string;
  classes_frequency: Record<string, number>;
  preview_visual_urls: string[];
  frame_metrics: VideoFrameMetric[];
  warning: string;
  notes: string[];
};
