from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
DATASET = ROOT / 'data' / 'dataset'
if not DATASET.exists():
    candidates = sorted((ROOT / 'data').glob('*/data.yaml'))
    if not candidates:
        raise FileNotFoundError("No dataset folder found under data/ (expected data/<name>/data.yaml)")
    DATASET = candidates[0].parent
OUT_DIR = ROOT / 'data' / 'enriched'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_labels(label_path: Path) -> list[tuple[int, float, float, float, float]]:
    rows = []
    for line in label_path.read_text(encoding='utf-8', errors='ignore').splitlines():
        parts = line.strip().split()
        if len(parts) != 5:
            continue
        cls, x, y, w, h = parts
        rows.append((int(float(cls)), float(x), float(y), float(w), float(h)))
    return rows


def proxy_metrics(image_bgr: np.ndarray) -> tuple[float, float]:
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    v = hsv[:, :, 2].astype(np.float32) / 255.0
    s = hsv[:, :, 1].astype(np.float32) / 255.0

    hydration = float(np.clip(np.mean((1.0 - v) * 0.7 + s * 0.3) * 100.0, 0.0, 100.0))

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    contrast = float(np.std(gray) / 64.0)
    darkness = float(1.0 - np.mean(gray) / 255.0)
    richness = float(np.clip((darkness * 0.6 + contrast * 0.4) * 100.0, 0.0, 100.0))

    return hydration, richness


def enrich_subset(subset: str) -> tuple[list[dict], Counter]:
    image_dir = DATASET / 'images' / subset
    label_dir = DATASET / 'labels' / subset

    class_counter: Counter = Counter()
    records: list[dict] = []

    for image_path in sorted(image_dir.glob('*.jpg')):
        label_path = label_dir / f'{image_path.stem}.txt'
        if not label_path.exists():
            continue

        image = cv2.imread(str(image_path))
        if image is None:
            continue

        labels = parse_labels(label_path)
        if not labels:
            continue

        classes = [row[0] for row in labels]
        class_counter.update(classes)

        hydration, richness = proxy_metrics(image)

        counts = Counter(classes)
        total = sum(counts.values())
        probs = np.array([v / total for v in counts.values()], dtype=np.float32)
        diversity = float(-np.sum(probs * np.log2(probs + 1e-8)) / np.log2(max(len(counts), 2)))

        bbox_area_ratio = float(np.mean([w * h for _, _, _, w, h in labels]))

        records.append(
            {
                'subset': subset,
                'image_path': str(image_path.relative_to(ROOT)),
                'label_path': str(label_path.relative_to(ROOT)),
                'box_count': len(labels),
                'class_ids': ';'.join(str(c) for c in sorted(set(classes))),
                'hydration_proxy_pct': round(hydration, 4),
                'richness_proxy_score': round(richness, 4),
                'plant_diversity_index': round(diversity, 4),
                'mean_bbox_area_ratio': round(bbox_area_ratio, 6),
            }
        )

    return records, class_counter


def main() -> None:
    all_records: list[dict] = []
    total_counter: Counter = Counter()

    for subset in ('train', 'val'):
        records, counter = enrich_subset(subset)
        all_records.extend(records)
        total_counter.update(counter)

    csv_path = OUT_DIR / 'soil_dataset_enriched.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                'subset',
                'image_path',
                'label_path',
                'box_count',
                'class_ids',
                'hydration_proxy_pct',
                'richness_proxy_score',
                'plant_diversity_index',
                'mean_bbox_area_ratio',
            ],
        )
        writer.writeheader()
        writer.writerows(all_records)

    summary = {
        'num_records': len(all_records),
        'class_distribution': {str(k): int(v) for k, v in sorted(total_counter.items())},
        'notes': [
            'hydration_proxy_pct and richness_proxy_score are visual proxies, not lab ground truth.',
            'Use sensor/lab/geospatial data for scientific-grade targets.',
        ],
    }

    (OUT_DIR / 'soil_dataset_enriched_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(f'Wrote {csv_path} with {len(all_records)} rows')


if __name__ == '__main__':
    main()
