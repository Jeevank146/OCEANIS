from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from agents.marine_conditions.schemas import (
    MarineConditionsAssessmentResponse,
    MarineConditionsQuery,
)
from agents.marine_conditions.service import MarineConditionsAgentService
from database import get_db

router = APIRouter(prefix="/agents/marine-conditions", tags=["Marine Conditions Intelligence Agent"])
marine_conditions_service = MarineConditionsAgentService()


@router.post(
    "/assess",
    response_model=MarineConditionsAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess marine physical conditions, sea state, and wave dynamics",
    description=(
        "Evaluates wave height/period/direction, swell metrics, wind-wave dynamics, "
        "ocean current velocities, and sea surface temperature from observational data "
        "to generate deterministic, explainable sea-state assessments and safety recommendations."
    ),
)
def assess_marine_conditions(
    payload: MarineConditionsQuery,
    db: Session = Depends(get_db),
) -> Any:
    """
    Evaluates real-time marine sea state, physical wave/swell severity, and ocean risk.
    """
    return marine_conditions_service.assess_marine_conditions(db=db, query=payload)
