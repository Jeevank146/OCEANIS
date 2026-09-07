from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class MarineObservation(Base, TimestampMixin):
    """
    Stores normalized oceanographic and marine observations/forecasts
    retrieved by OCEANIS data connectors.

    Designed to accommodate multi-parameter ocean intelligence, including
    sea state (waves, swell, wind waves), ocean dynamics (currents), and
    thermal characteristics (sea surface temperature).
    """

    __tablename__ = "marine_observations"

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

    # Wave metrics
    wave_height_m: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    wave_direction_deg: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    wave_period_s: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Swell metrics
    swell_wave_height_m: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    swell_wave_direction_deg: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    swell_wave_period_s: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Wind wave metrics
    wind_wave_height_m: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    wind_wave_direction_deg: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    wind_wave_period_s: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Ocean currents
    ocean_current_velocity_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    ocean_current_direction_deg: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Thermal metrics
    sea_surface_temperature_c: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Ocean chemistry and extra physics
    salinity_psu: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    sea_level_m: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    # Provenance and metadata
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    data_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OBSERVATION",
    )

    quality_flag: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="REALTIME",
    )

    source_timezone: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<MarineObservation("
            f"id={self.id}, "
            f"lat={self.latitude}, "
            f"lon={self.longitude}, "
            f"wave_height={self.wave_height_m}m, "
            f"sst={self.sea_surface_temperature_c}C, "
            f"source='{self.source}'"
            f")>"
        )
