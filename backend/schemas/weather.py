from typing import Optional
from pydantic import BaseModel, Field


class WeatherLocationSchema(BaseModel):
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")


class WeatherCurrentMetricsSchema(BaseModel):
    temperature_c: Optional[float] = Field(None, description="Air temperature at 2m in Celsius")
    humidity_percent: Optional[float] = Field(None, description="Relative humidity percentage at 2m")
    wind_speed_kmh: Optional[float] = Field(None, description="Wind speed at 10m in km/h")
    wind_direction_deg: Optional[float] = Field(None, description="Wind direction in degrees (0-360)")
    precipitation_mm: Optional[float] = Field(None, description="Precipitation amount in mm")


class WeatherCurrentResponse(BaseModel):
    """
    Response schema for current weather conditions.
    Distinguishes raw upstream data provider from internal analytics/AI interpretation.
    """
    source: str = Field(..., description="Weather data provider (e.g. Open-Meteo)")
    retrieved_at: str = Field(..., description="UTC ISO 8601 timestamp of retrieval")
    location: WeatherLocationSchema = Field(..., description="Geographic location of the observation")
    current: WeatherCurrentMetricsSchema = Field(..., description="Current atmospheric metrics")
    raw_timezone: Optional[str] = Field(None, description="Timezone reported by upstream provider")
    observation_id: Optional[int] = Field(None, description="Database record ID for the persisted observation")
