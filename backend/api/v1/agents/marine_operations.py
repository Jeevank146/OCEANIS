from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from agents.marine_operations.schemas import (
    MarineOperationsAssessmentResponse,
    MarineOperationsQuery,
)
from agents.marine_operations.service import MarineOperationsAgentService
from database import get_db

router = APIRouter(prefix="/agents/marine-operations", tags=["Marine Operations"])
marine_operations_service = MarineOperationsAgentService()


@router.post(
    "/assess",
    response_model=MarineOperationsAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess marine route operations, transit clearance, and constraints",
    description=(
        "Executes multi-domain operational intelligence combining geodesic route calculations, "
        "transit duration estimates, PostGIS restricted/protected zone intersections, active hazard zones, "
        "official disaster alerts, tropical cyclones, and live environmental sea-state thresholds."
    ),
)
def assess_marine_operations(
    payload: MarineOperationsQuery,
    db: Session = Depends(get_db),
) -> Any:
    """
    Assesses planned marine operations, voyage feasibility, transit timing, and operational risks.
    """
    return marine_operations_service.assess_operations(db=db, query=payload)
