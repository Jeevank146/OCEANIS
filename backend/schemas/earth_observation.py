from typing import Optional
from pydantic import BaseModel, Field


class EarthObservationLocationSchema(BaseModel):
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")


class EarthObservationMetricsSchema(BaseModel):
    sea_surface_temperature_c: Optional[float] = Field(None, description="Sea Surface Temperature in Celsius")
    chlorophyll_a_mg_m3: Optional[float] = Field(None, description="Chlorophyll-a concentration in mg/m³")
    ocean_colour: Optional[str] = Field(None, description="Ocean colour / water clarity classification")
    cloud_cover_percent: Optional[float] = Field(None, description="Satellite-observed cloud cover percentage (0-100)")
    solar_radiation_w_m2: Optional[float] = Field(None, description="Direct/Shortwave solar irradiance in W/m²")


class EarthObservationMetadataSchema(BaseModel):
    satellite_platform: Optional[str] = Field(None, description="Satellite constellation or spacecraft platform")
    sensor_instrument: Optional[str] = Field(None, description="Satellite instrument / radiometer / sensor")
    source_url: Optional[str] = Field(None, description="Upstream product URL or documentation endpoint")
    source_timezone: Optional[str] = Field(None, description="Reference timezone reported by provider")


class EarthObservationResponse(BaseModel):
    """
    Structured response schema for Earth Observation (EO) and remotely-sensed
    oceanographic and atmospheric data.
    """
    source: str = Field(..., description="Earth Observation data provider or mission")
    product_type: str = Field(..., description="EO product category (e.g. SST_AND_OPTICAL, OCEAN_COLOR, SST)")
    observed_at: str = Field(..., description="Observation or satellite pass timestamp (UTC ISO 8601)")
    retrieved_at: str = Field(..., description="Ingestion timestamp into OCEANIS (UTC ISO 8601)")
    data_type: str = Field("OBSERVATION_ASSIMILATION", description="Data provenance (e.g. SATELLITE_DIRECT, OBSERVATION_ASSIMILATION)")
    quality_flag: Optional[str] = Field("OPERATIONAL_QUALITY", description="Product validation / operational quality flag")
    location: EarthObservationLocationSchema = Field(..., description="Geographic coordinates of the observation")
    measurements: EarthObservationMetricsSchema = Field(..., description="Remotely sensed physical and optical measurements")
    metadata: Optional[EarthObservationMetadataSchema] = Field(None, description="Satellite mission, sensor, and product metadata")
    observation_id: Optional[int] = Field(None, description="Database record ID for the persisted EO observation")
