from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from orchestrator.schemas import OrchestrationQuery, OrchestrationResponse
from orchestrator.service import OrchestratorService

router = APIRouter(prefix="/orchestrator", tags=["Agent Orchestrator"])
orchestrator_service = OrchestratorService()


@router.post(
    "/query",
    response_model=OrchestrationResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit natural language query to the OCEANIS Agent Orchestrator",
    description=(
        "Dynamically analyzes natural-language user queries, extracts entities (locations, dates, times, vessels), "
        "classifies operational intent, selects the relevant domain agents, coordinates structured agent execution, "
        "fuses evidence, applies deterministic safety overrides, and synthesizes explainable recommendations."
    ),
)
def process_orchestrator_query(
    payload: OrchestrationQuery,
    db: Session = Depends(get_db),
) -> Any:
    """
    Processes natural-language inquiries across the six OCEANIS domain agents.
    """
    return orchestrator_service.process_query(db=db, query=payload)
