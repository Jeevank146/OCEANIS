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


class LocationSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[LocationCandidate]


class LocationSuggestionsResponse(BaseModel):
    suggestions: List[LocationCandidate]
