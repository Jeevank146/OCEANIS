from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DisasterCoordinateSchema(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to 180)")


# ---------------------------------------------------------------------------
# Marine Alert Schemas
# ---------------------------------------------------------------------------

class MarineAlertBase(BaseModel):
    alert_id: str = Field(..., max_length=100, description="Unique identifier for the alert")
    title: str = Field(..., max_length=255, description="Alert title/headline")
    alert_type: str = Field(..., max_length=100, description="Type (e.g. HIGH_WAVES, SWELL_SURGE, GALE_WIND, CYCLONE, TSUNAMI, ROUGH_SEA)")
    severity: str = Field(..., max_length=50, description="Severity (INFO, CAUTION, WARNING, CRITICAL)")
    status: str = Field("ACTIVE", max_length=50, description="Status (ACTIVE, EXPIRED, CANCELLED)")
    description: Optional[str] = Field(None, description="Detailed advisory or bulletin text")
    source: str = Field("INCOIS", max_length=150, description="Issuing agency or organization")
    source_category: str = Field("OFFICIAL", max_length=50, description="Category: OFFICIAL, MODEL/FORECAST, DEMO/TEST, UNKNOWN")
    issued_at: datetime = Field(..., description="Timestamp when alert was issued")
    effective_from: datetime = Field(..., description="Timestamp when alert becomes active")
    effective_until: Optional[datetime] = Field(None, description="Timestamp when alert expires")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Focal latitude if point-specific")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Focal longitude if point-specific")
    source_url: Optional[str] = Field(None, max_length=500, description="Link to official advisory bulletin")
    is_active: bool = Field(True, description="Whether alert is active")


class MarineAlertCreate(MarineAlertBase):
    geometry_wkt: Optional[str] = Field(None, description="Well-Known Text (WKT) geometry string (Point or Polygon)")
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON geometry object")


class MarineAlertResponse(MarineAlertBase):
    id: int
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON geometry")
    distance_km: Optional[float] = Field(None, description="Distance in km to focal coordinate if proximity query")
    freshness: str = Field("UNKNOWN", description="Data freshness evaluation: FRESH, AGING, STALE, EXPIRED, UNKNOWN")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Cyclone Track Schemas
# ---------------------------------------------------------------------------

class CycloneTrackBase(BaseModel):
    cyclone_id: str = Field(..., max_length=100, description="Cyclone identifier (e.g. BOB_01_2026)")
    name: str = Field(..., max_length=100, description="Cyclone name (e.g. ASNA, MICHAUNG)")
    basin: str = Field("NORTH_INDIAN_OCEAN", max_length=50, description="Ocean basin")
    classification: str = Field("CYCLONIC_STORM", max_length=100, description="Intensity classification")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Track point latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Track point longitude")
    wind_speed_kmh: Optional[float] = Field(None, ge=0.0, description="Maximum sustained wind speed in km/h")
    pressure_hpa: Optional[float] = Field(None, ge=800.0, le=1100.0, description="Central pressure in hPa")
    movement_direction_deg: Optional[float] = Field(None, ge=0.0, le=360.0, description="Direction of movement in degrees")
    movement_speed_kmh: Optional[float] = Field(None, ge=0.0, description="Translation speed in km/h")
    observed_at: datetime = Field(..., description="Observation timestamp")
    forecast_time: Optional[datetime] = Field(None, description="Forecast target timestamp if forecast point")
    source: str = Field("IMD", max_length=150, description="Data provider (e.g. IMD, JTWC)")
    source_category: str = Field("OFFICIAL", max_length=50, description="Category: OFFICIAL, MODEL/FORECAST, DEMO/TEST, UNKNOWN")
    data_type: str = Field("OBSERVED", max_length=50, description="Data type: OBSERVED, FORECAST, ESTIMATED")
    is_active: bool = Field(True, description="Whether cyclone is active")


class CycloneTrackCreate(CycloneTrackBase):
    pass


class CycloneTrackResponse(CycloneTrackBase):
    id: int
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON point geometry")
    distance_km: Optional[float] = Field(None, description="Distance from requested coordinates in km")
    freshness: str = Field("UNKNOWN", description="Data freshness evaluation: FRESH, AGING, STALE, EXPIRED, UNKNOWN")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Hazard Zone Schemas
# ---------------------------------------------------------------------------

class HazardZoneBase(BaseModel):
    name: str = Field(..., max_length=150, description="Hazard zone designation name")
    hazard_type: str = Field(..., max_length=100, description="Hazard type (e.g. CYCLONE_IMPACT_ZONE, STORM_SURGE_ZONE, HIGH_WAVE_RISK)")
    severity: str = Field("WARNING", max_length=50, description="Severity rating: INFO, CAUTION, WARNING, CRITICAL")
    description: Optional[str] = Field(None, description="Hazard description, warning notes, impact description")
    source: str = Field("INCOIS", max_length=150, description="Issuing agency or model")
    source_category: str = Field("OFFICIAL", max_length=50, description="Category: OFFICIAL, MODEL/FORECAST, DEMO/TEST, UNKNOWN")
    source_url: Optional[str] = Field(None, max_length=500, description="Link to source bulletin")
    effective_from: Optional[datetime] = Field(None, description="Activation timestamp")
    effective_until: Optional[datetime] = Field(None, description="Expiry timestamp")
    is_active: bool = Field(True, description="Whether hazard zone is actively enforced")


class HazardZoneCreate(HazardZoneBase):
    geometry_wkt: Optional[str] = Field(None, description="Well-Known Text (WKT) geometry string")
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON polygon or multipolygon")


class HazardZoneResponse(HazardZoneBase):
    id: int
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON polygon/multipolygon geometry")
    distance_km: Optional[float] = Field(None, description="Distance to nearest boundary point in km")
    contains_point: Optional[bool] = Field(None, description="True if query point is inside this hazard zone")
    freshness: str = Field("UNKNOWN", description="Data freshness evaluation: FRESH, AGING, STALE, EXPIRED, UNKNOWN")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Safety Assessment Schema
# ---------------------------------------------------------------------------

class SafetyAssessmentResponse(BaseModel):
    location: DisasterCoordinateSchema
    status: str = Field(..., description="Safety assessment status: SAFE, CAUTION, WARNING, CRITICAL, INSUFFICIENT_DATA")
    active_alerts: List[MarineAlertResponse] = Field(default_factory=list, description="Active alerts affecting this area")
    nearby_hazards: List[HazardZoneResponse] = Field(default_factory=list, description="Hazard zones containing or near the location")
    nearby_cyclones: List[CycloneTrackResponse] = Field(default_factory=list, description="Active cyclone tracks within proximity")
    nearest_safe_port: Optional[Dict[str, Any]] = Field(None, description="Nearest known port / coastal refuge with distance")
    data_freshness: str = Field(..., description="Overall data freshness: FRESH, AGING, STALE, EXPIRED, UNKNOWN, INSUFFICIENT")
    confidence: str = Field(..., description="Assessment confidence: HIGH, MEDIUM, LOW, NONE")
    reasons: List[str] = Field(default_factory=list, description="Diagnostic reasons justifying the deterministic assessment")
    assessment_timestamp: datetime = Field(..., description="Timestamp when safety assessment was computed")

    model_config = ConfigDict(from_attributes=True)
