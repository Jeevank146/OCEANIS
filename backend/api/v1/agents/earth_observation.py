from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from agents.earth_observation.schemas import (
    EarthObservationAssessmentResponse,
    EarthObservationQuery,
)
from agents.earth_observation.service import EarthObservationAgentService
from database import get_db

router = APIRouter(prefix="/agents/earth-observation", tags=["Earth Observation"])
eo_service = EarthObservationAgentService()


@router.post(
    "/assess",
    response_model=EarthObservationAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess satellite Earth Observation, ocean colour, and SST indicators",
    description=(
        "Evaluates satellite-derived Sea Surface Temperature (SST), chlorophyll-a optical reflectance, "
        "ocean colour classification, cloud cover fraction, and temporal trends across satellite passes "
        "to produce explainable bio-optical and oceanographic intelligence."
    ),
)
def assess_earth_observation(
    payload: EarthObservationQuery,
    db: Session = Depends(get_db),
) -> Any:
    """
    Evaluates real-time and historical satellite Earth Observation telemetry and indicators.
    """
    return eo_service.assess_earth_observation(db=db, query=payload)
