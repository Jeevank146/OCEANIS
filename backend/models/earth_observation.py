from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class EarthObservation(Base, TimestampMixin):
    """
    Stores Earth Observation (EO), satellite telemetry, and remotely sensed
    oceanographic and atmospheric data.

    Accommodates satellite-derived multi-spectral variables such as Sea Surface
    Temperature (SST), ocean color/chlorophyll-a, cloud fraction, and radiation
    measurements. PostGIS-ready for spatial footprint extensions.
    """

    __tablename__ = "earth_observations"

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

    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    product_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    satellite_platform: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    sensor_instrument: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    sea_surface_temperature_c: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    chlorophyll_a_mg_m3: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    ocean_colour: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    cloud_cover_percent: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    solar_radiation_w_m2: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    data_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OBSERVATION_ASSIMILATION",
    )

    quality_flag: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="OPERATIONAL_QUALITY",
    )

    source_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    source_timezone: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<EarthObservation("
            f"id={self.id}, "
            f"lat={self.latitude}, "
            f"lon={self.longitude}, "
            f"product='{self.product_type}', "
            f"sst={self.sea_surface_temperature_c}C, "
            f"source='{self.source}'"
            f")>"
        )
