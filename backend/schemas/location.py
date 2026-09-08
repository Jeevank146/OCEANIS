from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LocationSearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=200, description="Search query string")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of candidates")


class LocationValidateRequest(BaseModel):
    query: Optional[str] = Field(None, max_length=200, description="Location search query or name")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude coordinate")


class LocationReverseGeocodeRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")


class LocationCandidate(BaseModel):
    id: str
    name: str
    display_name: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    latitude: float
    longitude: float
    is_coastal: bool
    is_marine: bool
    distance_to_coast_km: float
    place_type: str = "coastal_station"
    nearest_port: Optional[str] = None
    marine_context: Optional[str] = None


class ResolvedLocation(BaseModel):
    """
    Standardized, authoritative resolved location object across OCEANIS.
    Latitude and Longitude are the authoritative source of truth.
    """
    latitude: float = Field(..., description="Authoritative latitude coordinate")
    longitude: float = Field(..., description="Authoritative longitude coordinate")
    display_name: str = Field(..., description="Human-readable full location label")
    location_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    coastal_status: str = Field("COASTAL", description="COASTAL | MARINE | INLAND | OFFSHORE | UNRESOLVED")
    is_coastal: bool = True
    is_marine: bool = True
    distance_to_coast_km: Optional[float] = None
    resolution_source: str = Field("COORDINATE_INPUT", description="COORDINATE_INPUT | BROWSER_GEOLOCATION | SEARCH_GEOCODING | REGISTRY")
    nearest_port: Optional[str] = None
    marine_context: Optional[str] = None
    requested_latitude: Optional[float] = None
    requested_longitude: Optional[float] = None
    source_grid_latitude: Optional[float] = None
    source_grid_longitude: Optional[float] = None
    resolved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LocationValidationResult(BaseModel):
    status: str = Field(..., description="VALID_COASTAL | VALID_MARINE | INLAND | UNRESOLVED")
    is_coastal: bool = Field(..., description="Whether location is within 50km of seashore")
    is_marine: bool = Field(..., description="Whether location has accessible marine context")
    location_name: str
    display_name: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_to_coast_km: Optional[float] = None
    nearest_port: Optional[str] = None
    marine_context: Optional[str] = None
    reason: str
    coordinates_formatted: Optional[str] = None
    coastal_status: Optional[str] = None
    resolution_source: Optional[str] = None
    resolved_at: Optional[str] = None
    requested_latitude: Optional[float] = None
    requested_longitude: Optional[float] = None
    source_grid_latitude: Optional[float] = None
    source_grid_longitude: Optional[float] = None


class LocationSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[LocationCandidate]


class LocationSuggestionsResponse(BaseModel):
    suggestions: List[LocationCandidate]
