import type { PredictionResponse, VideoReportResponse } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function submitSoilSample(payload: {
  image: File;
  latitude?: number;
  longitude?: number;
  sampledAt?: string;
}): Promise<PredictionResponse> {
  const form = new FormData();
  form.append('image', payload.image);

  if (payload.latitude !== undefined) {
    form.append('latitude', String(payload.latitude));
  }

  if (payload.longitude !== undefined) {
    form.append('longitude', String(payload.longitude));
  }

  if (payload.sampledAt) {
    form.append('sampledAt', payload.sampledAt);
  }

  const response = await fetch(`${API_BASE}/api/v1/predictions`, {
    method: 'POST',
    body: form
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Prediction request failed');
  }

  const data = (await response.json()) as PredictionResponse;

  if (data.segmentation_mask_url.startsWith('/')) {
    data.segmentation_mask_url = `${API_BASE}${data.segmentation_mask_url}`;
  }

  return data;
}

export async function submitSoilVideo(payload: {
  video: File;
  frameIntervalSec?: number;
  latitude?: number;
  longitude?: number;
  sampledAt?: string;
}): Promise<VideoReportResponse> {
  const form = new FormData();
  form.append('video', payload.video);

  if (payload.frameIntervalSec !== undefined) {
    form.append('frameIntervalSec', String(payload.frameIntervalSec));
  }

  if (payload.latitude !== undefined) {
    form.append('latitude', String(payload.latitude));
  }

  if (payload.longitude !== undefined) {
    form.append('longitude', String(payload.longitude));
  }

  if (payload.sampledAt) {
    form.append('sampledAt', payload.sampledAt);
  }

  const response = await fetch(`${API_BASE}/api/v1/video-reports`, {
    method: 'POST',
    body: form
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Video report request failed');
  }

  const data = (await response.json()) as VideoReportResponse;
  data.preview_visual_urls = data.preview_visual_urls.map((url) => (url.startsWith('/') ? `${API_BASE}${url}` : url));
  return data;
}
