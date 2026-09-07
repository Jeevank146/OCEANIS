from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from orchestrator.models import AgentQueryRequest, OrchestratorQueryResponse
from orchestrator.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/agents", tags=["Agent Orchestrator"])
orchestrator = AgentOrchestrator()


@router.post(
    "/query",
    response_model=OrchestratorQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Process natural-language ocean inquiry through Agent Orchestrator",
    description=(
        "Central intelligence routing layer that parses user intent and entities (location, "
        "time, activity, species), dynamically constructs a multi-agent execution plan, "
        "coordinates domain agents (Fishing, Disaster & Safety, Marine Operations, Weather, "
        "Marine Conditions, Earth Observation, Geo-Spatial), fuses evidence, and enforces strict "
        "safety-first decision overrides."
    ),
)
def process_agent_query(
    payload: AgentQueryRequest,
    db: Session = Depends(get_db),
) -> Any:
    """
    Submits a natural language or structured query to the OCEANIS Agent Orchestrator.
    """
    return orchestrator.process_query(db=db, request=payload)
