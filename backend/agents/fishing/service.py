from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from agents.fishing.agent import FishingIntelligenceAgent
from agents.fishing.schemas import (
    FishingAssessment,
    FishingQuery,
    LocationComparisonQuery,
    LocationComparisonResponse,
    WhatIfQuery,
    WhatIfResponse,
)


class FishingAgentService:
    """
    Service gateway for the Fishing Intelligence Agent domain.
    """

    def __init__(self, agent: Optional[FishingIntelligenceAgent] = None):
        self.agent = agent or FishingIntelligenceAgent()

    def assess_fishing_query(self, db: Session, query: FishingQuery) -> FishingAssessment:
        return self.agent.assess(db=db, query=query)

    def compare_locations(self, db: Session, query: LocationComparisonQuery) -> LocationComparisonResponse:
        return self.agent.compare(db=db, query=query)

    def evaluate_what_if_scenario(self, db: Session, query: WhatIfQuery) -> WhatIfResponse:
        return self.agent.what_if(db=db, query=query)
