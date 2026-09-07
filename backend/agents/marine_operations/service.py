from typing import Optional
from sqlalchemy.orm import Session

from agents.marine_operations.agent import MarineOperationsIntelligenceAgent
from agents.marine_operations.schemas import (
    MarineOperationsAssessmentResponse,
    MarineOperationsQuery,
)


class MarineOperationsAgentService:
    """
    Service gateway for the Marine Operations Intelligence Agent.
    Coordinates operational data collection, route clearance, constraint evaluation,
    and structured operational response generation.
    Independently callable by API routes and the future Agent Orchestrator.
    """

    def __init__(self, agent: Optional[MarineOperationsIntelligenceAgent] = None):
        self.agent = agent or MarineOperationsIntelligenceAgent()

    def assess_operations(
        self,
        db: Session,
        query: MarineOperationsQuery,
    ) -> MarineOperationsAssessmentResponse:
        """
        Assesses planned marine operations, route clearance, and environmental constraints.
        """
        return self.agent.assess(db=db, query=query)

    def assess(
        self,
        db: Session,
        query: MarineOperationsQuery,
    ) -> MarineOperationsAssessmentResponse:
        """
        Alias for assess_operations.
        """
        return self.assess_operations(db=db, query=query)
