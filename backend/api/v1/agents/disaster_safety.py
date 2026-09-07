from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from agents.disaster_safety.schemas import (
    DisasterSafetyAssessmentResponse,
    DisasterSafetyQuery,
)
from agents.disaster_safety.service import DisasterSafetyAgentService
from database import get_db

router = APIRouter(prefix="/agents/disaster-safety", tags=["Disaster & Safety"])
disaster_safety_service = DisasterSafetyAgentService()


@router.post(
    "/assess",
    response_model=DisasterSafetyAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess disaster hazards, alerts, cyclones, and maritime safety",
    description=(
        "Executes deterministic safety evaluations using official marine alerts (INCOIS), "
        "tropical cyclone tracks and intensity metrics (IMD), spatial hazard zones (storm surge, reef, high waves), "
        "and emergency harbors of refuge. Safety rules strictly override optimistic conditions."
    ),
)
def assess_disaster_safety(
    payload: DisasterSafetyQuery,
    db: Session = Depends(get_db),
) -> Any:
    """
    Assesses disaster hazards, official warnings, cyclone proximity, and emergency safety status.
    """
    return disaster_safety_service.assess_safety(db=db, query=payload)
