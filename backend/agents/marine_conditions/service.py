from typing import Optional
from sqlalchemy.orm import Session

from agents.marine_conditions.agent import MarineConditionsIntelligenceAgent
from agents.marine_conditions.schemas import (
    MarineConditionsAssessmentResponse,
    MarineConditionsQuery,
)


class MarineConditionsAgentService:
    """
    Service gateway for the Marine Conditions Intelligence Agent.
    Coordinates evidence collection, deterministic reasoning, and structured response generation.
    Independently usable by API routes and the Agent Orchestrator.
    """

    def __init__(self, agent: Optional[MarineConditionsIntelligenceAgent] = None):
        self.agent = agent or MarineConditionsIntelligenceAgent()

    def assess_marine_conditions(
        self,
        db: Session,
        query: MarineConditionsQuery,
    ) -> MarineConditionsAssessmentResponse:
        """
        Assesses marine physical conditions, sea state, and wave dynamics for the specified query.
        """
        return self.agent.assess(db=db, query=query)

    def assess(
        self,
        db: Session,
        query: MarineConditionsQuery,
    ) -> MarineConditionsAssessmentResponse:
        """
        Alias for assess_marine_conditions.
        """
        return self.assess_marine_conditions(db=db, query=query)
