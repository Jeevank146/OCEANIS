from datetime import datetime
from typing import Any, Optional

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class MarineAlert(Base, TimestampMixin):
    """
    Represents official marine warnings, navigational warnings, and disaster alerts
    (e.g., INCOIS High Waves, IMD Cyclone Warnings, Tsunami Advisories).
    """

    __tablename__ = "marine_alerts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    alert_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    alert_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="e.g. HIGH_WAVES, SWELL_SURGE, GALE_WIND, CYCLONE, TSUNAMI, ROUGH_SEA",
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="INFO, CAUTION, WARNING, CRITICAL",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVE",
        index=True,
        comment="ACTIVE, EXPIRED, CANCELLED",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="INCOIS",
    )

    source_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OFFICIAL",
        comment="OFFICIAL, MODEL/FORECAST, DEMO/TEST, UNKNOWN",
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    effective_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )

    geometry: Mapped[Optional[Any]] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
        nullable=True,
    )

    source_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<MarineAlert(id={self.id}, alert_id='{self.alert_id}', "
            f"type='{self.alert_type}', severity='{self.severity}', status='{self.status}')>"
        )


class CycloneTrack(Base, TimestampMixin):
    """
    Represents historical, observed, and forecast cyclone track positions and intensity metrics.
    """

    __tablename__ = "cyclone_tracks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    cyclone_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Identifier for the tropical cyclone event (e.g. BOB_01_2026)",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    basin: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="NORTH_INDIAN_OCEAN",
        comment="e.g. BAY_OF_BENGAL, ARABIAN_SEA, NORTH_INDIAN_OCEAN",
    )

    classification: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="CYCLONIC_STORM",
        comment="DEPRESSION, DEEP_DEPRESSION, CYCLONIC_STORM, SEVERE_CYCLONIC_STORM, VERY_SEVERE_CYCLONIC_STORM, EXTREMELY_SEVERE_CYCLONIC_STORM, SUPER_CYCLONIC_STORM",
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

    geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    wind_speed_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Maximum sustained surface wind speed in km/h",
    )

    pressure_hpa: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Central barometric pressure in hPa",
    )

    movement_direction_deg: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Movement azimuth in degrees (0-360)",
    )

    movement_speed_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Translational speed in km/h",
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    forecast_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Target forecast valid time, or NULL if observed",
    )

    source: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="IMD",
    )

    source_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OFFICIAL",
        comment="OFFICIAL, MODEL/FORECAST, DEMO/TEST, UNKNOWN",
    )

    data_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OBSERVED",
        comment="OBSERVED, FORECAST, ESTIMATED",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<CycloneTrack(id={self.id}, cyclone_id='{self.cyclone_id}', name='{self.name}', "
            f"class='{self.classification}', lat={self.latitude}, lon={self.longitude})>"
        )


class HazardZone(Base, TimestampMixin):
    """
    Represents spatial hazard zones (e.g. cyclone impact zones, storm surge inundation zones,
    submerged reef hazards, high-wave risk coastal sectors).
    """

    __tablename__ = "hazard_zones"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    hazard_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="CYCLONE_IMPACT_ZONE, STORM_SURGE_ZONE, HIGH_WAVE_RISK, TSUNAMI_INUNDATION, SUBMERGED_REEF",
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="WARNING",
        index=True,
        comment="INFO, CAUTION, WARNING, CRITICAL",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="INCOIS",
    )

    source_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OFFICIAL",
        comment="OFFICIAL, MODEL/FORECAST, DEMO/TEST, UNKNOWN",
    )

    source_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    effective_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    effective_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<HazardZone(id={self.id}, name='{self.name}', type='{self.hazard_type}', "
            f"severity='{self.severity}', active={self.is_active})>"
        )
