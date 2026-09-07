from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from agents.fishing.schemas import (
    FishingAssessment,
    FishingQuery,
    LocationComparisonQuery,
    LocationComparisonResponse,
    WhatIfQuery,
    WhatIfResponse,
)
from agents.fishing.service import FishingAgentService
from database import get_db

router = APIRouter(prefix="/agents/fishing", tags=["Fishing Intelligence Agent"])
fishing_service = FishingAgentService()


@router.post(
    "/assess",
    response_model=FishingAssessment,
    status_code=status.HTTP_200_OK,
    summary="Assess fishing suitability & safety",
    description=(
        "Executes complete multi-domain evidence fusion across Weather, Marine Conditions, "
        "Earth Observation satellite metrics, Geo-Spatial boundaries, and Disaster & Safety warnings "
        "to generate explainable, deterministic fishing recommendations."
    ),
)
def assess_fishing_operation(
    payload: FishingQuery,
    db: Session = Depends(get_db),
) -> Any:
    """
    Evaluates fishing suitability, risk level, and safety overrides for the given parameters.
    """
    return fishing_service.assess_fishing_query(db=db, query=payload)


@router.post(
    "/compare",
    response_model=LocationComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare two fishing locations",
    description=(
        "Performs side-by-side comparative analysis of two fishing locations using the same "
        "evidence framework, highlighting safety differences, sea state, SST profiles, and suitability."
    ),
)
def compare_fishing_locations(
    payload: LocationComparisonQuery,
    db: Session = Depends(get_db),
) -> Any:
    """
    Compares two candidate fishing grounds or operational times.
    """
    return fishing_service.compare_locations(db=db, query=payload)


@router.post(
    "/what-if",
    response_model=WhatIfResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate what-if fishing operational scenarios",
    description=(
        "Recomputes multi-layer oceanographic evidence across modified parameters (such as altered "
        "departure times, alternative coordinates, or trip duration) to evaluate operational shifts."
    ),
)
def evaluate_what_if_scenario(
    payload: WhatIfQuery,
    db: Session = Depends(get_db),
) -> Any:
    """
    Recomputes operational evidence across scenario changes to evaluate before/after feasibility.
    """
    return fishing_service.evaluate_what_if_scenario(db=db, query=payload)
