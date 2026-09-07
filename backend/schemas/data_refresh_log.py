from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DataRefreshLogBase(BaseModel):
    data_source_id: int = Field(..., description="ID of associated data source")
    started_at: datetime = Field(..., description="Refresh start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Refresh completion timestamp")
    status: str = Field(..., max_length=50, description="Refresh status (e.g. STARTED, SUCCESS, FAILED)")
    records_processed: int = Field(0, description="Number of records processed")
    error_message: Optional[str] = Field(None, description="Error message if refresh failed")


class DataRefreshLogCreate(BaseModel):
    data_source_id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "STARTED"
    records_processed: int = 0
    error_message: Optional[str] = None


class DataRefreshLogResponse(DataRefreshLogBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
