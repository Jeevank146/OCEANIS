from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GeospatialCoordinateSchema(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to 180)")


# ---------------------------------------------------------------------------
# Port Schemas
# ---------------------------------------------------------------------------

class PortBase(BaseModel):
    name: str = Field(..., max_length=150, description="Port or harbor name")
    port_type: str = Field("MAJOR_PORT", max_length=50, description="Port classification (e.g. MAJOR_PORT, MINOR_PORT, ANCHORAGE)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Port latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Port longitude")
    country: str = Field("India", max_length=100, description="Country")
    state: Optional[str] = Field(None, max_length=100, description="State / Province")
    district: Optional[str] = Field(None, max_length=100, description="District / County")
    description: Optional[str] = Field(None, description="Port facility details, depths, cargo types")
    is_active: bool = Field(True, description="Whether the port is operational")


class PortCreate(PortBase):
    pass


class PortResponse(PortBase):
    id: int
    distance_km: Optional[float] = Field(None, description="Calculated distance in km when queried with proximity")
    location_geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON representation of location geometry")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Restricted Zone Schemas
# ---------------------------------------------------------------------------

class RestrictedZoneBase(BaseModel):
    name: str = Field(..., max_length=150, description="Name of the restricted area")
    zone_type: str = Field("MILITARY_EXCLUSION", max_length=100, description="Type (e.g. MILITARY_EXCLUSION, FIRING_RANGE, SECURITY_ZONE)")
    description: Optional[str] = Field(None, description="Detailed zone regulations and restrictions")
    authority: Optional[str] = Field(None, max_length=150, description="Governing authority (e.g. Indian Navy, DG Shipping)")
    is_active: bool = Field(True, description="Whether restriction is actively enforced")


class RestrictedZoneCreate(RestrictedZoneBase):
    geometry_wkt: Optional[str] = Field(None, description="Well-Known Text (WKT) geometry string")
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON polygon/multipolygon geometry dict")


class RestrictedZoneResponse(RestrictedZoneBase):
    id: int
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON boundary of the zone")
    distance_km: Optional[float] = Field(None, description="Distance from query point in km")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Protected Zone Schemas
# ---------------------------------------------------------------------------

class ProtectedZoneBase(BaseModel):
    name: str = Field(..., max_length=150, description="Protected area or sanctuary name")
    zone_type: str = Field("MARINE_PROTECTED_AREA", max_length=100, description="Classification (e.g. MARINE_PROTECTED_AREA, CORAL_REEF, TURTLE_SANCTUARY)")
    description: Optional[str] = Field(None, description="Conservation scope and ecological importance")
    authority: Optional[str] = Field(None, max_length=150, description="Conservation authority (e.g. MoEFCC, State Forest Dept)")
    is_active: bool = Field(True, description="Whether protection is actively designated")


class ProtectedZoneCreate(ProtectedZoneBase):
    geometry_wkt: Optional[str] = Field(None, description="Well-Known Text (WKT) geometry string")
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON polygon/multipolygon geometry dict")


class ProtectedZoneResponse(ProtectedZoneBase):
    id: int
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON boundary of the zone")
    distance_km: Optional[float] = Field(None, description="Distance from query point in km")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Proximity & Distance Schemas
# ---------------------------------------------------------------------------

class NearbyZonesResponse(BaseModel):
    center_latitude: float
    center_longitude: float
    radius_km: float
    restricted_zones: List[RestrictedZoneResponse] = Field(default_factory=list)
    protected_zones: List[ProtectedZoneResponse] = Field(default_factory=list)


class DistanceCalculationResponse(BaseModel):
    origin: GeospatialCoordinateSchema
    destination: GeospatialCoordinateSchema
    distance_km: float = Field(..., description="Geodesic distance in kilometers")
    distance_nautical_miles: float = Field(..., description="Geodesic distance in Nautical Miles (1 NM = 1.852 km)")
    calculation_method: str = Field("HAVERSINE_GEODESIC", description="Formula/method used")


# ---------------------------------------------------------------------------
# Navigation Assessment Schema
# ---------------------------------------------------------------------------

class RouteAssessmentResponse(BaseModel):
    origin: GeospatialCoordinateSchema
    destination: GeospatialCoordinateSchema
    distance_km: float
    distance_nautical_miles: float
    origin_in_restricted_zone: bool
    destination_in_restricted_zone: bool
    origin_in_protected_zone: bool
    destination_in_protected_zone: bool
    restricted_zone_intersection: bool
    protected_zone_intersection: bool
    intersecting_restricted_zones: List[str] = Field(default_factory=list)
    intersecting_protected_zones: List[str] = Field(default_factory=list)
    navigation_status: str = Field(..., description="Assessment status: CLEAR, CAUTION, or RESTRICTED")
    reasons: List[str] = Field(default_factory=list, description="Detailed diagnostic reasons explaining navigation status")
