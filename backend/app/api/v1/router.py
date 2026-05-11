from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.predictions import router as predictions_router
from app.api.v1.endpoints.video_reports import router as video_reports_router

router = APIRouter(prefix='/api/v1')
router.include_router(health_router)
router.include_router(predictions_router)
router.include_router(video_reports_router)
