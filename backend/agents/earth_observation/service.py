from typing import Optional
from sqlalchemy.orm import Session

from agents.earth_observation.agent import EarthObservationIntelligenceAgent
from agents.earth_observation.schemas import (
    EarthObservationAssessmentResponse,
    EarthObservationQuery,
)


class EarthObservationAgentService:
    """
    Service gateway for the Earth Observation Intelligence Agent.
    Coordinates satellite telemetry collection, deterministic bio-optical reasoning,
    temporal comparison, and structured response generation.
    Independently usable by API endpoints and the Agent Orchestrator.
    """

    def __init__(self, agent: Optional[EarthObservationIntelligenceAgent] = None):
        self.agent = agent or EarthObservationIntelligenceAgent()

    def assess_earth_observation(
        self,
        db: Session,
        query: EarthObservationQuery,
    ) -> EarthObservationAssessmentResponse:
        """
        Assesses satellite Earth Observation telemetry, ocean colour, SST, and productivity indicators.
        """
        return self.agent.assess(db=db, query=query)

    def assess(
        self,
        db: Session,
        query: EarthObservationQuery,
    ) -> EarthObservationAssessmentResponse:
        """
        Alias for assess_earth_observation.
        """
        return self.assess_earth_observation(db=db, query=query)
