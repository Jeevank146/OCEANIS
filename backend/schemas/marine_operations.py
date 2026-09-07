from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OperationCoordinateSchema(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to 180)")


# ---------------------------------------------------------------------------
# Marine Operation CRUD Schemas
# ---------------------------------------------------------------------------

class MarineOperationBase(BaseModel):
    operation_type: str = Field("TRANSIT", max_length=50, description="Type: FISHING_TRIP, TRANSIT, RESCUE_SUPPORT, SURVEY, PORT_TRANSFER, OTHER")
    vessel_type: str = Field("FISHING_VESSEL", max_length=50, description="Vessel classification")
    vessel_name: Optional[str] = Field(None, max_length=150, description="Optional vessel identifier/name")
    origin_latitude: float = Field(..., ge=-90.0, le=90.0, description="Origin latitude (-90 to 90)")
    origin_longitude: float = Field(..., ge=-180.0, le=180.0, description="Origin longitude (-180 to 180)")
    destination_latitude: float = Field(..., ge=-90.0, le=90.0, description="Destination latitude (-90 to 90)")
    destination_longitude: float = Field(..., ge=-180.0, le=180.0, description="Destination longitude (-180 to 180)")
    planned_departure_at: Optional[datetime] = Field(None, description="Planned departure timestamp (UTC)")
    estimated_speed_kmh: Optional[float] = Field(None, gt=0.0, description="Estimated cruising speed in km/h (> 0)")
    notes: Optional[str] = Field(None, description="Operational notes or trip objectives")
    source: str = Field("MANUAL_INPUT", max_length=100, description="Source registry or user input")
    data_type: str = Field("PLANNED", max_length=50, description="PLANNED, LOGGED, SIMULATED")


class MarineOperationCreate(MarineOperationBase):
    operation_id: Optional[str] = Field(None, max_length=100, description="Optional custom operational ID")
    operational_status: Optional[str] = Field("PLANNED", max_length=50, description="Initial operational status")


class MarineOperationUpdate(BaseModel):
    operation_type: Optional[str] = Field(None, max_length=50)
    vessel_type: Optional[str] = Field(None, max_length=50)
    vessel_name: Optional[str] = Field(None, max_length=150)
    origin_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    origin_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    destination_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    destination_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    planned_departure_at: Optional[datetime] = None
    estimated_speed_kmh: Optional[float] = Field(None, gt=0.0)
    operational_status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class MarineOperationResponse(MarineOperationBase):
    id: int
    operation_id: str
    estimated_distance_km: float = Field(..., ge=0.0, description="Calculated geodesic distance in km")
    estimated_duration_minutes: Optional[float] = Field(None, ge=0.0, description="Estimated transit duration in minutes")
    operational_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Utility Schemas: Distance & Time Estimation
# ---------------------------------------------------------------------------

class OperationDistanceResponse(BaseModel):
    origin: OperationCoordinateSchema
    destination: OperationCoordinateSchema
    distance_km: float = Field(..., ge=0.0, description="Geodesic distance in kilometers")
    distance_nautical_miles: float = Field(..., ge=0.0, description="Geodesic distance in Nautical Miles")
    calculation_method: str = Field("HAVERSINE_GEODESIC", description="Calculation algorithm")


class OperationTimeEstimateResponse(BaseModel):
    origin: OperationCoordinateSchema
    destination: OperationCoordinateSchema
    distance_km: float = Field(..., ge=0.0, description="Distance in kilometers")
    distance_nautical_miles: float = Field(..., ge=0.0, description="Distance in Nautical Miles")
    speed_kmh: float = Field(..., gt=0.0, description="Speed in km/h")
    estimated_duration_minutes: float = Field(..., ge=0.0, description="Estimated duration in minutes")
    estimated_duration_hours: float = Field(..., ge=0.0, description="Estimated duration in decimal hours")
    calculation_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Operational Assessment Schemas
# ---------------------------------------------------------------------------

class MarineOperationAssessment(BaseModel):
    operation_id: Optional[str] = Field(None, description="Operation ID if evaluating an existing record")
    origin: OperationCoordinateSchema
    destination: OperationCoordinateSchema
    distance_km: float = Field(..., ge=0.0)
    distance_nautical_miles: float = Field(..., ge=0.0)
    estimated_speed_kmh: Optional[float] = None
    estimated_duration_minutes: Optional[float] = None
    route_assessment: Dict[str, Any] = Field(..., description="Restricted, protected, and hazard zone intersection metrics")
    marine_conditions: Optional[Dict[str, Any]] = Field(None, description="Marine conditions telemetry along route")
    weather_conditions: Optional[Dict[str, Any]] = Field(None, description="Atmospheric weather telemetry along route")
    active_alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Active marine alerts affecting trajectory")
    cyclone_activity: List[Dict[str, Any]] = Field(default_factory=list, description="Nearby active cyclonic systems")
    nearest_safe_ports: List[Dict[str, Any]] = Field(default_factory=list, description="Nearest coastal ports/refuges")
    operational_status: str = Field(..., description="Deterministic status: PLANNED, ASSESSED, CAUTION, WARNING, BLOCKED, INSUFFICIENT_DATA")
    data_freshness: Dict[str, Any] = Field(default_factory=dict, description="Telemetry and safety data freshness audit")
    confidence: str = Field(..., description="Assessment confidence: HIGH, MEDIUM, LOW, NONE")
    reasons: List[str] = Field(default_factory=list, description="Diagnostic reasons justifying the operational status")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed source records and timestamps")
    assessment_timestamp: datetime = Field(..., description="UTC timestamp when assessment was generated")

    model_config = ConfigDict(from_attributes=True)


class DepartureAssessmentResponse(BaseModel):
    origin: OperationCoordinateSchema
    destination: OperationCoordinateSchema
    departure_at: datetime
    estimated_arrival_at: Optional[datetime] = None
    distance_km: float = Field(..., ge=0.0)
    distance_nautical_miles: float = Field(..., ge=0.0)
    estimated_speed_kmh: Optional[float] = None
    estimated_duration_minutes: Optional[float] = None
    operational_status: str = Field(..., description="PLANNED, ASSESSED, CAUTION, WARNING, BLOCKED, INSUFFICIENT_DATA")
    route_assessment: Dict[str, Any] = Field(..., description="Zone intersection details")
    marine_conditions: Optional[Dict[str, Any]] = None
    weather_conditions: Optional[Dict[str, Any]] = None
    active_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list, description="Active warnings or temporal hazards")
    reasons: List[str] = Field(default_factory=list, description="Diagnostic departure assessment reasons")
    confidence: str
    data_freshness: str
    assessment_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
