from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'SoftGreen API'
    app_env: str = 'dev'
    database_url: str = 'postgresql+psycopg://softgreen:softgreen@db:5432/softgreen'

    # Paths are relative to backend/ working directory in Docker
    thinker_model_path: str = 'thinker/models/default.pt'
    thinker_mode: str = 'heuristic_v1'
    outputs_dir: str = 'thinker/outputs'
    uploads_dir: str = 'storage/uploads'


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    backend_root = Path(__file__).resolve().parents[2]

    thinker_model_path = Path(settings.thinker_model_path)
    if not thinker_model_path.is_absolute():
        settings.thinker_model_path = str((backend_root / thinker_model_path).resolve())

    outputs_path = Path(settings.outputs_dir)
    if not outputs_path.is_absolute():
        outputs_path = (backend_root / outputs_path).resolve()
    outputs_path.mkdir(parents=True, exist_ok=True)
    settings.outputs_dir = str(outputs_path)

    uploads_path = Path(settings.uploads_dir)
    if not uploads_path.is_absolute():
        uploads_path = (backend_root / uploads_path).resolve()
    uploads_path.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir = str(uploads_path)

    return settings
