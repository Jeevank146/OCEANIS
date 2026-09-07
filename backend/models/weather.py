from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class WeatherObservation(Base, TimestampMixin):
    """
    Stores normalized weather observations retrieved by OCEANIS
    data connectors.
    """

    __tablename__ = "weather_observations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    temperature_c: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    humidity_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    wind_speed_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    wind_direction_deg: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    precipitation_mm: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    source_timezone: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<WeatherObservation("
            f"id={self.id}, "
            f"lat={self.latitude}, "
            f"lon={self.longitude}, "
            f"temperature={self.temperature_c}, "
            f"source='{self.source}'"
            f")>"
        )