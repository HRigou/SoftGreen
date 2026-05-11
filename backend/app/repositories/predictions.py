from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PredictionRun


async def create_prediction_run(
    db: AsyncSession,
    *,
    image_name: str,
    latitude: float | None,
    longitude: float | None,
    sampled_at,
    classes_detected: list[str],
    hydration_pct: float,
    richness_score: float,
    warning: str,
    output_visual_url: str,
) -> PredictionRun:
    row = PredictionRun(
        image_name=image_name,
        input_latitude=latitude,
        input_longitude=longitude,
        input_sampled_at=sampled_at,
        classes_detected_csv=','.join(classes_detected),
        hydration_pct_estimate=hydration_pct,
        richness_score_estimate=richness_score,
        warning=warning,
        output_visual_url=output_visual_url,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_prediction_runs(db: AsyncSession, limit: int = 20) -> list[PredictionRun]:
    query = select(PredictionRun).order_by(desc(PredictionRun.created_at)).limit(limit)
    rows = await db.execute(query)
    return list(rows.scalars().all())


async def get_prediction_run(db: AsyncSession, run_id: int) -> PredictionRun | None:
    row = await db.execute(select(PredictionRun).where(PredictionRun.id == run_id))
    return row.scalar_one_or_none()
