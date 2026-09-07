from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ingestion.worker import BackgroundIngestionWorker
from ingestion.config import IngestionConfig

router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion & Cache Worker"],
)


class IngestionTriggerRequest(BaseModel):
    provider: str = Field(
        ...,
        description="Target provider name (INCOIS, Copernicus, EarthObservation, IMD)",
        examples=["INCOIS"],
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Optional custom latitude coordinate",
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Optional custom longitude coordinate",
    )


class IngestionTriggerResponse(BaseModel):
    provider: str
    status: str
    records_processed: int = 0
    error: Optional[str] = None
    reason: Optional[str] = None


@router.get(
    "/status",
    summary="Get automated ingestion worker status",
    description="Returns live runtime health, scheduled cadences, and last run telemetry for all providers.",
)
def get_ingestion_worker_status() -> Dict[str, Any]:
    worker = BackgroundIngestionWorker.get_instance()
    return worker.get_worker_status()


@router.get(
    "/locations",
    summary="Get monitored coastal ingestion locations",
    description="Lists all geographical coastal stations currently configured for periodic background ingestion.",
)
def get_monitored_locations() -> List[Dict[str, Any]]:
    config = IngestionConfig.from_env()
    return [
        {"name": loc.name, "latitude": loc.latitude, "longitude": loc.longitude}
        for loc in config.locations
    ]


@router.post(
    "/trigger",
    response_model=IngestionTriggerResponse,
    summary="Manually trigger a provider ingestion job",
    description="Safely executes an on-demand data ingestion cycle for a specific provider without blocking the event loop.",
)
async def trigger_ingestion_job(payload: IngestionTriggerRequest) -> IngestionTriggerResponse:
    worker = BackgroundIngestionWorker.get_instance()
    result = await worker.trigger_job(
        provider_name=payload.provider,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )

    if result.get("status") == "ERROR":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Invalid trigger request"),
        )

    return IngestionTriggerResponse(
        provider=payload.provider,
        status=result.get("status", "UNKNOWN"),
        records_processed=result.get("records_processed", 0),
        error=result.get("error"),
        reason=result.get("reason"),
    )
