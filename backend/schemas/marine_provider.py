from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProviderStatus(str, Enum):
    HEALTHY = "HEALTHY"
    CONFIGURATION_REQUIRED = "CONFIGURATION_REQUIRED"
    UNAVAILABLE = "UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    AUTH_FAILURE = "AUTH_FAILURE"
    NO_DATA = "NO_DATA"
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    STALE_DATA = "STALE_DATA"


class MarineDataType(str, Enum):
    OBSERVED = "OBSERVED"
    FORECAST = "FORECAST"
    MODEL = "MODEL"
    OFFICIAL_WARNING = "OFFICIAL_WARNING"
    AI_ASSESSMENT = "AI_ASSESSMENT"


class DataFreshnessStatus(str, Enum):
    FRESH = "FRESH"
    AGING = "AGING"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class DataQualityStatus(str, Enum):
    VALIDATED = "VALIDATED"
    PROVISIONAL = "PROVISIONAL"
    SUSPECT = "SUSPECT"
    REJECTED = "REJECTED"
    DEMO = "DEMO"


class NormalizedMarineRecord(BaseModel):
    """
    Standardized, atomic representation of any marine/oceanographic/weather parameter.
    Preserves exact source provenance, validity window, units, and quality flags.
    """
    parameter: str = Field(..., description="Normalized parameter name e.g. wave_height, sst, wind_speed")
    value: Optional[float] = Field(None, description="Numerical value of the parameter")
    text_value: Optional[str] = Field(None, description="Categorical or textual representation e.g. Rough, Calm")
    unit: str = Field(..., description="Standard physical unit e.g. m, deg, s, km/h, C, hPa, mg/m3")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")
    valid_time: str = Field(..., description="ISO 8601 UTC timestamp of observation/forecast validity")
    retrieved_at: str = Field(..., description="ISO 8601 UTC timestamp of data retrieval")
    source: str = Field(..., description="Data provider/authority e.g. INCOIS, IMD, Copernicus, Open-Meteo")
    data_type: MarineDataType = Field(MarineDataType.OBSERVED, description="Nature of measurement")
    freshness_status: DataFreshnessStatus = Field(DataFreshnessStatus.FRESH, description="Freshness evaluation")
    quality_status: DataQualityStatus = Field(DataQualityStatus.VALIDATED, description="Quality validation outcome")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Source-reported confidence score")
    raw_identifier: Optional[str] = Field(None, description="Sensor/station or model run identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional source-specific metadata")


class ProviderResponse(BaseModel):
    """
    Structured outcome of a provider fetch operation.
    """
    provider_name: str = Field(..., description="Name of the queried provider")
    status: ProviderStatus = Field(..., description="Outcome status")
    records: List[NormalizedMarineRecord] = Field(default_factory=list, description="Extracted normalized records")
    error_message: Optional[str] = Field(None, description="Error or diagnostic detail if failed")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Raw provider payload if available")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MultiSourceMarineResponse(BaseModel):
    """
    Comprehensive multi-source marine intelligence payload.
    Exposes validated records from primary, secondary, and fallback providers
    with clear provenance attribution.
    """
    latitude: float = Field(..., description="Requested latitude")
    longitude: float = Field(..., description="Requested longitude")
    location_name: Optional[str] = Field(None, description="Resolved geographic name")
    is_coastal: bool = Field(True, description="Whether location is marine/coastal")
    primary_source: Optional[str] = Field(None, description="Primary data provider used")
    records: List[NormalizedMarineRecord] = Field(default_factory=list, description="All normalized parameter records")
    provider_statuses: Dict[str, ProviderStatus] = Field(default_factory=dict, description="Status of each queried provider")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    warnings: List[str] = Field(default_factory=list, description="Operational or safety notices")


class ProviderHealthResponse(BaseModel):
    """
    Health check status response for a registered data provider.
    """
    name: str = Field(..., description="Provider name")
    category: str = Field(..., description="Provider category e.g. In-situ Buoy, Radar, Satellite, Model")
    authority: str = Field(..., description="Governing institution e.g. MoES, ESA, NOAA")
    enabled: bool = Field(True, description="Whether provider is enabled in configuration")
    auth_configured: bool = Field(False, description="Whether required credentials are present")
    status: ProviderStatus = Field(..., description="Current operational status")
    last_successful_retrieval: Optional[str] = Field(None, description="ISO timestamp of last success")
    last_failure: Optional[str] = Field(None, description="ISO timestamp of last failure")
    details: Optional[str] = Field(None, description="Diagnostic notes")
