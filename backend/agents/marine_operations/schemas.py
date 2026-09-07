from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MarineOperationsQuery(BaseModel):
    """
    Input query payload for Marine Operations Intelligence Agent.
    """
    origin_latitude: float = Field(..., ge=-90.0, le=90.0, description="Origin latitude in decimal degrees (-90.0 to 90.0)")
    origin_longitude: float = Field(..., ge=-180.0, le=180.0, description="Origin longitude in decimal degrees (-180.0 to 180.0)")
    destination_latitude: float = Field(..., ge=-90.0, le=90.0, description="Destination latitude in decimal degrees (-90.0 to 90.0)")
    destination_longitude: float = Field(..., ge=-180.0, le=180.0, description="Destination longitude in decimal degrees (-180.0 to 180.0)")
    vessel_type: Optional[str] = Field("FISHING_VESSEL", description="Vessel classification (e.g. FISHING_VESSEL, TRAWLER, CARGO, PATROL_BOAT, TRADITIONAL_BOAT)")
    vessel_name: Optional[str] = Field(None, description="Optional vessel identifier name")
    speed_kmh: Optional[float] = Field(20.0, ge=0.5, le=150.0, description="Cruising speed in km/h (default 20.0 km/h)")
    planned_departure_at: Optional[str] = Field(None, description="Optional target departure ISO 8601 timestamp")
    operation_type: Optional[str] = Field("TRANSIT", description="Operation classification: TRANSIT, FISHING_TRIP, RESCUE_SUPPORT, SURVEY, PORT_TRANSFER")
    notes: Optional[str] = Field(None, description="Optional operational remarks")


class OperationalEvidenceItem(BaseModel):
    """
    Standardized traceable operational evidence item with provenance and regulatory attributes.
    """
    factor: str = Field(..., description="Operational factor identifier (e.g. route_distance, transit_duration, restricted_zone_intersection, hazard_zone_intersection, wave_state, wind_speed, cyclone_proximity)")
    title: Optional[str] = Field(None, description="Title or descriptor of the operational entity")
    entity_type: str = Field("ROUTE_GEOMETRY", description="ROUTE_GEOMETRY, REGULATORY_ZONE, HAZARD_ZONE, OFFICIAL_ALERT, CYCLONE_TRACK, MARINE_TELEMETRY, WEATHER_TELEMETRY, SAFE_PORT")
    severity: str = Field("NORMAL", description="NORMAL, INFO, CAUTION, WARNING, CRITICAL, UNKNOWN")
    source: str = Field("PostGIS Navigation / INCOIS / IMD", description="Data authority or provider")
    source_category: str = Field("OFFICIAL", description="OFFICIAL, MODEL/FORECAST, DEMO/TEST, UNKNOWN")
    data_type: str = Field("OPERATIONAL_CALCULATION", description="OPERATIONAL_CALCULATION, SPATIAL_REGULATORY, OFFICIAL_WARNING, OBSERVED_HAZARD, FORECAST_HAZARD")
    observed_at: Optional[str] = Field(None, description="ISO timestamp of observation or telemetry validity")
    distance_km: Optional[float] = Field(None, description="Distance from origin or along route in kilometers")
    duration_minutes: Optional[float] = Field(None, description="Estimated duration in minutes if applicable")
    spatial_relationship: str = Field("LINE_TRAJECTORY", description="LINE_TRAJECTORY, CONTAINS, INTERSECTS, NEARBY, PROXIMITY")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Deterministic confidence score between 0.0 and 1.0")
    freshness: str = Field("FRESH", description="Freshness evaluation: FRESH, AGING, STALE, UNAVAILABLE")
    notes: Optional[str] = Field(None, description="Diagnostic operational context note")


class RouteOperationalSummary(BaseModel):
    """
    Detailed geometric, temporal, and clearance summary for the planned marine operation route.
    """
    distance_km: float = Field(..., description="Geodesic route distance in kilometers")
    distance_nautical_miles: float = Field(..., description="Route distance in nautical miles")
    speed_kmh: Optional[float] = Field(None, description="Vessel cruising speed in km/h")
    estimated_duration_minutes: Optional[float] = Field(None, description="Estimated transit duration in minutes")
    estimated_duration_hours: Optional[float] = Field(None, description="Estimated transit duration in hours")
    planned_departure_at: Optional[str] = Field(None, description="Planned departure timestamp")
    estimated_arrival_at: Optional[str] = Field(None, description="Estimated arrival timestamp at destination")
    restricted_zone_intersection: bool = False
    protected_zone_intersection: bool = False
    hazard_zone_intersection: bool = False
    origin_in_restricted_zone: bool = False
    destination_in_restricted_zone: bool = False
    origin_in_protected_zone: bool = False
    destination_in_protected_zone: bool = False
    intersecting_restricted_zones: List[str] = Field(default_factory=list)
    intersecting_protected_zones: List[str] = Field(default_factory=list)
    intersecting_hazard_zones: List[str] = Field(default_factory=list)
    alternative_route_available: bool = False
    alternative_route_suggestion: Optional[str] = None


class MarineOperationsAssessmentResponse(BaseModel):
    """
    Structured response generated by the Marine Operations Intelligence Agent.
    """
    agent: str = Field("marine_operations", description="Name of the domain agent")
    origin: Dict[str, float] = Field(..., description="Origin coordinate latitude and longitude")
    destination: Dict[str, float] = Field(..., description="Destination coordinate latitude and longitude")
    operational_status: str = Field(..., description="Deterministic operational status: CLEAR, CAUTION, WARNING, BLOCKED, INSUFFICIENT_DATA")
    operational_risk: str = Field("LOW", description="Overall operational risk level: LOW, MODERATE, HIGH, CRITICAL, UNKNOWN")
    route: RouteOperationalSummary = Field(..., description="Route distance, duration, and clearance evaluation")
    marine_conditions: Optional[Dict[str, Any]] = Field(None, description="Local marine conditions (waves, swell, currents)")
    weather_conditions: Optional[Dict[str, Any]] = Field(None, description="Local atmospheric conditions (wind, temp, precipitation)")
    safe_ports: List[Dict[str, Any]] = Field(default_factory=list, description="Designated harbors and emergency maritime refuges along corridor")
    constraints: List[str] = Field(default_factory=list, description="Operational constraints and boundary restrictions")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Deterministic confidence rating between 0.0 and 1.0")
    data_freshness: str = Field("FRESH", description="Freshness status of underlying operational telemetry")
    evidence: List[OperationalEvidenceItem] = Field(default_factory=list, description="Traceable operational evidence provenance items")
    warnings: List[str] = Field(default_factory=list, description="Operational caveats, adverse sea states, or emergency alerts")
    recommendation: str = Field(..., description="Actionable operational directive and voyage guidance")
    explanation: str = Field(..., description="Evidence-based deterministic reasoning narrative")
    generated_at: datetime = Field(..., description="UTC timestamp of response generation")

    model_config = ConfigDict(from_attributes=True)
