from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from orchestrator.orchestrator import AgentOrchestrator
from orchestrator.schemas import (
    OrchestrationQuery,
    OrchestrationResponse,
)


class OrchestratorService:
    """
    Application Service layer for the OCEANIS Agent Orchestrator.
    Exposes a unified interface for natural language query execution
    and multi-agent decision support.
    """

    def __init__(self, orchestrator: Optional[AgentOrchestrator] = None):
        self.orchestrator = orchestrator or AgentOrchestrator()

    def process_query(
        self,
        db: Session,
        query: OrchestrationQuery,
        now: Optional[datetime] = None,
    ) -> OrchestrationResponse:
        """
        Orchestrates natural language user query processing and returns synthesized decision.
        """
        return self.orchestrator.orchestrate(db=db, query=query, now=now)
