import { FormEvent, useMemo, useState } from 'react';
import { submitSoilVideo } from './api/client';
import type { VideoFrameMetric, VideoReportResponse } from './types';

function buildPolyline(values: number[], width: number, height: number): string {
  if (values.length === 0) {
    return '';
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(max - min, 1e-6);

  return values
    .map((value, idx) => {
      const x = (idx / Math.max(values.length - 1, 1)) * width;
      const y = height - ((value - min) / span) * height;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');
}

function MetricChart({ title, color, values }: { title: string; color: string; values: number[] }) {
  const width = 460;
  const height = 140;
  const polyline = buildPolyline(values, width, height);

  return (
    <div className="chart">
      <h3>{title}</h3>
      {values.length === 0 ? (
        <p>No values.</p>
      ) : (
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}>
          <polyline fill="none" stroke={color} strokeWidth="3" points={polyline} />
        </svg>
      )}
    </div>
  );
}

function formatClassesFrequency(classesFrequency: Record<string, number>): string {
  const entries = Object.entries(classesFrequency);
  if (entries.length === 0) {
    return 'none';
  }

  return entries
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([name, count]) => `${name}: ${count}`)
    .join(' | ');
}

function App() {
  const [video, setVideo] = useState<File | null>(null);
  const [frameIntervalSec, setFrameIntervalSec] = useState('1');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [sampledAt, setSampledAt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<VideoReportResponse | null>(null);

  const previewUrl = useMemo(() => {
    if (!video) {
      return '';
    }
    return URL.createObjectURL(video);
  }, [video]);

  const frameMetrics: VideoFrameMetric[] = result?.frame_metrics ?? [];
  const hydrationSeries = frameMetrics.map((point) => point.hydration_pct);
  const richnessSeries = frameMetrics.map((point) => point.richness_score);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();

    if (!video) {
      setError('Please select a video first.');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const report = await submitSoilVideo({
        video,
        frameIntervalSec: frameIntervalSec ? Number(frameIntervalSec) : undefined,
        latitude: latitude ? Number(latitude) : undefined,
        longitude: longitude ? Number(longitude) : undefined,
        sampledAt: sampledAt || undefined
      });
      setResult(report);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page">
      <section className="card">
        <h1>SoftGreen Video Analyzer</h1>
        <p>Upload video, extract frames, analyze each frame, and generate a trend report.</p>

        <form onSubmit={onSubmit} className="form">
          <label>
            Soil video
            <input
              type="file"
              accept="video/*"
              onChange={(event) => setVideo(event.target.files?.[0] ?? null)}
            />
          </label>

          <label>
            Frame interval (seconds)
            <input
              type="number"
              min="0.1"
              step="0.1"
              value={frameIntervalSec}
              onChange={(event) => setFrameIntervalSec(event.target.value)}
            />
          </label>

          <label>
            Latitude (optional)
            <input type="number" step="0.000001" value={latitude} onChange={(event) => setLatitude(event.target.value)} />
          </label>

          <label>
            Longitude (optional)
            <input type="number" step="0.000001" value={longitude} onChange={(event) => setLongitude(event.target.value)} />
          </label>

          <label>
            Sampling date (optional)
            <input type="date" value={sampledAt} onChange={(event) => setSampledAt(event.target.value)} />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? 'Analyzing video...' : 'Generate report'}
          </button>
        </form>

        {error ? <p className="error">{error}</p> : null}
      </section>

      <section className="card preview">
        <h2>Video preview</h2>
        {previewUrl ? <video controls src={previewUrl} /> : <p>No video selected</p>}
      </section>

      <section className="card results">
        <h2>Report</h2>
        {!result ? <p>No report generated yet.</p> : null}
        {result ? (
          <>
            <p>
              Video: <strong>{result.video_name}</strong>
            </p>
            <p>
              Duration: {result.duration_sec.toFixed(2)}s | FPS: {result.fps.toFixed(2)} | Frames analyzed: {result.frames_analyzed}
            </p>
            <p>
              Hydration avg/min/max: {result.hydration_avg.toFixed(1)} / {result.hydration_min.toFixed(1)} / {result.hydration_max.toFixed(1)}
            </p>
            <p>
              Richness avg/min/max: {result.richness_avg.toFixed(1)} / {result.richness_min.toFixed(1)} / {result.richness_max.toFixed(1)}
            </p>
            <p>
              Hydration trend: <strong>{result.hydration_trend}</strong> | Richness trend: <strong>{result.richness_trend}</strong>
            </p>
            <p>Classes frequency: {formatClassesFrequency(result.classes_frequency)}</p>
            <p className="warn">{result.warning}</p>

            <div className="charts-grid">
              <MetricChart title="Hydration trend" color="#0f766e" values={hydrationSeries} />
              <MetricChart title="Richness trend" color="#7c3aed" values={richnessSeries} />
            </div>

            {result.preview_visual_urls.length > 0 ? (
              <>
                <h3>Analyzed frame previews</h3>
                <div className="preview-grid">
                  {result.preview_visual_urls.map((url) => (
                    <img key={url} src={url} alt="Analyzed frame" />
                  ))}
                </div>
              </>
            ) : null}

            <h3>Notes</h3>
            <ul>
              {result.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          </>
        ) : null}
      </section>
    </main>
  );
}

export default App;
