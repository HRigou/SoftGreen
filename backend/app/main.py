from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.models.prediction import PredictionRun

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(api_router)
app.mount('/outputs', StaticFiles(directory=settings.outputs_dir), name='outputs')


@app.on_event('startup')
async def on_startup() -> None:
    # Ensure DB schema exists for MVP without alembic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
