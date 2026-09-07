from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from ingestion.earth_observation import EarthObservationIngestionService
from schemas.earth_observation import EarthObservationResponse

router = APIRouter(
    prefix="/earth-observation",
    tags=["Earth Observation"],
)


@router.get(
    "/observations",
    response_model=EarthObservationResponse,
    summary="Get Earth Observation and satellite-derived oceanic data",
    description=(
        "Fetches remotely-sensed and satellite-derived Earth Observation data for the specified "
        "coordinates, including sea surface temperature (SST), cloud cover, and solar irradiance. "
        "Normalizes the data, persists the observation to PostgreSQL, and returns the structured "
        "EO payload. Satellite telemetry is decoupled from downstream AI reasoning layers."
    ),
)
def get_earth_observations(
    latitude: float = Query(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees (-90.0 to 90.0)",
        examples=[16.9891],
    ),
    longitude: float = Query(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees (-180.0 to 180.0)",
        examples=[82.2475],
    ),
    product_type: Optional[str] = Query(
        None,
        description="Optional EO product type filter (e.g. SST, OPTICAL, SST_AND_OPTICAL)",
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve and persist Earth Observation telemetry for geospatial coordinates.
    """
    service = EarthObservationIngestionService()

    try:
        data = service.ingest(
            db=db,
            latitude=latitude,
            longitude=longitude,
            product_type=product_type,
        )
        return data

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream Earth Observation provider error: {str(exc)}",
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database or internal processing failure: {str(exc)}",
        )
