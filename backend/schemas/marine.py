from typing import Optional
from pydantic import BaseModel, Field


class MarineLocationSchema(BaseModel):
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")


class WaveMetricsSchema(BaseModel):
    wave_height_m: Optional[float] = Field(None, description="Significant wave height in meters")
    wave_direction_deg: Optional[float] = Field(None, description="Mean wave direction in degrees (0-360)")
    wave_period_s: Optional[float] = Field(None, description="Mean wave period in seconds")


class SwellMetricsSchema(BaseModel):
    swell_wave_height_m: Optional[float] = Field(None, description="Swell wave height in meters")
    swell_wave_direction_deg: Optional[float] = Field(None, description="Swell wave direction in degrees (0-360)")
    swell_wave_period_s: Optional[float] = Field(None, description="Swell wave period in seconds")


class WindWaveMetricsSchema(BaseModel):
    wind_wave_height_m: Optional[float] = Field(None, description="Wind wave height in meters")
    wind_wave_direction_deg: Optional[float] = Field(None, description="Wind wave direction in degrees (0-360)")
    wind_wave_period_s: Optional[float] = Field(None, description="Wind wave period in seconds")


class OceanCurrentMetricsSchema(BaseModel):
    velocity_kmh: Optional[float] = Field(None, description="Ocean current velocity in km/h")
    direction_deg: Optional[float] = Field(None, description="Ocean current direction in degrees (0-360)")


class MarineConditionsMetricsSchema(BaseModel):
    waves: WaveMetricsSchema = Field(default_factory=WaveMetricsSchema, description="Total wave conditions")
    swell: SwellMetricsSchema = Field(default_factory=SwellMetricsSchema, description="Swell wave characteristics")
    wind_waves: WindWaveMetricsSchema = Field(default_factory=WindWaveMetricsSchema, description="Locally generated wind waves")
    ocean_current: OceanCurrentMetricsSchema = Field(default_factory=OceanCurrentMetricsSchema, description="Ocean surface currents")
    sea_surface_temperature_c: Optional[float] = Field(None, description="Sea surface temperature in Celsius")


class MarineConditionsResponse(BaseModel):
    """
    Structured response schema for marine conditions and oceanographic intelligence.
    Identifies the upstream physical sensor / model provider and distinguishes raw data
    from AI interpretation or decision logic.
    """
    source: str = Field(..., description="Marine data provider (e.g. Open-Meteo Marine, INCOIS)")
    retrieved_at: str = Field(..., description="UTC ISO 8601 timestamp of data ingestion")
    location: MarineLocationSchema = Field(..., description="Geographic location of observation")
    data_type: str = Field("OBSERVATION", description="Classification (e.g. OBSERVATION, FORECAST, NOWCAST)")
    quality_flag: Optional[str] = Field("REALTIME", description="Data quality or validation indicator")
    conditions: MarineConditionsMetricsSchema = Field(..., description="Multi-parameter oceanographic metrics")
    raw_timezone: Optional[str] = Field(None, description="Upstream provider source timezone")
    observation_id: Optional[int] = Field(None, description="Database record ID for the persisted marine observation")


class DynamicMarineConditionsResponse(BaseModel):
    """
    Location-agnostic dynamic marine conditions response schema.
    Distinguishes Cases A (Inland), B (Coastal - No Data), C (Coastal - Live Data), D (Provider Down).
    """
    availability_status: str = Field(
        ...,
        description="AVAILABLE | UNAVAILABLE | INLAND_BLOCKED | PROVIDER_DOWN",
    )
    is_coastal: bool = Field(..., description="Whether location is coastal/marine")
    location_name: str = Field(..., description="Resolved location name or coordinates")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    message: Optional[str] = Field(None, description="Operational or warning message")
    sea_state: Optional[str] = Field(None, description="Calm | Smooth | Slight | Moderate | Rough | Very Rough")
    wave_height_m: Optional[float] = Field(None, description="Significant wave height in meters")
    wave_period_s: Optional[float] = Field(None, description="Wave peak period in seconds")
    wave_direction_deg: Optional[float] = Field(None, description="Wave direction in degrees")
    swell_height_m: Optional[float] = Field(None, description="Swell height in meters")
    wind_wave_height_m: Optional[float] = Field(None, description="Wind wave height in meters")
    wind_speed_kmh: Optional[float] = Field(None, description="Wind speed in km/h")
    wind_speed_kts: Optional[float] = Field(None, description="Wind speed in knots")
    wind_direction_deg: Optional[float] = Field(None, description="Wind direction in degrees")
    wind_direction_cardinal: Optional[str] = Field(None, description="Wind cardinal direction e.g. SSW")
    sea_surface_temperature_c: Optional[float] = Field(None, description="SST in degrees Celsius")
    ocean_current_velocity_kmh: Optional[float] = Field(None, description="Current velocity in km/h")
    ocean_current_speed_kts: Optional[float] = Field(None, description="Current speed in knots")
    ocean_current_direction_deg: Optional[float] = Field(None, description="Current direction in degrees")
    visibility_km: Optional[float] = Field(None, description="Atmospheric visibility in kilometers")
    risk_level: Optional[str] = Field(None, description="LOW | MODERATE | HIGH | CRITICAL")
    safety_status: Optional[str] = Field(None, description="CLEAR | CAUTION | WARNING | BLOCKED")
    source: Optional[str] = Field(None, description="Data source attribution")
    data_type: Optional[str] = Field("OBSERVED", description="OBSERVED | FORECAST")
    freshness: Optional[str] = Field("FRESH (< 15 min)", description="Data freshness indicator")
    retrieved_at: Optional[str] = Field(None, description="ISO timestamp of observation")
