from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from agents.disaster_safety.collector import DisasterSafetyDataCollector
from agents.disaster_safety.reasoning import DisasterSafetyReasoningEngine
from agents.disaster_safety.schemas import (
    DisasterSafetyAssessmentResponse,
    DisasterSafetyQuery,
)


class DisasterSafetyIntelligenceAgent:
    """
    OCEANIS Disaster & Safety Intelligence Domain Agent.
    Owns the complete disaster, hazard, alert, and maritime safety domain:
    - Tropical cyclone tracking, position, and intensity intelligence
    - Official marine weather warnings and navigational alerts
    - Spatial hazard zone containment and boundary proximity
    - Emergency decision support and nearest harbor of refuge
    - Strict deterministic safety overrides (CRITICAL -> BLOCKED, WARNING -> WARNING)
    - Zero optimistic overrides over safety threats
    - Data coverage verification with INSUFFICIENT_DATA fallback
    """

    def __init__(
        self,
        collector: Optional[DisasterSafetyDataCollector] = None,
        reasoning_engine: Optional[DisasterSafetyReasoningEngine] = None,
    ):
        self.collector = collector or DisasterSafetyDataCollector()
        self.reasoning = reasoning_engine or DisasterSafetyReasoningEngine()

    def assess(
        self,
        db: Session,
        query: DisasterSafetyQuery,
        now: Optional[datetime] = None,
    ) -> DisasterSafetyAssessmentResponse:
        """
        Executes disaster and safety assessment for the specified location.
        """
        # 1. Collect disaster/safety data
        collected_data = self.collector.collect(
            db=db,
            latitude=query.latitude,
            longitude=query.longitude,
            radius_km=query.radius_km,
            target_datetime=query.target_datetime,
        )

        # 2. Run deterministic reasoning engine
        assessment = self.reasoning.evaluate(collected_data=collected_data)

        return assessment
