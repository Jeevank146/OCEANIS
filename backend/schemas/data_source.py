from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DataSourceBase(BaseModel):
    name: str = Field(..., max_length=100, description="Unique name/identifier of data source")
    provider: str = Field(..., max_length=100, description="Data provider or organization (e.g. INCOIS, NOAA)")
    source_type: str = Field(..., max_length=50, description="Source format or protocol (e.g. API, NetCDF, GRIB2)")
    base_url: Optional[str] = Field(None, max_length=500, description="Endpoint or base URL")
    description: Optional[str] = Field(None, description="Detailed description")
    is_active: bool = Field(True, description="Whether the data source is currently enabled")


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100, description="Unique name/identifier of data source")
    provider: Optional[str] = Field(None, max_length=100, description="Data provider or organization (e.g. INCOIS, NOAA)")
    source_type: Optional[str] = Field(None, max_length=50, description="Source format or protocol (e.g. API, NetCDF, GRIB2)")
    base_url: Optional[str] = Field(None, max_length=500, description="Endpoint or base URL")
    description: Optional[str] = Field(None, description="Detailed description")
    is_active: Optional[bool] = Field(None, description="Whether the data source is currently enabled")


class DataSourceResponse(DataSourceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

