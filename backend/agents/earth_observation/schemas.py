from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EarthObservationQuery(BaseModel):
    """
    Input query payload for Earth Observation Intelligence Agent.
    """
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90.0 to 90.0)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180.0 to 180.0)")
    target_datetime: Optional[str] = Field(None, description="Optional target date or ISO 8601 timestamp")


class EarthObservationEvidenceItem(BaseModel):
    """
    Standardized traceable evidence item for satellite-derived Earth observations.
    """
    factor: str = Field(..., description="Parameter name (e.g. sea_surface_temperature, chlorophyll_a, ocean_colour, cloud_cover)")
    value: Optional[Any] = Field(None, description="Recorded metric value")
    unit: Optional[str] = Field(None, description="Measurement unit (°C, mg/m³, %, W/m²)")
    source: str = Field(..., description="Satellite data provider or mission source")
    satellite_platform: Optional[str] = Field(None, description="Satellite constellation/platform (e.g. Sentinel-3, MODIS, NOAA-20)")
    sensor_instrument: Optional[str] = Field(None, description="Payload instrument (e.g. OLCI, SLSTR, VIIRS)")
    product_type: Optional[str] = Field(None, description="Satellite product identifier (e.g. CHL_OC4ME, SST_GHRSST)")
    latitude: Optional[float] = Field(None, description="Observation latitude")
    longitude: Optional[float] = Field(None, description="Observation longitude")
    observed_at: Optional[str] = Field(None, description="ISO timestamp of satellite pass / observation validity")
    retrieved_at: Optional[str] = Field(None, description="ISO timestamp when telemetry was ingested")
    data_type: str = Field("OBSERVATION", description="OBSERVATION, FORECAST, OFFICIAL_WARNING, AI_ASSESSMENT, OBSERVATION_ASSIMILATION")
    quality: str = Field("OPERATIONAL_QUALITY", description="Quality flag: GOOD, OPERATIONAL_QUALITY, DEGRADED, SUSPECT, UNKNOWN")
    freshness: str = Field("FRESH", description="Freshness evaluation: FRESH, AGING, STALE, EXPIRED, UNKNOWN")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Deterministic confidence score between 0.0 and 1.0")
    severity: str = Field("NORMAL", description="Factor status: NORMAL, FAVORABLE_INDICATOR, ANOMALOUS, LOW_QUALITY, STALE, UNKNOWN")
    notes: Optional[str] = Field(None, description="Diagnostic observation note")


class EarthObservationTemporalComparison(BaseModel):
    """
    Temporal comparison between current and previous satellite passes.
    """
    has_historical_data: bool = Field(False, description="True if a previous satellite pass was available for comparison")
    status: str = Field("INSUFFICIENT_DATA", description="AVAILABLE or INSUFFICIENT_DATA")
    previous_observed_at: Optional[str] = Field(None, description="ISO timestamp of previous satellite pass")
    current_observed_at: Optional[str] = Field(None, description="ISO timestamp of current satellite pass")
    time_delta_hours: Optional[float] = Field(None, description="Elapsed hours between observations")
    sst_change_c: Optional[float] = Field(None, description="SST difference in °C (current - previous)")
    sst_trend: Optional[str] = Field("UNKNOWN", description="WARMING, COOLING, STABLE, UNKNOWN")
    chlorophyll_change_mg_m3: Optional[float] = Field(None, description="Chlorophyll difference in mg/m³")
    chlorophyll_trend: Optional[str] = Field("UNKNOWN", description="INCREASING, DECREASING, STABLE, UNKNOWN")
    cloud_cover_change_percent: Optional[float] = Field(None, description="Cloud cover percentage change")
    cloud_cover_trend: Optional[str] = Field("UNKNOWN", description="INCREASING, DECREASING, STABLE, UNKNOWN")
    summary: str = Field("INSUFFICIENT_DATA: No historical satellite observation available for temporal trend comparison.", description="Comparative summary")


class EarthObservationSummary(BaseModel):
    """
    Raw satellite-derived oceanographic and atmospheric metrics.
    """
    sea_surface_temperature_c: Optional[float] = None
    chlorophyll_a_mg_m3: Optional[float] = None
    ocean_colour: Optional[str] = None
    cloud_cover_percent: Optional[float] = None
    solar_radiation_w_m2: Optional[float] = None
    satellite_platform: Optional[str] = None
    sensor_instrument: Optional[str] = None
    product_type: Optional[str] = None
    observed_at: Optional[str] = None
    retrieved_at: Optional[str] = None
    source: Optional[str] = None
    data_type: Optional[str] = None
    quality_flag: Optional[str] = None


class EarthObservationIndicators(BaseModel):
    """
    Derived oceanographic and bio-optical condition indicators.
    """
    sst_status: str = Field("UNKNOWN", description="NORMAL, COOL_UPWELLING, WARM_THERMAL_FRONT, ANOMALOUS, UNKNOWN")
    chlorophyll_status: str = Field("UNKNOWN", description="FAVORABLE_INDICATOR, MODERATE_PRODUCTIVITY, OLIGOTROPHIC, ANOMALOUS_BLOOM, UNKNOWN")
    ocean_colour_status: str = Field("UNKNOWN", description="MESOTROPHIC, EUTROPHIC, CLEAR_OCEANIC, UNKNOWN")
    optical_observability: str = Field("HIGH_QUALITY", description="HIGH_QUALITY, MODERATE_HAZE, CLOUD_OBSCURED, UNKNOWN")
    thermal_front_detected: bool = Field(False, description="True if sharp thermal divergence or upwelling signatures detected")
    chlorophyll_gradient_detected: bool = Field(False, description="True if elevated biological productivity gradient detected")


class EarthObservationAssessmentResponse(BaseModel):
    """
    Structured response generated by the Earth Observation Intelligence Agent.
    """
    agent: str = Field("earth_observation", description="Name of the domain agent")
    location: Dict[str, float] = Field(..., description="Target coordinate latitude and longitude")
    observations: Dict[str, Any] = Field(default_factory=dict, description="Raw satellite observation payload")
    indicators: Dict[str, Any] = Field(default_factory=dict, description="Derived EO oceanographic indicators")
    temporal_comparison: Optional[EarthObservationTemporalComparison] = Field(None, description="Temporal trend comparison with historical observations")
    observation_quality: str = Field("OPERATIONAL_QUALITY", description="Overall satellite observation quality flag")
    data_freshness: str = Field("FRESH", description="Freshness status of underlying telemetry")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Deterministic confidence rating between 0.0 and 1.0")
    evidence: List[EarthObservationEvidenceItem] = Field(default_factory=list, description="Traceable satellite evidence provenance items")
    warnings: List[str] = Field(default_factory=list, description="Observation caveats, cloud obscuration, or anomalous warnings")
    recommendation: str = Field(..., description="Evidence-based actionable oceanographic insight")
    explanation: str = Field(..., description="Detailed deterministic reasoning narrative")
    generated_at: datetime = Field(..., description="UTC timestamp of response generation")

    model_config = ConfigDict(from_attributes=True)
