from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from orchestrator.orchestrator import AgentOrchestrator
from orchestrator.schemas import OrchestrationQuery, OrchestrationResponse
from schemas.agent_contract import FinalDecisionObject, WhatIfComparison


class OrchestratorService:
    """
    Service gateway for the OCEANIS Central Agent Orchestrator.
    Exposes high-level interfaces for structured decision intelligence,
    what-if simulations, and backwards-compatible orchestration responses.
    """

    def __init__(self, orchestrator: Optional[AgentOrchestrator] = None):
        self.orchestrator = orchestrator or AgentOrchestrator()

    def get_decision(
        self,
        db: Session,
        query: OrchestrationQuery,
        what_if_time: Optional[str] = None,
        what_if_lat: Optional[float] = None,
        what_if_lon: Optional[float] = None,
        what_if_loc_name: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> FinalDecisionObject:
        """
        Primary entry point for obtaining unified FinalDecisionObject.
        """
        return self.orchestrator.decide(
            db=db,
            query=query,
            what_if_time=what_if_time,
            what_if_lat=what_if_lat,
            what_if_lon=what_if_lon,
            what_if_loc_name=what_if_loc_name,
            now=now,
        )

    def run_what_if(
        self,
        db: Session,
        query: OrchestrationQuery,
        what_if_time: Optional[str] = None,
        what_if_lat: Optional[float] = None,
        what_if_lon: Optional[float] = None,
        what_if_loc_name: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> WhatIfComparison:
        """
        Runs dedicated What-If scenario simulation.
        """
        decision_obj = self.get_decision(
            db=db,
            query=query,
            what_if_time=what_if_time,
            what_if_lat=what_if_lat,
            what_if_lon=what_if_lon,
            what_if_loc_name=what_if_loc_name,
            now=now,
        )
        return decision_obj.what_if_comparison or WhatIfComparison(
            status="insufficient_evidence",
            message="What-If simulation could not be computed.",
        )

    def process_query(
        self,
        db: Session,
        query: OrchestrationQuery,
        now: Optional[datetime] = None,
    ) -> OrchestrationResponse:
        """
        Legacy query processing method.
        """
        return self.orchestrator.orchestrate(db=db, query=query, now=now)
