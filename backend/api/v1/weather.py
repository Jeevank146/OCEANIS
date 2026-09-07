import requests
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from ingestion.weather_ingestion import WeatherIngestionService
from schemas.weather import WeatherCurrentResponse

router = APIRouter(
    prefix="/weather",
    tags=["Weather"],
)


@router.get(
    "/current",
    response_model=WeatherCurrentResponse,
    summary="Get current weather observation",
    description=(
        "Fetches live weather observation for the given coordinates, normalizes it, "
        "persists the record into PostgreSQL, and returns the current meteorological metrics. "
        "Source data is directly retrieved from the configured upstream connector (e.g. Open-Meteo) "
        "and is distinct from downstream AI interpretation layers."
    ),
)
def get_current_weather(
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
    db: Session = Depends(get_db),
):
    """
    Retrieve and persist current weather conditions for specified geospatial coordinates.
    """
    service = WeatherIngestionService()

    try:
        data = service.ingest(
            db=db,
            latitude=latitude,
            longitude=longitude,
        )
        return data

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream weather provider error: {str(exc)}",
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database or internal processing failure: {str(exc)}",
        )
