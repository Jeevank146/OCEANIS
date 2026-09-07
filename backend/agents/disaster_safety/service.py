from typing import Optional
from sqlalchemy.orm import Session

from agents.disaster_safety.agent import DisasterSafetyIntelligenceAgent
from agents.disaster_safety.schemas import (
    DisasterSafetyAssessmentResponse,
    DisasterSafetyQuery,
)


class DisasterSafetyAgentService:
    """
    Service gateway for the Disaster & Safety Intelligence Agent.
    Coordinates alert, hazard zone, cyclone, and refuge data collection,
    executes deterministic safety evaluations, and produces explainable safety responses.
    Independently callable by API routes and the future Agent Orchestrator.
    """

    def __init__(self, agent: Optional[DisasterSafetyIntelligenceAgent] = None):
        self.agent = agent or DisasterSafetyIntelligenceAgent()

    def assess_safety(
        self,
        db: Session,
        query: DisasterSafetyQuery,
    ) -> DisasterSafetyAssessmentResponse:
        """
        Assesses disaster, hazard, and maritime safety conditions for given coordinates.
        """
        return self.agent.assess(db=db, query=query)

    def assess(
        self,
        db: Session,
        query: DisasterSafetyQuery,
    ) -> DisasterSafetyAssessmentResponse:
        """
        Alias for assess_safety.
        """
        return self.assess_safety(db=db, query=query)
