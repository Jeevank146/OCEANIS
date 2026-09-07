from typing import Any, Optional

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class Port(Base, TimestampMixin):
    """
    Represents a coastal harbor, anchorage, or major/minor seaport in OCEANIS.
    Uses PostGIS geometry Point (SRID 4326) with spatial indexing.
    """

    __tablename__ = "ports"

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

    port_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="MAJOR_PORT",
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

    location: Mapped[Any] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        default="India",
        nullable=False,
    )

    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    district: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Port(id={self.id}, name='{self.name}', type='{self.port_type}', "
            f"lat={self.latitude}, lon={self.longitude})>"
        )


class RestrictedZone(Base, TimestampMixin):
    """
    Represents maritime security exclusion zones, firing ranges, naval exercise
    corridors, and non-navigable restricted zones.
    """

    __tablename__ = "restricted_zones"

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

    zone_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="MILITARY_EXCLUSION",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
        nullable=False,
    )

    authority: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<RestrictedZone(id={self.id}, name='{self.name}', type='{self.zone_type}')>"


class ProtectedZone(Base, TimestampMixin):
    """
    Represents Marine Protected Areas (MPAs), sensitive ecosystems, coral reefs,
    turtle nesting sanctuaries, and mangrove conservation sectors.
    """

    __tablename__ = "protected_zones"

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

    zone_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="MARINE_PROTECTED_AREA",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
        nullable=False,
    )

    authority: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ProtectedZone(id={self.id}, name='{self.name}', type='{self.zone_type}')>"
