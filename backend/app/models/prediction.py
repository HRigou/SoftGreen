from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PredictionRun(Base):
    __tablename__ = 'prediction_runs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)

    image_name: Mapped[str] = mapped_column(String(255))
    input_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    input_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    input_sampled_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    classes_detected_csv: Mapped[str] = mapped_column(Text, default='')
    hydration_pct_estimate: Mapped[float] = mapped_column(Float)
    richness_score_estimate: Mapped[float] = mapped_column(Float)
    warning: Mapped[str] = mapped_column(Text)

    output_visual_url: Mapped[str] = mapped_column(String(1024))
