from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class MarineOperation(Base, TimestampMixin):
    """
    Represents a planned, active, or assessed marine vessel operation
    (e.g., fishing trip, cargo transit, rescue support, coastal transfer).
    """

    __tablename__ = "marine_operations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    operation_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique operational identifier (e.g. OP_2026_09_001)",
    )

    operation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="TRANSIT",
        index=True,
        comment="FISHING_TRIP, TRANSIT, RESCUE_SUPPORT, SURVEY, PORT_TRANSFER, OTHER",
    )

    vessel_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="FISHING_VESSEL",
        comment="e.g. TRAWLER, CARGO, TANKER, PATROL_BOAT, RESEARCH_VESSEL, TRADITIONAL_BOAT",
    )

    vessel_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )

    origin_latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    origin_longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    destination_latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    destination_longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    planned_departure_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    estimated_speed_kmh: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Estimated vessel cruising speed in km/h",
    )

    estimated_distance_km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Estimated path distance in kilometers",
    )

    estimated_duration_minutes: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Estimated trip transit duration in minutes",
    )

    operational_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PLANNED",
        index=True,
        comment="PLANNED, ASSESSED, CAUTION, WARNING, BLOCKED, INSUFFICIENT_DATA",
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="MANUAL_INPUT",
    )

    data_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PLANNED",
        comment="PLANNED, LOGGED, SIMULATED",
    )

    def __repr__(self) -> str:
        return (
            f"<MarineOperation(id={self.id}, op_id='{self.operation_id}', "
            f"type='{self.operation_type}', status='{self.operational_status}', "
            f"dist_km={self.estimated_distance_km})>"
        )
