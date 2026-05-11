from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session
from app.repositories.predictions import create_prediction_run, get_prediction_run, list_prediction_runs
from app.schemas.prediction import PredictionListItem, PredictionResponse
from app.services.thinker_inference import ThinkerInferenceService

router = APIRouter(prefix='/predictions', tags=['predictions'])
settings = get_settings()
inference_service = ThinkerInferenceService()


def _split_classes(csv_value: str) -> list[str]:
    if not csv_value:
        return []
    return [item for item in csv_value.split(',') if item]


@router.post('', response_model=PredictionResponse, status_code=201)
async def create_prediction(
    image: UploadFile = File(...),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    sampledAt: date | None = Form(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> PredictionResponse:
    if latitude is not None and (latitude < -90 or latitude > 90):
        raise HTTPException(status_code=400, detail='latitude must be between -90 and 90')

    if longitude is not None and (longitude < -180 or longitude > 180):
        raise HTTPException(status_code=400, detail='longitude must be between -180 and 180')

    suffix = Path(image.filename or 'upload.jpg').suffix or '.jpg'
    temp_name = f'upload_{uuid4().hex}{suffix}'
    temp_path = Path(settings.uploads_dir) / temp_name

    content = await image.read()
    temp_path.write_bytes(content)

    try:
        prediction = inference_service.predict(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)

    output_visual_url = f'/outputs/{prediction["output_visual_name"]}'
    row = await create_prediction_run(
        db,
        image_name=image.filename or temp_name,
        latitude=latitude,
        longitude=longitude,
        sampled_at=sampledAt,
        classes_detected=prediction['classes_detected'],
        hydration_pct=prediction['soil_hydration_pct_estimate'],
        richness_score=prediction['soil_richness_score_estimate'],
        warning=prediction['warning'],
        output_visual_url=output_visual_url,
    )

    if latitude is not None and longitude is not None:
        prediction['soil_quality_notes'].append(
            f'Geo context received ({latitude:.5f}, {longitude:.5f}); enrich with weather/soil layers next.'
        )

    if sampledAt is not None:
        prediction['soil_quality_notes'].append(f'Sample date: {sampledAt.isoformat()}')

    return PredictionResponse(
        id=row.id,
        created_at=row.created_at,
        segmentation_mask_url=output_visual_url,
        classes_detected=prediction['classes_detected'],
        soil_hydration_pct_estimate=prediction['soil_hydration_pct_estimate'],
        soil_richness_score_estimate=prediction['soil_richness_score_estimate'],
        soil_quality_notes=prediction['soil_quality_notes'],
        warning=prediction['warning'],
    )


@router.get('', response_model=list[PredictionListItem])
async def list_predictions(db: AsyncSession = Depends(get_db_session)) -> list[PredictionListItem]:
    rows = await list_prediction_runs(db)
    return [
        PredictionListItem(
            id=row.id,
            created_at=row.created_at,
            image_name=row.image_name,
            classes_detected=_split_classes(row.classes_detected_csv),
            soil_hydration_pct_estimate=row.hydration_pct_estimate,
            soil_richness_score_estimate=row.richness_score_estimate,
            output_visual_url=row.output_visual_url,
        )
        for row in rows
    ]


@router.get('/{prediction_id}', response_model=PredictionListItem)
async def get_prediction(prediction_id: int, db: AsyncSession = Depends(get_db_session)) -> PredictionListItem:
    row = await get_prediction_run(db, prediction_id)
    if row is None:
        raise HTTPException(status_code=404, detail='prediction not found')

    return PredictionListItem(
        id=row.id,
        created_at=row.created_at,
        image_name=row.image_name,
        classes_detected=_split_classes(row.classes_detected_csv),
        soil_hydration_pct_estimate=row.hydration_pct_estimate,
        soil_richness_score_estimate=row.richness_score_estimate,
        output_visual_url=row.output_visual_url,
    )
