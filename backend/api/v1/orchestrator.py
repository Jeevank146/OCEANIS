from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from orchestrator.schemas import OrchestrationQuery, OrchestrationResponse
from orchestrator.service import OrchestratorService
from schemas.agent_contract import FinalDecisionObject, WhatIfComparison

router = APIRouter(prefix="/orchestrator", tags=["Agent Orchestrator"])
orchestrator_service = OrchestratorService()


class WhatIfRequest(BaseModel):
    query: str = Field(..., description="Natural language base query")
    latitude: Optional[float] = Field(None, description="Base or query latitude")
    longitude: Optional[float] = Field(None, description="Base or query longitude")
    target_datetime: Optional[str] = Field(None, description="Base target date/time")
    what_if_time: Optional[str] = Field(None, description="Simulated departure time (e.g. 09:00)")
    what_if_latitude: Optional[float] = Field(None, description="Simulated alternative latitude")
    what_if_longitude: Optional[float] = Field(None, description="Simulated alternative longitude")
    what_if_location_name: Optional[str] = Field(None, description="Simulated location name")


@router.post(
    "/decision",
    response_model=FinalDecisionObject,
    status_code=status.HTTP_200_OK,
    summary="Obtain complete structured marine decision intelligence from all six domain agents",
    description=(
        "Executes end-to-end OCEANIS decision intelligence pipeline: NLP query understanding, "
        "dynamic location resolution, coordination across all six domain agents, evidence fusion, "
        "deterministic safety hierarchy, transparent confidence calculation, and explainability breakdown."
    ),
)
def get_orchestrator_decision(
    payload: OrchestrationQuery,
    what_if_time: Optional[str] = Query(None, description="Optional simulated departure time for what-if comparison"),
    what_if_lat: Optional[float] = Query(None, description="Optional simulated latitude"),
    what_if_lon: Optional[float] = Query(None, description="Optional simulated longitude"),
    what_if_loc_name: Optional[str] = Query(None, description="Optional simulated location name"),
    db: Session = Depends(get_db),
) -> FinalDecisionObject:
    """
    Primary endpoint for obtaining unified, evidence-grounded marine decision objects.
    """
    return orchestrator_service.get_decision(
        db=db,
        query=payload,
        what_if_time=what_if_time,
        what_if_lat=what_if_lat,
        what_if_lon=what_if_lon,
        what_if_loc_name=what_if_loc_name,
    )


@router.post(
    "/query",
    response_model=OrchestrationResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit natural language query to the OCEANIS Agent Orchestrator (Legacy endpoint)",
    description="Maintains backwards-compatibility with existing frontend and orchestration consumers.",
)
def process_orchestrator_query(
    payload: OrchestrationQuery,
    db: Session = Depends(get_db),
) -> Any:
    return orchestrator_service.process_query(db=db, query=payload)


@router.post(
    "/what-if",
    response_model=WhatIfComparison,
    status_code=status.HTTP_200_OK,
    summary="Run What-If scenario simulation comparing base vs modified operational parameters",
    description="Evaluates operational shifts in departure time, route, or location against forecast telemetry.",
)
def run_what_if_simulation(
    payload: WhatIfRequest,
    db: Session = Depends(get_db),
) -> WhatIfComparison:
    orch_q = OrchestrationQuery(
        query=payload.query,
        latitude=payload.latitude,
        longitude=payload.longitude,
        target_datetime=payload.target_datetime,
    )
    return orchestrator_service.run_what_if(
        db=db,
        query=orch_q,
        what_if_time=payload.what_if_time,
        what_if_lat=payload.what_if_latitude,
        what_if_lon=payload.what_if_longitude,
        what_if_loc_name=payload.what_if_location_name,
    )
